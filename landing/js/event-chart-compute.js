/**
 * SA.eventChart — Rechenkern für /event-chart (Darstellung: landing/pages/event-chart.html,
 * Wächter: scripts/verify_event_chart.py mit unabhängiger Python-Referenz).
 *
 *   achse(daten, bisIso)          Handelstage des Basiswerts + künftige Werktage bis bisIso (Liste ISO-Daten)
 *   idxAb(achse, iso)             Index des Termintags, sonst des nächsten Tags der Achse (−1 hinter dem Ende)
 *   durchschnitt(daten, schluss, termine, opts)
 *       daten   aufsteigende ISO-Daten der Kurszeilen, schluss gleich lang (Schlusskurse > 0)
 *       termine ISO-Daten der gewählten Terminart (beliebige Reihenfolge, Dubletten erlaubt)
 *       opts    {vor, nach, start}: start = erstes ISO-Datum, ab dem Termine UND Vergleichstage zählen
 *     → {n, nBasis, start, anker, mittel, median, q1, q3, basis, P, B}
 *
 * Anker = Schluss am Termintag bzw. am nächsten Handelstag (Termin an einem Börsenfeiertag). Pfad k = −vor…+nach:
 * S[a+k] / S[a] · 100. Nur Termine mit vollständigem Fenster; zwei Termine auf demselben Anker zählen einmal.
 * Basis: derselbe Pfad für JEDEN Handelstag ab start mit vollständigem Fenster. Quantile linear wie numpy.
 */
window.SA.__release('%%RELEASE%%');   // Releasekennung (landing/js/methode.js) — muss erste Anweisung bleiben
(function () {
  'use strict';
  var SA = window.SA = window.SA || {};

  function plusTag(iso) {
    var d = new Date(iso + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + 1); return d.toISOString().slice(0, 10);
  }
  function wochentag(iso) { return new Date(iso + 'T12:00:00Z').getUTCDay(); }

  function achse(daten, bisIso) {
    var a = daten.slice();
    if (!a.length) return a;
    var d = a[a.length - 1];
    while (bisIso && d < bisIso) { d = plusTag(d); var w = wochentag(d); if (w !== 0 && w !== 6) a.push(d); }
    return a;
  }

  function idxAb(a, iso) {
    var lo = 0, hi = a.length;
    while (lo < hi) { var m = (lo + hi) >> 1; if (a[m] < iso) lo = m + 1; else hi = m; }
    return lo < a.length ? lo : -1;
  }

  function quantil(s, q) {
    var p = (s.length - 1) * q, lo = Math.floor(p), hi = Math.ceil(p);
    return s[lo] + (s[hi] - s[lo]) * (p - lo);
  }

  function pfade(S, anker, vor, nach) {
    return anker.map(function (a) {
      var p = []; for (var k = -vor; k <= nach; k++) p.push(S[a + k] / S[a] * 100); return p;
    });
  }

  function durchschnitt(daten, schluss, termine, opts) {
    var vor = opts.vor, nach = opts.nach, start = opts.start || '';
    var letzter = daten.length - 1;
    var anker = [], gesehen = {};
    termine.slice().sort().forEach(function (d) {
      if (d < start) return;
      var a = idxAb(daten, d);
      if (a < 0 || a < vor || a + nach > letzter || gesehen[a]) return;
      gesehen[a] = true; anker.push(a);
    });
    var alle = [];
    for (var a = vor; a + nach <= letzter; a++) if (daten[a] >= start) alle.push(a);
    var P = pfade(schluss, anker, vor, nach), B = pfade(schluss, alle, vor, nach);
    var L = vor + nach + 1;
    function mittel(M) {
      var r = []; for (var j = 0; j < L; j++) { var s = 0; for (var i = 0; i < M.length; i++) s += M[i][j]; r.push(s / M.length); } return r;
    }
    var i0 = idxAb(daten, start);
    var res = { n: anker.length, nBasis: alle.length, start: i0 >= 0 ? daten[i0] : null, anker: anker,
                mittel: P.length ? mittel(P) : [], basis: B.length ? mittel(B) : [], median: [], q1: [], q3: [], P: P, B: B };
    if (P.length) {
      for (var j = 0; j < L; j++) {
        var sp = P.map(function (p) { return p[j]; }).sort(function (x, y) { return x - y; });
        res.median.push(quantil(sp, 0.5)); res.q1.push(quantil(sp, 0.25)); res.q3.push(quantil(sp, 0.75));
      }
    }
    return res;
  }

  SA.eventChart = { achse: achse, idxAb: idxAb, quantil: quantil, durchschnitt: durchschnitt };
})();
