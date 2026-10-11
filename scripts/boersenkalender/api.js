/*
 * SA.boersenkalender — Börsenkalender und Handelstag-Nummern für die Seiten.
 *
 * Quelle: ausschließlich Python (shared/boersenereignisse.py, shared/exchange_holidays.py, shared/symbols.py). Diese Datei ist der
 * API-Teil; scripts/build_boersenkalender_js.py setzt sie mit den Daten zu landing/js/boersenkalender.js
 * zusammen. Nicht von Hand in landing/js/ ändern.
 *
 * Bis zur gemeinsamen Umschaltung (Plan v6, Weg A) bindet KEINE Seite diese Datei ein; holidays.js bleibt
 * der Kalender der Seiten. Der Wächter scripts/verify_boersenkalender_js.py prüft das.
 *
 * Zeitzonenfrei: alle Rechnungen auf ganzen Zahlen (Jahr, Monat, Tag, Tageszähler). Kein Date-Objekt —
 * new Date("YYYY-MM-DD") ist UTC, new Date(j, m, t) lokal, und in Pacific/Apia fehlt der 30.12.2011
 * (Codex Runde 5/6).
 */
window.SA.__release('%%RELEASE%%');   // Releasekennung (landing/js/methode.js) — muss erste Anweisung bleiben
(function (global) {
  'use strict';
  var SA = global.SA = global.SA || {};
  var DATEN = /*__DATEN__*/null;
  if (!DATEN || DATEN.schema !== 2) throw new Error('boersenkalender: Daten fehlen oder Schema unbekannt');

  var ALIAS = { NASDAQ: 'NYSE' };
  var ISO = /^[0-9]{4}-[0-9]{2}-[0-9]{2}$/;

  // Eigene Fehlerklasse für GEWOLLTE Fehler (ungültige Eingabe, Datenende). Aufrufer und Wächter
  // unterscheiden damit einen Kalenderfehler von einem Absturz — über die Klasse, nicht über den Text
  // (ein Meldungspräfix ließ sich unterlaufen, Codex P1b R2).
  function KalenderFehler(text) {
    this.name = 'KalenderFehler';
    this.message = 'boersenkalender: ' + text;
    this.stack = (new Error(this.message)).stack;
  }
  KalenderFehler.prototype = Object.create(Error.prototype);
  KalenderFehler.prototype.constructor = KalenderFehler;
  function fehler(text) { throw new KalenderFehler(text); }

  function istSchaltjahr(j) { return (j % 4 === 0 && j % 100 !== 0) || j % 400 === 0; }
  function monatsTage(j, m) { return [31, istSchaltjahr(j) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]; }

  // Tage seit 1970-01-01 (proleptisch gregorianisch, Howard Hinnant) — nur ganze Zahlen.
  function tagNr(j, m, t) {
    var y = m <= 2 ? j - 1 : j;
    var era = Math.floor(y / 400);
    var yoe = y - era * 400;
    var doy = Math.floor((153 * (m + (m > 2 ? -3 : 9)) + 2) / 5) + t - 1;
    var doe = yoe * 365 + Math.floor(yoe / 4) - Math.floor(yoe / 100) + doy;
    return era * 146097 + doe - 719468;
  }
  // Wochentag 0 = Montag … 6 = Sonntag (wie Python date.weekday()); 1970-01-01 war ein Donnerstag.
  function wochentag(j, m, t) { return ((tagNr(j, m, t) % 7) + 7 + 3) % 7; }
  function zweistellig(n) { return (n < 10 ? '0' : '') + n; }
  function iso(j, m, t) { return j + '-' + zweistellig(m) + '-' + zweistellig(t); }

  function boerseNormalisieren(b) {
    if (typeof b !== 'string' || !b.trim()) fehler('Börse fehlt oder ist kein Text: ' + b);
    var e = b.trim().toUpperCase();
    e = ALIAS[e] || e;
    if (!Object.prototype.hasOwnProperty.call(DATEN.woche, e)) fehler('Unbekannte Börse: ' + b);
    return e;
  }

  function ganzzahl(x, name) {
    if (typeof x !== 'number' || !isFinite(x) || Math.floor(x) !== x) fehler(name + ' muss eine ganze Zahl sein: ' + x);
    return x;
  }

  function jahrPruefen(j) {
    ganzzahl(j, 'Jahr');
    if (j < DATEN.von || j > DATEN.bis) fehler('Jahr außerhalb des Rechenbereichs ' + DATEN.von + '–' + DATEN.bis + ': ' + j);
    return j;
  }

  function datumZerlegen(x) {
    if (typeof x !== 'string' || !ISO.test(x)) fehler('Datum nicht im Format YYYY-MM-DD: ' + x);
    var j = +x.slice(0, 4), m = +x.slice(5, 7), t = +x.slice(8, 10);
    if (m < 1 || m > 12 || t < 1 || t > monatsTage(j, m)) fehler('Kein gültiges Datum: ' + x);
    jahrPruefen(j);
    return [j, m, t];
  }

  // Schließtage je (Börse, Jahr) als Menge 'MMDD' — direkt aus den Daten.
  var schliessCache = {};
  function schliessMenge(b, j) {
    var k = b + '|' + j, s = schliessCache[k];
    if (s) return s;
    s = {};
    var roh = (DATEN.schliessungen[b] || {})[String(j)] || '';
    for (var i = 0; i < roh.length; i += 4) s[roh.slice(i, i + 4)] = true;
    schliessCache[k] = s;
    return s;
  }

  function offen(b, j, m, t) {
    if (DATEN.woche[b] === 'taeglich') return true;
    if (wochentag(j, m, t) >= 5) return false;
    return !schliessMenge(b, j)[zweistellig(m) + zweistellig(t)];
  }

  // Nummern je Kalendertag eines Jahres — wie Python _jahresnummern.
  var jahrCache = {};
  function jahresTabelle(b, j) {
    var k = b + '|' + j, tab = jahrCache[k];
    if (tab) return tab;
    var tage = [], jahrSumme = 0, monatSumme = {}, m, t;
    for (m = 1; m <= 12; m++) {
      monatSumme[m] = 0;
      for (t = 1; t <= monatsTage(j, m); t++) {
        var o = offen(b, j, m, t);
        tage.push([m, t, o]);
        if (o) { jahrSumme++; monatSumme[m]++; }
      }
    }
    tab = {};
    var tdoy = 0, tdom = 0, monat = 0;
    for (var i = 0; i < tage.length; i++) {
      m = tage[i][0]; t = tage[i][1];
      if (m !== monat) { monat = m; tdom = 0; }
      if (tage[i][2]) {
        tdoy++; tdom++;
        tab[iso(j, m, t)] = Object.freeze({ tdom: tdom, tdoy: tdoy, tdom_rev: -(monatSumme[m] - tdom + 1),
                                            tdoy_rev: -(jahrSumme - tdoy + 1), offen: true });
      } else {
        tab[iso(j, m, t)] = Object.freeze({ tdom: tdom, tdoy: tdoy, tdom_rev: null, tdoy_rev: null, offen: false });
      }
    }
    jahrCache[k] = tab;
    return tab;
  }

  // Ereigniskatalog (V1c-1, Vertrag B4): Objekte wie Python Ereignis.als_dict(), unveränderlich.
  function vollesDatum(j, mmdd) { return j + '-' + mmdd.slice(0, 2) + '-' + mmdd.slice(2, 4); }
  function isoAus8(x) { return x.slice(0, 4) + '-' + x.slice(4, 6) + '-' + x.slice(6, 8); }
  var ereignisCache = {};
  function ereignisListe(b, j) {
    var k = b + '|' + j, liste = ereignisCache[k];
    if (liste) return liste;
    var roh = (DATEN.ereignisse[b] || {})[String(j)] || [];
    liste = [];
    for (var i = 0; i < roh.length; i++) {
      var r = DATEN.regeln[b][roh[i][0]], ab = roh[i][2] || {};
      var nominal = vollesDatum(j, roh[i][1]);
      var rechtlich = ab.r ? isoAus8(ab.r) : nominal;
      var wirksam = ab.w ? isoAus8(ab.w) : rechtlich;
      var herkunft = ab.h || 'regel';
      var nIdx = Object.prototype.hasOwnProperty.call(ab, 'n') ? ab.n : r[2];
      var q = DATEN.quellen[Object.prototype.hasOwnProperty.call(ab, 'q') ? ab.q : r[3]];
      liste.push(Object.freeze({
        ereignis_id: herkunft === 'tabelle' ? b + ':tabelle:' + nominal : b + ':' + r[0] + ':' + nominal,
        boerse: b, regel_id: r[0], art: ab.a || r[1], nominal: nominal, rechtlich: rechtlich, wirksam: wirksam,
        ersatzgrund: ab.g || 'keiner', verlegt: ab.v === 1, nominal_herkunft: herkunft,
        name_de: nIdx < 0 ? null : DATEN.namen[nIdx][0], name_en: nIdx < 0 ? null : DATEN.namen[nIdx][1],
        quelle: q[0], quelle_titel: q[1], quelle_beleg: q[2], quelle_stand: q[3],
        kalenderversion: DATEN.kalenderversion
      }));
    }
    liste = Object.freeze(liste);
    ereignisCache[k] = liste;
    return liste;
  }


  // ── US-Produkttermine (V1c-2, wie Python shared/produkttermine.py) ─────────────────────────────────────────
  // Tag aus Tageszähler (Howard Hinnant civil_from_days) — ganze Zahlen, zeitzonenfrei.
  function ausTagNr(z) {
    z += 719468;
    var era = Math.floor(z / 146097), doe = z - era * 146097;
    var yoe = Math.floor((doe - Math.floor(doe / 1460) + Math.floor(doe / 36524) - Math.floor(doe / 146096)) / 365);
    var doy = doe - (365 * yoe + Math.floor(yoe / 4) - Math.floor(yoe / 100));
    var mp = Math.floor((5 * doy + 2) / 153), t = doy - Math.floor((153 * mp + 2) / 5) + 1;
    var m = mp + (mp < 10 ? 3 : -9), j = yoe + era * 400 + (m <= 2 ? 1 : 0);
    return [j, m, t];
  }
  function isoNr(n) { var d = ausTagNr(n); return iso(d[0], d[1], d[2]); }
  function offenNr(n) { var d = ausTagNr(n); return offen('NYSE', d[0], d[1], d[2]); }
  function vorherNr(n) { n -= 1; while (!offenNr(n)) n -= 1; return n; }
  function dritterFreitagNr(j, m) { return tagNr(j, m, 15) + ((4 - wochentag(j, m, 15)) % 7 + 7) % 7; }
  var PR = DATEN.produkte;
  function monatStr(j, m) { return j + '-' + zweistellig(m); }
  function vorM(a, b) { return a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]); }
  function monatZerlegen(x) {
    if (typeof x !== 'string' || !/^[0-9]{4}-[0-9]{2}$/.test(x)) fehler('Monat nicht im Format YYYY-MM: ' + x);
    var j = +x.slice(0, 4), m = +x.slice(5, 7);
    if (m < 1 || m > 12) fehler('Monat außerhalb 1–12: ' + x);
    return [j, m];
  }
  function pruefdatumPruefen(p) {
    if (p === undefined || p === null) fehler('pruefdatum fehlt (Pflichtangabe, YYYY-MM-DD)');
    datumZerlegen(p);
    return p;
  }
  function einstufen(monat, reihe, regelIso, p) {
    var beleg = PR.belege[reihe].monate[monat];
    if (beleg !== undefined) return [beleg, 'belegt', null];
    if (regelIso > p) return [regelIso, 'projektion', null];
    return [null, 'luecke', 'nicht_belegt'];
  }
  function quelleVon(listung, reihe) { return listung === 'belegt' ? reihe : (listung === 'projektion' ? 'regel' : null); }
  function opexRegel(j, m) {
    var r = dritterFreitagNr(j, m), v = offenNr(r) ? r : vorherNr(r);
    return { regeltermin: isoNr(r), verfallstermin: isoNr(v) };
  }
  function vixRegel(j, m) {
    var fj = m === 12 ? j + 1 : j, fm = m === 12 ? 1 : m + 1;
    var ref = dritterFreitagNr(fj, fm), nominal = ref - 30;
    var s = (offenNr(nominal) && offenNr(ref)) ? nominal : vorherNr(nominal);
    return { referenzfreitag: isoNr(ref), nominal: isoNr(nominal), settlement: isoNr(s) };
  }
  function vorherIso(x) { var d = datumZerlegen(x); return isoNr(vorherNr(tagNr(d[0], d[1], d[2]))); }
  function opexEreignis(j, m, p) {
    if (vorM([j, m], PR.opex_ab)) return null;
    var monat = monatStr(j, m), r = opexRegel(j, m), e = einstufen(monat, 'SPX_STANDARD', r.verfallstermin, p);
    if (e[1] === 'luecke') return null;
    return Object.freeze({
      ereignis_id: 'US_OPT:opex.monat:' + monat, produkt: 'US_OPT', art: 'opex', verfallsmonat: monat,
      regeltermin: r.regeltermin, verfallstermin: e[0], formaler_verfall: e[0],
      ersatzgrund: e[0] === r.regeltermin ? 'keiner' : 'feiertag', triple_witching: PR.triple_monate.indexOf(m) >= 0,
      listung: e[1], grund: e[2], regel_abweichung: e[0] !== r.verfallstermin,
      regelstand: PR.regelstand_opex, quelle: quelleVon(e[1], 'SPX_STANDARD'),
      kalenderannahme: PR.kalenderannahme, kalenderstatus: PR.kalenderstatus,
      kalenderversion: DATEN.kalenderversion
    });
  }
  function vixEreignis(j, m, p) {
    if (vorM([j, m], PR.vix_ab)) return null;
    var monat = monatStr(j, m), r = vixRegel(j, m);
    var vx = einstufen(monat, 'VX', r.settlement, p), op = einstufen(monat, 'VIX_OPT', r.settlement, p);
    if (vx[1] === 'luecke' && op[1] === 'luecke') return null;
    return Object.freeze({
      ereignis_id: 'US_VIX:vix.settlement:' + monat, produkt: 'US_VIX', art: 'vix', kontraktmonat: monat,
      referenzfreitag: r.referenzfreitag, nominal: r.nominal,
      ersatzgrund: r.settlement === r.nominal ? 'keiner' : 'feiertag',
      settlement: vx[0], handelsende_futures: vx[0], listung_futures: vx[1], grund_futures: vx[2],
      verfall_optionen: op[0], handelsende_optionen: op[0] === null ? null : vorherIso(op[0]),
      listung_optionen: op[1], grund_optionen: op[2],
      quelle_futures: quelleVon(vx[1], 'VX'), quelle_optionen: quelleVon(op[1], 'VIX_OPT'),
      kalenderannahme: PR.kalenderannahme, kalenderstatus: PR.kalenderstatus,
      regel_abweichung: (vx[0] !== null && vx[0] !== r.settlement) || (op[0] !== null && op[0] !== r.settlement),
      regelstand: PR.regelstand_vix, kalenderversion: DATEN.kalenderversion
    });
  }
  function monateAb(a, b, f) {
    var j = a[0], m = a[1];
    while (!vorM(b, [j, m])) { f(j, m); if (m === 12) { j++; m = 1; } else m++; }
  }

  var API = {
    version: DATEN.version,
    /** Hash über die aufgelösten Ereignisinhalte (jede Inhaltsänderung) — wie Python ereignisversion(). */
    ereignisversion: DATEN.ereignisversion,
    /** Hash über die Schließungsprojektion — ändert sich genau dann, wenn sie sich ändert. */
    kalenderversion: DATEN.kalenderversion,
    schema: DATEN.schema,
    pruefdatum: DATEN.pruefdatum,
    von: DATEN.von,
    bis: DATEN.bis,
    /** Klasse der gewollten Fehler: `e instanceof SA.boersenkalender.Fehler`. */
    Fehler: KalenderFehler,

    /** Kanonische Börse eines Tickers — dieselbe Regel wie shared.symbols.get_exchange_for_holidays. */
    boerse: function (ticker) {
      if (typeof ticker !== 'string' || !ticker.trim()) fehler('Ticker fehlt: ' + ticker);
      var t = ticker.trim().toUpperCase();
      if (/-USDT?$/.test(t)) return 'CRYPTO';
      if (/=X$/.test(t)) return 'FOREX';
      if (Object.prototype.hasOwnProperty.call(DATEN.ticker, t)) return DATEN.ticker[t];
      for (var i = 0; i < DATEN.suffix.length; i++) {
        var suf = DATEN.suffix[i][0];
        if (t.slice(-suf.length) === suf) return DATEN.suffix[i][1];   // wie Python str.endswith
      }
      if (t.charAt(0) === '^' || t.indexOf('.') >= 0 || t.indexOf('=') >= 0) fehler('Kein Börsenkalender für unbekannten Ticker ' + ticker);
      return 'NYSE';
    },

    istHandelstag: function (datum, boerse) {
      var b = boerseNormalisieren(boerse), d = datumZerlegen(datum);
      return offen(b, d[0], d[1], d[2]);
    },

    /** Wie Python handelstag_nummern: Börse zuerst, Reihenfolge und Duplikate bleiben, unveränderliche Objekte. */
    nummern: function (daten, boerse) {
      var b = boerseNormalisieren(boerse);
      if (!Array.isArray(daten)) fehler('Daten müssen eine Liste sein');
      var zerlegt = daten.map(datumZerlegen), out = [];
      for (var i = 0; i < zerlegt.length; i++) out.push(jahresTabelle(b, zerlegt[i][0])[daten[i]]);
      return out;
    },

    /** n-ter Handelstag (n ≥ 1) eines Monats; null, wenn es ihn nicht gibt. */
    nterHandelstag: function (j, m, n, boerse) {
      var b = boerseNormalisieren(boerse);
      jahrPruefen(j); ganzzahl(m, 'Monat'); ganzzahl(n, 'Position');
      if (m < 1 || m > 12) fehler('Monat außerhalb 1–12: ' + m);
      if (n < 1) fehler('Position muss ≥ 1 sein: ' + n);
      var tab = jahresTabelle(b, j);
      for (var t = 1; t <= monatsTage(j, m); t++) {
        var x = tab[iso(j, m, t)];
        if (x.offen && x.tdom === n) return iso(j, m, t);
      }
      return null;
    },

    /** n-ter Handelstag von hinten (1 = letzter) eines Monats; null, wenn es ihn nicht gibt. */
    letzterHandelstag: function (j, m, nVonHinten, boerse) {
      var b = boerseNormalisieren(boerse);
      jahrPruefen(j); ganzzahl(m, 'Monat'); ganzzahl(nVonHinten, 'Position');
      if (m < 1 || m > 12) fehler('Monat außerhalb 1–12: ' + m);
      if (nVonHinten < 1) fehler('Position muss ≥ 1 sein: ' + nVonHinten);
      var tab = jahresTabelle(b, j);
      for (var t = monatsTage(j, m); t >= 1; t--) {
        var x = tab[iso(j, m, t)];
        if (x.offen && x.tdom_rev === -nVonHinten) return iso(j, m, t);
      }
      return null;
    },

    /** n-ter Handelstag (n ≥ 1) eines Jahres; null, wenn es ihn nicht gibt. */
    nterHandelstagImJahr: function (j, n, boerse) {
      var b = boerseNormalisieren(boerse);
      jahrPruefen(j); ganzzahl(n, 'Position');
      if (n < 1) fehler('Position muss ≥ 1 sein: ' + n);
      var tab = jahresTabelle(b, j);
      for (var m = 1; m <= 12; m++) {
        for (var t = 1; t <= monatsTage(j, m); t++) {
          var x = tab[iso(j, m, t)];
          if (x.offen && x.tdoy === n) return iso(j, m, t);
        }
      }
      return null;
    },

    /** Erster Handelstag AB EINSCHLIESSLICH datum; über Jahresgrenzen; Datenende → Fehler. */
    naechsterHandelstag: function (datum, boerse) {
      var b = boerseNormalisieren(boerse), d = datumZerlegen(datum);
      var j = d[0], m = d[1], t = d[2];
      for (;;) {
        if (offen(b, j, m, t)) return iso(j, m, t);
        t++;
        if (t > monatsTage(j, m)) { t = 1; m++; }
        if (m > 12) { m = 1; j++; }
        if (j > DATEN.bis) fehler('Kein Handelstag bis zum Datenende ' + DATEN.bis + ' (ab ' + datum + ')');
      }
    },

    /** Bisherige Feiertagsmenge eines Jahres (wie Python get_holidays, sortiert, inkl. Wochenenddaten). */
    feiertagsmenge: function (j, boerse) {
      var b = boerseNormalisieren(boerse);
      jahrPruefen(j);
      var roh = (DATEN.schliessungen[b] || {})[String(j)] || '', out = [];
      for (var i = 0; i < roh.length; i += 4) out.push(j + '-' + roh.slice(i, i + 2) + '-' + roh.slice(i + 2, i + 4));
      return out;
    },

    /** Wirksame Vollschließungen auf sonst offenen Tagen (Mo–Fr), eindeutig, sortiert — wie Python schliessungen(). */
    schliessungen: function (j, boerse) {
      var b = boerseNormalisieren(boerse);
      jahrPruefen(j);
      var liste = ereignisListe(b, j), menge = {}, out = [];
      for (var i = 0; i < liste.length; i++) {
        var e = liste[i];
        if (e.art === 'halbtag') continue;
        var w = e.wirksam;
        if (wochentag(+w.slice(0, 4), +w.slice(5, 7), +w.slice(8, 10)) < 5) menge[w] = true;
      }
      for (var d in menge) out.push(d);
      return out.sort();
    },

    /** Ereignisse eines Jahres (Jahr des Regeltermins) — neue Liste unveränderlicher Objekte, Reihenfolge wie Python. */
    ereignisse: function (j, boerse) {
      var b = boerseNormalisieren(boerse);
      jahrPruefen(j);
      return ereignisListe(b, j).slice();
    },

    /** 'tabelle' (Identität nur aus Datumstabelle — Abnahmelücke) | 'regel' — wie Python identitaet(). */
    /** Version der Produkttermin-Fakten (Regeln + Belege) — wie Python produktversion(). */
    produktversion: PR.produktversion,

    /** OPEX/VIX-Ereignisse der Monate von..bis ('YYYY-MM'); pruefdatum ('YYYY-MM-DD') ist Pflicht. */
    produkttermine: function (von, bis, art, pruefdatum) {
      if (art !== 'opex' && art !== 'vix') fehler('Unbekannte Art: ' + art);
      var p = pruefdatumPruefen(pruefdatum), a = monatZerlegen(von), b = monatZerlegen(bis);
      var grenze = art === 'opex' ? PR.bis : PR.vix_bis;
      if (vorM(grenze, b)) fehler('Monat nach dem Rechenbereich: ' + bis);
      var out = [], f = art === 'opex' ? opexEreignis : vixEreignis;
      monateAb(a, b, function (j, m) { var e = f(j, m, p); if (e) out.push(e); });
      return out;
    },

    /** Abdeckungslücken je Belegreihe zum Prüfdatum — wie Python abdeckung(). */
    abdeckung: function (pruefdatum) {
      var p = pruefdatumPruefen(pruefdatum), l = { SPX_STANDARD: [], VX: [], VIX_OPT: [] }, ds = {};
      monateAb(PR.opex_ab, PR.bis, function (j, m) {
        if (einstufen(monatStr(j, m), 'SPX_STANDARD', opexRegel(j, m).verfallstermin, p)[1] === 'luecke') l.SPX_STANDARD.push(monatStr(j, m));
      });
      monateAb(PR.vix_ab, PR.vix_bis, function (j, m) {
        var s = vixRegel(j, m).settlement;
        if (einstufen(monatStr(j, m), 'VX', s, p)[1] === 'luecke') l.VX.push(monatStr(j, m));
        if (einstufen(monatStr(j, m), 'VIX_OPT', s, p)[1] === 'luecke') l.VIX_OPT.push(monatStr(j, m));
      });
      for (var k in PR.belege) ds[k] = PR.belege[k].datenstand;
      return { pruefdatum: p, nicht_modelliert: { opex_vor: monatStr(PR.opex_ab[0], PR.opex_ab[1]),
               vix_vor: monatStr(PR.vix_ab[0], PR.vix_ab[1]) }, luecken: l, datenstand: ds };
    },

    identitaet: function (boerse, j) {
      var b = boerseNormalisieren(boerse);
      jahrPruefen(j);
      return DATEN.identitaet[b].indexOf(j) >= 0 ? 'tabelle' : 'regel';
    },

    /** 'belegt' | 'annahme' | 'ungeprueft' | 'konvention' — wie Python kalender_status. */
    status: function (boerse, j) {
      var b = boerseNormalisieren(boerse);
      ganzzahl(j, 'Jahr');
      var s = DATEN.status[b];
      for (var i = 0; i < s[1].length; i++) if (s[1][i][0] <= j && j <= s[1][i][1]) return s[1][i][2];
      return s[0];
    }
  };

  SA.boersenkalender = Object.freeze(API);
})(typeof window !== 'undefined' ? window : globalThis);
