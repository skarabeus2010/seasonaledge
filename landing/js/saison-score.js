/**
 * SeasonAlpha — Saison-Score (ersetzt den „KI-Score"; Plan v1–v3 mit Codex-Freigabe 2026-10-09).
 *
 * EINE Rechnung für Dashboard, Watchlist, KI-Seite — Zwilling: shared/saison_score.py (Scanner, Mails).
 * Braucht: seasonal-compute.js (tagNummer, _interpolateTo365) und decade-compute.js (marktklasse, _bereinigen,
 * _zielTag, _epochTag, ANOMALIE.TOLERANZ).
 *
 * Vertrag (Kurzfassung, Details im Plan):
 *  * Eingabe: VOLLSTÄNDIGE Kursreihe + Ticker (Pflicht); kein Aufrufer filtert vorher. as_of = letzte Kurszeile,
 *    oder opts.as_of → die Reihe wird ZUERST darauf abgeschnitten (präfixinvariant).
 *  * Fenster: as_of → +30 Kalendertage. Fensterrendite eines Vorjahres y aus Rohkursen: Start = letzte Kurszeile ≤
 *    Zieltag (Monat/Tag von as_of in y, 29.02. → 28.02.), Ende = letzte Kurszeile ≤ Zieltag + 30 KT; beide höchstens
 *    T Kalendertage vor ihrem Ziel und kein Abstand > T dazwischen (Heuristik, T wie das Anomalie-Radar).
 *  * Lookback = die 20 jüngsten abgeschlossenen Jahre mit gültigem Fenster und vollständigem Jahrespfad (≥ 20 Kurszeilen,
 *    erste Kurszeile spätestens am 10.01.); mindestens 10, sonst nicht berechenbar.
 *  * Bausteine (je 0…1, alle auf DEMSELBEN Fenster):
 *      B1 Anteil der Lookback-Jahre mit positiver Fensterrendite
 *      B2 clip((Ø Fensterrendite + 3) / 6)
 *      B3 Anteil der 5 Musterjahre mit positiver Fensterrendite
 *      B4 clip((ähnlichkeitsgewichtete Ø Fensterrendite der Musterjahre + 3) / 6), Gewicht w = (r + 1) / 2
 *    Score = 2,5 · (B1 + B2 + B3 + B4), ausgegeben halb aufwärts auf eine Stelle.
 *  * Musterjahre („Pfadähnlichkeit", fest v1): Pearson r des Jahrespfads (100 · Kurs / erster Kurs des Jahres, auf 365
 *    Tagesnummern interpoliert) über die Tage 1…d, d = min(Tagesnummer(as_of), 365); r undefiniert → kein Kandidat;
 *    Sortierung r absteigend, Gleichstand → jüngeres Jahr zuerst; ungerundet.
 *  * Musterkonformität (nur Anzeige, NICHT im Score): r zwischen laufendem Pfad und dem Mittelpfad der Lookback-Jahre.
 *  * Nicht berechenbar statt Ersatzwert: vor dem 20. Handelstag des Jahres, < 10 Lookback-Jahre, < 5 Musterjahre,
 *    Gewichtssumme 0. Keine Richtungsetiketten (Bullish/Bearish) — Nutzerentscheidung bis zur Validierung.
 */
var SA = window.SA || {};

SA.saisonScore = {
  METHODE: 'saison_v1',
  P: { HORIZONT: 30, LOOKBACK: 20, MIN_JAHRE: 10, TOP_N: 5, MIN_HANDELSTAGE: 20, SPAETESTER_JAHRESSTART: 10 },

  /** Pearson r, zweistufig (Mittelwerte zuerst) — wortgleich in shared/saison_score.py. null bei Streuung 0. */
  pearson: function(a, b) {
    var n = Math.min(a.length, b.length);
    if (n < 2) return null;
    // Konstanz VOR der Mittelwertrechnung erkennen: die Summation lässt bei exakt konstanten Werten eine winzige
    // Restvarianz stehen, und ein konstanter Pfad galt dann als perfekt korreliert (Codex Kern R1)
    var amin = a[0], amax = a[0], bmin = b[0], bmax = b[0], i;
    for (i = 1; i < n; i++) { if (a[i] < amin) amin = a[i]; if (a[i] > amax) amax = a[i]; if (b[i] < bmin) bmin = b[i]; if (b[i] > bmax) bmax = b[i]; }
    if (amin === amax || bmin === bmax) return null;
    var ma = 0, mb = 0;
    for (i = 0; i < n; i++) { ma += a[i]; mb += b[i]; }
    ma /= n; mb /= n;
    var sab = 0, saa = 0, sbb = 0;
    for (i = 0; i < n; i++) { var da = a[i] - ma, db = b[i] - mb; sab += da * db; saa += da * da; sbb += db * db; }
    if (!(saa > 0) || !(sbb > 0)) return null;
    return sab / Math.sqrt(saa * sbb);
  },

  _clip01: function(x) { return x < 0 ? 0 : (x > 1 ? 1 : x); },
  _runden1: function(x) { return Math.floor(x * 10 + 0.5) / 10; },

  berechne: function(rows, ticker, opts) {
    var DC = SA.decadeCompute, SE = SA.seasonal, P = this.P, self = this;
    var klasse = DC.marktklasse(ticker), T = DC.ANOMALIE.TOLERANZ[klasse];
    var asOfOpt = opts && opts.as_of ? String(opts.as_of).substring(0, 10) : null;
    var r = DC._bereinigen(rows, asOfOpt), n = r.length;
    var aus = function(code, grund) {
      return { status: 'nicht_berechenbar', grund_code: code, grund: grund, methode: self.METHODE,
               as_of: n ? r[n - 1].date : null, marktklasse: klasse, score: null };
    };
    if (!n) return aus('keine_kurse', 'keine Kurse');
    var asOf = r[n - 1].date, Y = +asOf.substring(0, 4), mA = +asOf.substring(5, 7), dA = +asOf.substring(8, 10);
    var tage = r.map(function(z) { return DC._epochTag(z.date); });

    // Jahrespfade (100 · Kurs / erster Kurs des Jahres) auf 365 Tagesnummern
    var proJahr = {};
    for (var i = 0; i < n; i++) {
      var y = +r[i].date.substring(0, 4);
      (proJahr[y] = proJahr[y] || []).push(i);
    }
    var pfad = function(y) {
      var idx = proJahr[y];
      if (!idx || idx.length < P.MIN_HANDELSTAGE) return null;
      if (+r[idx[0]].date.substring(8, 10) > P.SPAETESTER_JAHRESSTART || +r[idx[0]].date.substring(5, 7) !== 1) return null;
      var c0 = r[idx[0]].close;
      return SE._interpolateTo365(idx.map(function(k) { return SE.tagNummer(r[k].date); }),
                                  idx.map(function(k) { return 100 * r[k].close / c0; }));
    };
    if (!proJahr[Y] || proJahr[Y].length < P.MIN_HANDELSTAGE) return aus('zu_frueh_im_jahr', 'vor dem 20. Handelstag des Jahres');
    var pfadY = pfad(Y);
    if (!pfadY) return aus('unvollstaendiges_jahr', 'laufendes Jahr beginnt nach dem 10. Januar');
    var d = Math.min(SE.tagNummer(asOf), 365);

    // letzte Kurszeile ≤ Kalendertag (binäre Suche auf tage)
    var bisIdx = function(ziel) {
      var lo = 0, hi = n - 1, best = -1;
      while (lo <= hi) { var mid = (lo + hi) >> 1; if (tage[mid] <= ziel) { best = mid; lo = mid + 1; } else hi = mid - 1; }
      return best;
    };
    var fenster = function(y) {
      var z1 = DC._zielTag(y, mA, dA), z2 = z1 + P.HORIZONT;
      var s = bisIdx(z1), e = bisIdx(z2);
      if (s < 0 || e <= s || z1 - tage[s] > T || z2 - tage[e] > T) return null;
      for (var k = s + 1; k <= e; k++) if (tage[k] - tage[k - 1] > T) return null;
      return (r[e].close / r[s].close - 1) * 100;
    };

    // Lookback: die 20 jüngsten abgeschlossenen Jahre mit Fenster und Pfad
    var L = [], ersterJahr = +r[0].date.substring(0, 4);
    for (var yy = Y - 1; yy >= ersterJahr && L.length < P.LOOKBACK; yy--) {
      var py = pfad(yy);
      if (!py) continue;
      var R = fenster(yy);
      if (R === null) continue;
      L.push({ jahr: yy, rendite: R, pfad: py });
    }
    if (L.length < P.MIN_JAHRE) return aus('zu_wenige_jahre', 'weniger als ' + P.MIN_JAHRE + ' Vergleichsjahre');

    var cur = pfadY.slice(0, d);
    var kand = [];
    L.forEach(function(j) {
      var rr = self.pearson(cur, j.pfad.slice(0, d));
      if (rr !== null) kand.push({ jahr: j.jahr, r: rr, rendite: j.rendite });
    });
    kand.sort(function(a, b) { return b.r - a.r || b.jahr - a.jahr; });
    var top = kand.slice(0, P.TOP_N);
    if (top.length < P.TOP_N) return aus('zu_wenige_musterjahre', 'weniger als ' + P.TOP_N + ' Musterjahre');
    var W = 0, WR = 0;
    top.forEach(function(t) { var w = (t.r + 1) / 2; W += w; WR += w * t.rendite; });
    if (!(W > 0)) return aus('gewichte_null', 'Gewichtssumme der Musterjahre 0');

    var k1 = L.filter(function(j) { return j.rendite > 0; }).length;
    var mittel = L.reduce(function(s, j) { return s + j.rendite; }, 0) / L.length;
    var k3 = top.filter(function(t) { return t.rendite > 0; }).length;
    var mittelW = WR / W;
    var b1 = k1 / L.length, b2 = this._clip01((mittel + 3) / 6), b3 = k3 / top.length, b4 = this._clip01((mittelW + 3) / 6);
    var roh = 2.5 * (b1 + b2 + b3 + b4);

    // Musterkonformität: laufender Pfad gegen den Mittelpfad der Lookback-Jahre (Anzeige)
    var mittelpfad = [];
    for (var t = 0; t < d; t++) {
      var sm = 0;
      for (var q = 0; q < L.length; q++) sm += L[q].pfad[t];
      mittelpfad.push(sm / L.length);
    }
    var bisDatum = new Date((DC._epochTag(asOf) + P.HORIZONT) * 86400000).toISOString().substring(0, 10);
    return {
      status: 'ok', grund_code: null, grund: null, methode: this.METHODE, as_of: asOf, marktklasse: klasse,
      fenster: { von: asOf, bis: bisDatum, tage: P.HORIZONT },
      score: this._runden1(roh), score_roh: roh,
      b1: { wert: b1, k: k1, n: L.length },
      b2: { wert: b2, mittel: mittel },
      b3: { wert: b3, k: k3, n: top.length },
      b4: { wert: b4, mittel: mittelW },
      vergleich_ohne_matching: 5 * (b1 + b2),
      jahre: L.map(function(j) { return j.jahr; }),
      musterjahre: top,
      konformitaet: self.pearson(cur, mittelpfad)
    };
  }
};

window.SA = SA;
