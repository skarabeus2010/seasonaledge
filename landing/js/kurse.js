/**
 * SA.kurse — der eine Kurslader der Seite (Plan: docs/TICKER_LADEN.md, S1).
 *
 * Eine Kursreihe wird je Ticker EINMAL geladen und von allen Verbrauchern der Seite geteilt (Chart, Saison-Score,
 * Radar, Overnight …). Ein Ergebnis ist vollständig oder eine Ablehnung — eine halbe Reihe wird nie als ganze
 * ausgegeben und nie gecacht.
 *
 *   SA.kurse.laden(ticker, {felder: ['date','close',…], ab: 'YYYY-MM-DD' | null})
 *     → Promise<{zeilen, generation, abdeckungAb, geladenUm}>
 *   SA.kurse.zeilen(ticker, opts) → Promise<zeilen>          (Kurzform)
 *
 * zeilen: neue Objekte, aufsteigend nach Datum, genau die Zeilen mit date >= ab (Grenztag eingeschlossen), genau die
 * angeforderten Felder, Werte unverändert aus der Datenbank (null bleibt null, 0 bleibt 0).
 * generation: global monoton steigend, nie wiederverwendet — wer abgeleitete Ergebnisse cacht, nimmt sie in den
 * Schlüssel (ticker|generation|Parameter), dann rechnet er nach jeder neuen Ladung neu.
 *
 * Laden: Keyset (order=date.asc&limit=1000&date=gt.<letztes>), ohne count=exact, Ende = Block < 1000. Jeder Block
 * wird geprüft (HTTP, Array, gültige ISO-Daten, streng aufsteigend, erstes Datum > Cursor, angeforderte Felder
 * vorhanden). 429/5xx/Netz/Zeitüberschreitung → bis zu 4 Wiederholungen (Retry-After hat Vorrang), danach Ablehnung.
 *
 * Koordinator je Ticker: ein Bestand (Felder, Abdeckung ab Grenze, Ladezeit). Deckt der frische Bestand oder eine
 * laufende/wartende Ladung die Anfrage, wird daraus bedient. Sonst wird EINE Ladung des vereinigten Bedarfs
 * (Felder ∪, früheste Grenze, null = ganze Historie gewinnt; der vorhandene Bestand ist Teil der Vereinigung, damit
 * er nie schrumpft) eingereiht — höchstens eine wartet hinter der laufenden. Erst nach Erfolg ersetzt sie den
 * Bestand. Scheitert sie, lehnen ihre Anfragen ab; ein älterer Bestand bleibt, ohne seine Frische zu verlängern.
 */
(function () {
  var SA = window.SA = window.SA || {};

  var ERLAUBT = ['date', 'open', 'high', 'low', 'close', 'log_return', 'tdom', 'tdoy'];
  var K = {
    BLOCK: 1000,
    MAX_BLOECKE: 61,          // 60 000 Zeilen — längste Reihe heute ~35 000; Schutz gegen Endlosschleifen
    TTL_MS: 15 * 60 * 1000,
    MAX_TICKER: 12,
    POOL: 4,
    TIMEOUT_MS: 20000,
    MAX_WIEDERHOLUNGEN: 4,
    MAX_WARTEN_MS: 60000      // Obergrenze für eine Retry-After-Wartezeit
  };

  var generationen = 0;
  var koordinatoren = {};       // ticker → Koordinator
  var zugriff = 0;              // LRU-Zähler
  var aktiv = 0, schlange = [];
  var uhr = function () { return Date.now(); };

  function KursFehler(meldung) {
    var e = new Error(meldung);
    e.name = 'KursFehler';
    return e;
  }

  // ── Pool: höchstens K.POOL gleichzeitig OFFENE Netzanfragen über alle Ticker ──────────────────────────────
  // Ein Platz wird erst frei, wenn der Transport wirklich endet — nicht schon, wenn die Frist abläuft. Sonst
  // stapeln sich bei einem Server, der nicht antwortet (oder einem Browser, der den Abbruch nicht kennt), offene
  // Anfragen über die Grenze (Codex S1 R1, Befund 2).
  // Die Wartezeit in der Schlange zählt zur Frist der Anfrage (Codex S1 R2, Befund 1): `entfernen` nimmt einen noch
  // wartenden Eintrag heraus, damit eine abgelaufene Anfrage später keinen Platz mehr belegt.
  function platz() {
    var eintrag, ok;
    var p = new Promise(function (res) { ok = res; });
    eintrag = function () {
      aktiv++;
      var frei = false;
      ok(function () { if (frei) return; frei = true; aktiv--; weiter(); });
    };
    schlange.push(eintrag);
    weiter();
    return {
      promise: p,
      entfernen: function () { var i = schlange.indexOf(eintrag); if (i >= 0) schlange.splice(i, 1); }
    };
  }
  function weiter() {
    while (aktiv < K.POOL && schlange.length) schlange.shift()();
  }

  /** Retry-After: Sekunden ODER HTTP-Datum (RFC 9110 §10.2.3). null = keine verwertbare Angabe. */
  function retryAfterMs(wert) {
    if (wert == null) return null;
    var s = String(wert).trim();
    if (/^\d+$/.test(s)) return Math.min(+s * 1000, K.MAX_WARTEN_MS);
    var t = Date.parse(s);
    if (isNaN(t)) return null;
    return Math.min(Math.max(0, t - uhr()), K.MAX_WARTEN_MS);
  }

  // ── Eingaben ────────────────────────────────────────────────────────────────────────────────────────────
  var ISO = /^(\d{4})-(\d{2})-(\d{2})$/;
  function istIso(s) {
    if (typeof s !== 'string') return false;
    var m = ISO.exec(s);
    if (!m) return false;
    var j = +m[1], mo = +m[2], t = +m[3];
    if (mo < 1 || mo > 12 || t < 1) return false;
    var tage = [31, (j % 4 === 0 && (j % 100 !== 0 || j % 400 === 0)) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    return t <= tage[mo - 1];
  }
  function felderNorm(felder) {
    if (!Array.isArray(felder) || !felder.length) throw KursFehler('felder fehlt');
    var menge = { date: true };
    felder.forEach(function (f) {
      if (ERLAUBT.indexOf(f) < 0) throw KursFehler('unbekanntes Feld: ' + f);
      menge[f] = true;
    });
    return ERLAUBT.filter(function (f) { return menge[f]; });
  }
  function abNorm(ab) {
    if (ab === null || ab === undefined) return null;
    if (!istIso(ab)) throw KursFehler('ab ist kein Datum: ' + ab);
    return ab;
  }

  // ── Bedarf: {felder: [...], ab: 'YYYY-MM-DD'|null} ──────────────────────────────────────────────────────
  function deckt(bedarf, felder, ab) {
    if (!bedarf) return false;
    for (var i = 0; i < felder.length; i++) if (bedarf.felder.indexOf(felder[i]) < 0) return false;
    return bedarf.ab === null || (ab !== null && ab >= bedarf.ab);
  }
  function vereinige(a, b) {
    if (!a) return { felder: b.felder.slice(), ab: b.ab };
    if (!b) return { felder: a.felder.slice(), ab: a.ab };
    var menge = {};
    a.felder.concat(b.felder).forEach(function (f) { menge[f] = true; });
    return {
      felder: ERLAUBT.filter(function (f) { return menge[f]; }),
      ab: (a.ab === null || b.ab === null) ? null : (a.ab < b.ab ? a.ab : b.ab)
    };
  }

  // ── Netz ───────────────────────────────────────────────────────────────────────────────────────────────
  function warte(ms) { return new Promise(function (ok) { setTimeout(ok, ms); }); }

  function holeBlock(ticker, bedarf, nach, versuch) {
    var q = 'ticker=eq.' + encodeURIComponent(ticker) + '&select=' + bedarf.felder.join(',') +
            '&order=date.asc&limit=' + K.BLOCK + (bedarf.ab ? '&date=gte.' + bedarf.ab : '') + (nach ? '&date=gt.' + nach : '');
    var nochmal = function (ms) {
      return warte(ms != null ? ms : 350 * (versuch + 1) + Math.floor(Math.random() * 300))
        .then(function () { return holeBlock(ticker, bedarf, nach, versuch + 1); });
    };
    var abbruch = (typeof AbortController === 'function') ? new AbortController() : null;
    var zeit = null;
    var warten = platz();
    var frist = new Promise(function (ok, nein) {
      zeit = setTimeout(function () {
        warten.entfernen();                     // noch in der Schlange → raus, belegt nie einen Platz
        if (abbruch) abbruch.abort();
        nein(KursFehler('Zeitüberschreitung (' + ticker + ')'));
      }, K.TIMEOUT_MS);
    });
    var transport = warten.promise.then(function (frei) {
      var antwort;
      try {
        antwort = fetch(SA.supabase.url + '/rest/v1/prices?' + q, {
          headers: { 'apikey': SA.supabase.key, 'Authorization': 'Bearer ' + SA.supabase.key },
          signal: abbruch ? abbruch.signal : undefined
        }).then(function (r) {
          if (!r.ok) return { status: r.status, retryAfter: r.headers.get('retry-after') };
          return r.json().then(function (z) { return { status: r.status, zeilen: z }; });
        });
      } catch (e) {
        antwort = Promise.reject(e);
      }
      antwort.then(frei, frei);                 // Platz frei erst mit dem Ende des Transports (auch nach der Frist)
      return antwort;
    });
    return Promise.race([transport, frist]).then(function (w) { clearTimeout(zeit); return w; },
                                                  function (e) { clearTimeout(zeit); throw e; }).then(function (w) {
      if (w.zeilen === undefined) {
        if ((w.status === 429 || w.status >= 500) && versuch < K.MAX_WIEDERHOLUNGEN) {
          return nochmal(retryAfterMs(w.retryAfter));
        }
        throw KursFehler('prices ' + w.status + ' (' + ticker + ')');
      }
      return w.zeilen;
    }, function (e) {
      if (versuch < K.MAX_WIEDERHOLUNGEN) return nochmal(null);
      throw (e && e.name === 'KursFehler') ? e : KursFehler('Netzfehler (' + ticker + '): ' + (e && e.message));
    });
  }

  function pruefeBlock(z, nach, bedarf, ticker) {
    if (!Array.isArray(z)) throw KursFehler('prices non-array (' + ticker + ')');
    var vorher = nach;
    for (var i = 0; i < z.length; i++) {
      var zeile = z[i];
      if (!zeile || typeof zeile !== 'object' || !istIso(zeile.date)) throw KursFehler('ungültiges Datum (' + ticker + ')');
      if (vorher !== null && !(zeile.date > vorher)) throw KursFehler('Daten nicht streng aufsteigend (' + ticker + ')');
      for (var f = 0; f < bedarf.felder.length; f++) {
        if (!Object.prototype.hasOwnProperty.call(zeile, bedarf.felder[f])) {
          throw KursFehler('Feld ' + bedarf.felder[f] + ' fehlt (' + ticker + ')');
        }
      }
      if (bedarf.ab !== null && zeile.date < bedarf.ab) throw KursFehler('Zeile vor der Grenze (' + ticker + ')');
      vorher = zeile.date;
    }
  }

  function ladeAlles(ticker, bedarf) {
    var bloecke = [], nach = null, n = 0;
    function naechster() {
      if (++n > K.MAX_BLOECKE) return Promise.reject(KursFehler('zu viele Blöcke (' + ticker + ')'));
      return holeBlock(ticker, bedarf, nach, 0).then(function (z) {
        pruefeBlock(z, nach, bedarf, ticker);
        bloecke.push(z);
        if (z.length < K.BLOCK) return [].concat.apply([], bloecke);
        nach = z[z.length - 1].date;
        return naechster();
      });
    }
    return naechster();
  }

  // ── Koordinator ────────────────────────────────────────────────────────────────────────────────────────
  function koordinator(ticker) {
    var k = koordinatoren[ticker];
    if (!k) {
      k = koordinatoren[ticker] = { bestand: null, laufend: null, wartend: null, zugriff: 0 };
      verdraengen(ticker);
    }
    k.zugriff = ++zugriff;
    return k;
  }
  function verdraengen(neu) {
    var namen = Object.keys(koordinatoren);
    while (namen.length > K.MAX_TICKER) {
      var opfer = null;
      namen.forEach(function (t) {
        var k = koordinatoren[t];
        if (t === neu || k.laufend || k.wartend) return;      // nur ruhende Koordinatoren
        if (!opfer || k.zugriff < koordinatoren[opfer].zugriff) opfer = t;
      });
      if (!opfer) return;                                      // alle beschäftigt → vorübergehend mehr
      delete koordinatoren[opfer];
      namen = Object.keys(koordinatoren);
    }
  }

  function frisch(b) { return b && (uhr() - b.geladenUm) < K.TTL_MS; }

  function sicht(b, felder, ab) {
    var aus = [];
    for (var i = 0; i < b.zeilen.length; i++) {
      var z = b.zeilen[i];
      if (ab !== null && z.date < ab) continue;
      var o = {};
      for (var f = 0; f < felder.length; f++) o[felder[f]] = z[felder[f]];
      aus.push(o);
    }
    return { zeilen: aus, generation: b.generation, abdeckungAb: b.bedarf.ab, geladenUm: b.geladenUm };
  }

  function starte(ticker, k, bedarf) {
    var lauf = { bedarf: bedarf };
    lauf.promise = ladeAlles(ticker, bedarf).then(function (zeilen) {
      k.bestand = { zeilen: zeilen, bedarf: bedarf, geladenUm: uhr(), generation: ++generationen };
      return k.bestand;
    });
    k.laufend = lauf;
    var danach = function () {
      if (k.laufend !== lauf) return;
      k.laufend = null;
      var w = k.wartend;
      if (w) {
        k.wartend = null;
        // der Bestand (falls die laufende Ladung ihn gerade erneuert hat) gehört zur Vereinigung
        var b = starte(ticker, k, vereinige(w.bedarf, k.bestand ? k.bestand.bedarf : null));
        b.promise.then(w.ok, w.nein);
      }
      verdraengen(null);
    };
    lauf.promise.then(danach, danach);
    return lauf;
  }

  function laden(ticker, opts) {
    return Promise.resolve().then(function () {
      if (typeof ticker !== 'string' || !ticker) throw KursFehler('ticker fehlt');
      if (!(SA.supabase && SA.supabase.url)) throw KursFehler('Kursquelle nicht verfügbar');
      var felder = felderNorm(opts && opts.felder);
      var ab = abNorm(opts && opts.ab);
      var anfrage = { felder: felder, ab: ab };
      var k = koordinator(ticker);
      // Letzte Sperre: eine Sicht nur aus einem Bestand, der die Anfrage deckt — sonst gäbe eine falsch vereinigte
      // Ladung still eine zu kurze Reihe als vollständig aus.
      var aus = function (b) {
        if (!deckt(b.bedarf, felder, ab)) throw KursFehler('Bestand deckt die Anfrage nicht (' + ticker + ')');
        return sicht(b, felder, ab);
      };

      if (frisch(k.bestand) && deckt(k.bestand.bedarf, felder, ab)) return aus(k.bestand);
      if (k.laufend && deckt(k.laufend.bedarf, felder, ab)) return k.laufend.promise.then(aus);
      if (k.wartend) {
        if (!deckt(k.wartend.bedarf, felder, ab)) k.wartend.bedarf = vereinige(k.wartend.bedarf, anfrage);
        return k.wartend.promise.then(aus);
      }
      if (k.laufend) {
        var w = { bedarf: vereinige(anfrage, k.laufend.bedarf) };
        w.promise = new Promise(function (ok, nein) { w.ok = ok; w.nein = nein; });
        k.wartend = w;
        return w.promise.then(aus);
      }
      return starte(ticker, k, vereinige(anfrage, k.bestand ? k.bestand.bedarf : null)).promise.then(aus);
    });
  }

  SA.kurse = {
    laden: laden,
    zeilen: function (ticker, opts) { return laden(ticker, opts).then(function (e) { return e.zeilen; }); },
    KursFehler: 'KursFehler',
    /** nur für Proben: Grenzen, Uhr und Zustand */
    _intern: {
      K: K,
      setzeUhr: function (fn) { uhr = fn; },
      zuruecksetzen: function () { koordinatoren = {}; schlange = []; aktiv = 0; zugriff = 0; },
      koordinatoren: function () { return koordinatoren; },
      aktiv: function () { return aktiv; }
    }
  };
})();
