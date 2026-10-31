/**
 * SeasonAlpha — Drawdown-Analyse: EINE Rechnung für /drawdown (Zwilling von shared/drawdown.py).
 * Plan: docs/review_prompts/2026-10-31_drawdown_seite_plan_v3.md (+ v2, Methodik 2026-10-31_drawdown_analyse_plan.md),
 * von Codex mit Auflagen freigegeben. Reine Funktionen, kein DOM; die Seite rendert nur.
 * Wächter: scripts/verify_drawdown.py (unabhängige numpy-Referenz + Python-Zwilling + Handfälle).
 *
 * Verträge (Kurzfassung):
 *  * E = letzte offene Sitzung STRIKT VOR dem heutigen Börsendatum (konservativ; Krypto: letzter abgeschlossener
 *    UTC-Tag, Forex: letzter Werktag vor dem UTC-Datum). Zeilen nach E zählen nicht.
 *  * Achse = offene Sitzungen (SA.boersenkalender) von der ersten Kurszeile bis E. Sitzungsrendite = Summe der
 *    log_return der Zeilen nach der vorigen Sitzung bis s; unbekannt, wenn an s keine Zeile liegt oder eine
 *    beteiligte Rendite fehlt/nicht endlich ist. Ab der ersten unbekannten Rendite ist der Pfad unbekannt —
 *    nie neu basieren, kein laufender Drawdown, keine Ränge.
 *  * Episode Peak → Recovery (erste Sitzung mit Index ≥ Peak), Trough = erste Sitzung mit minimalem DD.
 *    Zeitraum = Peak im Zeitraum (Start = E minus N Kalenderjahre).
 */
window.SA.__release('%%RELEASE%%');   // Releasekennung (landing/js/methode.js) — muss erste Anweisung bleiben
(function () {
  var SA = window.SA = window.SA || {};
  var HORIZONTE = [20, 60, 120], Z95 = 1.959963984540054;
  // Schwellenvergleiche mit Toleranz (log/exp runden in Python und JS im letzten Bit verschieden) — wie shared/drawdown.py
  var EPS = 1e-12;
  // Renditebasis je Instrument: nur belegte Einträge, sonst „neutral“ (wie shared/drawdown.py RENDITEBASIS).
  var RENDITEBASIS = { '^GSPC': 'kursindex', '^NDX': 'kursindex', '^DJI': 'kursindex', '^GDAXI': 'performanceindex' };

  function K() {
    if (!SA.boersenkalender) throw new Error('SA.boersenkalender fehlt');
    return SA.boersenkalender;
  }
  function endlich(v) { return typeof v === 'number' && isFinite(v); }

  /** Quantil wie numpy ('linear'); leere Liste → null. */
  function quantil(werte, q) {
    var s = werte.slice().sort(function (a, b) { return a - b; });
    if (!s.length) return null;
    var pos = (s.length - 1) * q, lo = Math.floor(pos), hi = Math.min(lo + 1, s.length - 1);
    return s[lo] + (s[hi] - s[lo]) * (pos - lo);
  }

  function minusJahre(iso, n) {
    var j = +iso.slice(0, 4) - n, m = iso.slice(5, 7), t = iso.slice(8, 10);
    var schalt = (j % 4 === 0 && j % 100 !== 0) || j % 400 === 0;
    if (m === '02' && t === '29' && !schalt) t = '28';
    return String(j).padStart(4, '0') + '-' + m + '-' + t;
  }

  function stichtag(boerse, jetzt) {
    var h = K().heute(boerse, jetzt);
    return K().vorherige(h.datum, boerse, false);
  }

  function tageZwischen(a, b) {
    return Math.round((Date.UTC(+b.slice(0, 4), +b.slice(5, 7) - 1, +b.slice(8, 10)) -
                       Date.UTC(+a.slice(0, 4), +a.slice(5, 7) - 1, +a.slice(8, 10))) / 864e5);
  }

  // ───────────── Achse ─────────────
  // Fehlende Kurszeile an einer Kalendersitzung: überbrückt nur bei nicht belegtem Kalender (ungeprueft/annahme;
  // FOREX zählt dazu, CRYPTO nie), höchstens BRUECKE_MAX in Folge, spätere Zeile vorhanden und
  // Σ log_return (v, n] = ln(close_n/close_v) auf BRUECKE_TOL genau. Sonst echte Lücke. Fehlen Zeilen am
  // Reihenende vor E: aktueller Wert unbekannt (ende_fehlt). Wie shared/drawdown.py.
  var BRUECKE_TOL = 1e-6, BRUECKE_MAX = 2;
  function achse(zeilen, boerse, jetzt) {
    var daten = zeilen.map(function (z) { return String(z.date).slice(0, 10); });
    for (var q = 1; q < daten.length; q++) {
      if (!(daten[q] > daten[q - 1])) throw new Error('Kurszeilen nicht aufsteigend oder mit doppelten Daten');
    }
    var e = stichtag(boerse, jetzt);
    var aus = { boerse: boerse, e: e, datenende: daten.length ? daten[daten.length - 1] : null, daten: [], lr: [],
                n_nach_e: daten.filter(function (d) { return d > e; }).length, n_phantom: 0, erste_luecke: null,
                ende_fehlt: false, n_ueberbrueckt: 0, ueberbrueckt_jahre: [], kalender_nicht_belegt: [] };
    var z = [], zd = [];
    zeilen.forEach(function (r, i) { if (daten[i] <= e) { z.push(r); zd.push(daten[i]); } });
    if (!z.length) return aus;
    var sitz = K().sitzungen(zd[0], e, boerse), satz = {}, zeileAn = {};
    sitz.forEach(function (s) { satz[s] = true; });
    aus.n_phantom = zd.filter(function (d) { return !satz[d]; }).length;
    zd.forEach(function (d, i) { zeileAn[d] = i; });
    var i0 = -1;
    for (var k0 = 0; k0 < sitz.length; k0++) { if (zeileAn[sitz[k0]] !== undefined) { i0 = k0; break; } }
    if (i0 < 0) return aus;
    sitz = sitz.slice(i0);
    function summe(vRow, nRow) {
      var t = 0;
      for (var q = vRow + 1; q <= nRow; q++) { var x = z[q].log_return; if (!endlich(x)) return null; t += x; }
      return t;
    }
    function brueckenfaehig(fehl, vRow, nRow) {
      if (boerse === 'CRYPTO' || fehl.length > BRUECKE_MAX) return false;
      if (boerse !== 'FOREX' && fehl.some(function (x) { var st = K().status(boerse, +x.slice(0, 4)); return st !== 'ungeprueft' && st !== 'annahme'; })) return false;
      var t = summe(vRow, nRow), cv = z[vRow].close, cn = z[nRow].close;
      if (t === null || !endlich(cv) || !endlich(cn) || cv <= 0 || cn <= 0) return false;
      return Math.abs(t - Math.log(cn / cv)) <= BRUECKE_TOL;
    }
    var vRow = zeileAn[sitz[0]], jahreUe = {};
    aus.daten.push(sitz[0]); aus.lr.push(0);
    var k = 1;
    while (k < sitz.length) {
      var x = sitz[k];
      if (zeileAn[x] !== undefined) {
        var nRow = zeileAn[x];
        aus.daten.push(x); aus.lr.push(summe(vRow, nRow)); vRow = nRow; k++;
        continue;
      }
      var fehl = [];
      while (k < sitz.length && zeileAn[sitz[k]] === undefined) { fehl.push(sitz[k]); k++; }
      if (k === sitz.length) { aus.ende_fehlt = true; break; }
      if (brueckenfaehig(fehl, vRow, zeileAn[sitz[k]])) {
        aus.n_ueberbrueckt += fehl.length;
        fehl.forEach(function (f_) { jahreUe[+f_.slice(0, 4)] = true; });
        continue;
      }
      fehl.forEach(function (f_) { aus.daten.push(f_); aus.lr.push(null); });
    }
    var u = aus.lr.indexOf(null);
    if (u >= 0) aus.erste_luecke = aus.daten[u];
    aus.ueberbrueckt_jahre = Object.keys(jahreUe).map(Number).sort(function (p, q) { return p - q; });
    for (var jahr = +sitz[0].slice(0, 4); jahr <= +e.slice(0, 4); jahr++) {
      var st = K().status(boerse, jahr);
      if (st !== 'belegt' && st !== 'konvention') aus.kalender_nicht_belegt.push(jahr);
    }
    return aus;
  }

  function indexUndDd(a) {
    var ende = a.erste_luecke === null ? a.lr.length : a.lr.indexOf(null);
    var idx = [], hoch = [], dd = [], kum = 0, h = null;
    for (var i = 0; i < ende; i++) {
      kum += a.lr[i];
      var x = Math.exp(kum);
      h = h === null ? x : Math.max(h, x);
      var d = x / h - 1;
      idx.push(x); hoch.push(h); dd.push(d > -EPS ? 0 : d);   // Rundungsrest beim Wiedererreichen ist kein Drawdown
    }
    return { idx: idx, hoch: hoch, dd: dd, bekannt: ende };
  }

  // ───────────── Episoden ─────────────
  function episoden(a, k) {
    var idx = k.idx, n = k.bekannt, aus = [], peak = 0, ep = null;
    for (var i = 1; i < n; i++) {
      if (idx[i] >= idx[peak] * (1 - EPS)) {      // Recovery mit Toleranz (wie shared/drawdown.py)
        if (ep) { ep.r = i; aus.push(ep); ep = null; }
        peak = i;
      } else {
        var d = idx[i] / idx[peak] - 1;
        if (!ep) ep = { p: peak, t: i, r: null, tiefe: d };
        else if (d < ep.tiefe - EPS) { ep.t = i; ep.tiefe = d; }   // Gleichstand → früherer Trough
      }
    }
    if (ep) { ep.laufend = a.erste_luecke === null && !a.ende_fehlt; aus.push(ep); }
    return aus;
  }

  function ersterUebertritt(k, ep, schwelle) {
    var idx = k.idx, h = idx[ep.p], ende = ep.r !== null ? ep.r : k.bekannt;
    for (var i = ep.p + 1; i < ende; i++) { if (idx[i] / h - 1 <= schwelle + EPS) return i; }
    return null;
  }

  function kt(a, i, j) { return tageZwischen(a.daten[i], a.daten[j]); }

  function beschreibe(a, k, ep, dHeute) {
    var z = { peak: a.daten[ep.p], trough: a.daten[ep.t], recovery: ep.r !== null ? a.daten[ep.r] : null,
              max_dd: 100 * ep.tiefe, peak_to_trough: ep.t - ep.p, peak_to_trough_kt: kt(a, ep.p, ep.t) };
    if (ep.r !== null) {
      z.dauer = ep.r - ep.p; z.dauer_kt = kt(a, ep.p, ep.r); z.ttr = ep.r - ep.t; z.ttr_kt = kt(a, ep.t, ep.r);
    }
    if (dHeute !== null && dHeute !== undefined && dHeute < 0) {
      var s = ersterUebertritt(k, ep, dHeute);
      if (s !== null) {
        z.uebertritt = a.daten[s]; z.bis_uebertritt = s - ep.p;
        if (ep.r !== null) z.ab_uebertritt_bis_recovery = ep.r - s;
      }
    }
    return z;
  }

  // ───────────── Auswertung ─────────────
  function analyse(zeilen, boerse, jetzt) {
    var a = achse(zeilen, boerse, jetzt);
    if (a.daten.length < 2) return { achse: a, status: 'zu_wenig_daten' };
    var k = indexUndDd(a), eps = episoden(a, k), letzt = k.bekannt - 1;
    var last = eps.length ? eps[eps.length - 1] : null;
    var aktuell = a.erste_luecke === null && !a.ende_fehlt;
    var lauf = aktuell && last && last.r === null && last.laufend ? last : null;
    var dHeute = aktuell ? k.idx[letzt] / k.hoch[letzt] - 1 : null;
    var status = a.erste_luecke !== null ? 'luecke' : (a.ende_fehlt ? 'nicht_aktuell' : 'ok');
    var out = { achse: a, k: k, eps: eps, status: status, d_heute: dHeute === null ? null : 100 * dHeute };
    if (lauf) {
      var z = beschreibe(a, k, lauf, dHeute);
      z.seit_peak = letzt - lauf.p; z.seit_peak_kt = kt(a, lauf.p, letzt);
      out.laufend = z;
    }
    return out;
  }

  function gruppe(res, start, m) {
    var a = res.achse, k = res.k;
    var grp = res.eps.filter(function (e) { return e.r !== null && a.daten[e.p] >= start && -100 * e.tiefe >= m - 100 * EPS; });
    var dauer = grp.map(function (e) { return e.r - e.p; }), n = grp.length;
    var g = { n: n, dauer_median: quantil(dauer, .5), dauer_q25: quantil(dauer, .25), dauer_q75: quantil(dauer, .75),
              dauer_max: n ? Math.max.apply(null, dauer) : null,
              ttr_median: quantil(grp.map(function (e) { return e.r - e.t; }), .5),
              einzel: grp.map(function (e) { return beschreibe(a, k, e, res.d_heute === null ? null : res.d_heute / 100); }) };
    var lauf = res.laufend;
    g.laufend_erfuellt = !!lauf && -res.d_heute >= m - 100 * EPS;
    if (g.laufend_erfuellt) {
      g.kuerzer_als_laufend = dauer.filter(function (x) { return x < lauf.seit_peak; }).length;
      g.tiefer_als_laufend = grp.filter(function (e) { return 100 * e.tiefe < res.d_heute - 100 * EPS; }).length;
    }
    var stufen = dauer.slice().sort(function (x, y) { return x - y; }).filter(function (v, i, arr) { return i === 0 || v !== arr[i - 1]; });
    g.dauerkurve = n ? [[0, 1]].concat(stufen.map(function (t) {
      return [t, dauer.filter(function (x) { return x > t; }).length / n];
    })) : [];
    return g;
  }

  function grenzueberschreitend(res, start) {
    var a = res.achse, k = res.k;
    return res.eps.filter(function (e) {
      return a.daten[e.p] < start && (e.r === null || a.daten[e.r] >= start) && e.tiefe <= -0.05 + EPS;
    }).map(function (e) { return beschreibe(a, k, e, null); });
  }

  function zeitanteil(res, start) {
    if (res.d_heute === null) return null;
    var a = res.achse, k = res.k, n = 0, mind = 0;
    for (var i = 0; i < k.bekannt; i++) {
      if (a.daten[i] >= start) { n++; if (100 * k.dd[i] <= res.d_heute + 100 * EPS) mind++; }
    }
    return { n: n, mind: mind };
  }

  function vergleichAb(res, start, x) {
    var a = res.achse, k = res.k, s = -x / 100, tempo = [], ab = [], einzel = [];
    res.eps.forEach(function (e) {
      if (e.r === null || a.daten[e.p] < start) return;
      var c = ersterUebertritt(k, e, s);
      if (c === null) return;
      tempo.push(c - e.p); ab.push(e.r - c);
      einzel.push({ peak: a.daten[e.p], uebertritt: a.daten[c], bis_uebertritt: c - e.p, ab_uebertritt_bis_recovery: e.r - c });
    });
    var laufTempo = null;
    if (res.laufend) {
      var ep = res.eps[res.eps.length - 1], c = ersterUebertritt(k, ep, s);
      laufTempo = c === null ? null : c - ep.p;
    }
    return { x: x, n: ab.length, einzel: einzel, ab_median: quantil(ab, .5), ab_q25: quantil(ab, .25),
             ab_q75: quantil(ab, .75), tempo_laufend: laufTempo,
             langsamer_als_laufend: laufTempo === null ? null : tempo.filter(function (t) { return t > laufTempo; }).length };
  }

  function kaplanMeier(res, start, x) {
    var a = res.achse, k = res.k, s = -x / 100, letzt = k.bekannt - 1, beob = [];
    res.eps.forEach(function (e) {
      if (a.daten[e.p] < start) return;
      var c = ersterUebertritt(k, e, s);
      if (c === null) return;
      beob.push(e.r !== null ? [e.r - c, 1] : [letzt - c, 0]);
    });
    beob.sort(function (p, q) { return p[0] - q[0] || q[1] - p[1]; });
    var nRisk = beob.length, sT = 1, varSum = 0, median = null;
    var kurve = [{ t: 0, s: 1, risiko: nRisk, lo: null, hi: null }];
    var i = 0;
    while (i < beob.length) {
      var t = beob[i][0], d = 0, c = 0;
      beob.forEach(function (b) { if (b[0] === t) { if (b[1] === 1) d++; else c++; } });
      if (d) {
        sT *= (1 - d / nRisk);
        if (nRisk - d > 0) varSum += d / (nRisk * (nRisk - d));
        var lo = null, hi = null;
        if (sT > 0 && sT < 1) {
          var se = Math.sqrt(varSum) / Math.abs(Math.log(sT)), ll = Math.log(-Math.log(sT));
          lo = Math.exp(-Math.exp(ll + Z95 * se)); hi = Math.exp(-Math.exp(ll - Z95 * se));
        }
        kurve.push({ t: t, s: sT, risiko: nRisk, lo: lo, hi: hi });
        if (median === null && sT <= 0.5) median = t;
      }
      nRisk -= d + c;
      i += d + c;
    }
    return { x: x, n: beob.length, ereignisse: beob.filter(function (b) { return b[1] === 1; }).length,
             zensiert: beob.filter(function (b) { return b[1] === 0; }).map(function (b) { return b[0]; }),
             kurve: kurve, median: median };
  }

  function forwardReturns(res, start, x) {
    var a = res.achse, k = res.k, s = -x / 100, letzt = k.bekannt - 1, lr = a.lr, ereig = [];
    res.eps.forEach(function (e) {
      if (a.daten[e.p] < start) return;
      var c = ersterUebertritt(k, e, s);
      if (c !== null) ereig.push(c);
    });
    function pfad(i, h) {
      if (i + h > letzt) return null;
      var kum = 0, mn = 0;
      for (var j = i + 1; j <= i + h; j++) { kum += lr[j]; mn = Math.min(mn, Math.exp(kum) - 1); }
      return [Math.exp(kum) - 1, mn];
    }
    function kz(v) {
      if (!v.length) return null;
      var f = v.map(function (w) { return 100 * w[0]; });
      return { n: v.length, mittel: f.reduce(function (p, q) { return p + q; }, 0) / f.length, median: quantil(f, .5),
               anteil_positiv: v.filter(function (w) { return w[0] > EPS; }).length / v.length,
               zwischenverlust_mittel: v.reduce(function (p, w) { return p + 100 * w[1]; }, 0) / v.length };
    }
    var basisIdx = [];
    for (var i = 0; i < k.bekannt; i++) if (a.daten[i] >= start) basisIdx.push(i);
    var out = { x: x, h: {} };
    HORIZONTE.forEach(function (h) {
      var werte = ereig.map(function (c) { return pfad(c, h); });
      var voll = werte.filter(function (w) { return w !== null; });
      var bas = basisIdx.map(function (i) { return pfad(i, h); }).filter(function (w) { return w !== null; });
      var gueltig = ereig.filter(function (c) { return c + h <= letzt; }), ue = 0;
      for (var p = 0; p < gueltig.length; p++) for (var q = p + 1; q < gueltig.length; q++) if (Math.abs(gueltig[p] - gueltig[q]) < h) ue++;
      out.h[String(h)] = { ereignisse: kz(voll), unvollstaendig: werte.length - voll.length, basis: kz(bas), ueberlappende_paare: ue };
    });
    return out;
  }

  function kalender(res) {
    var a = res.achse, k = res.k, daten = a.daten, jahre = [], gesehen = {};
    daten.forEach(function (d) { var j = d.slice(0, 4); if (!gesehen[j]) { gesehen[j] = true; jahre.push(j); } });
    return jahre.map(function (j) {
      var pos = [];
      daten.forEach(function (d, i) { if (d.slice(0, 4) === j) pos.push(i); });
      var bekannt = pos.every(function (i) { return i < k.bekannt; });
      var z = { jahr: +j, n: pos.length, teiljahr: j === jahre[0] || j === jahre[jahre.length - 1], tiefster: null, ulcer: null };
      if (bekannt && pos.length) {
        var d = pos.map(function (i) { return 100 * k.dd[i]; });
        z.tiefster = Math.min.apply(null, d);
        z.ulcer = Math.sqrt(d.reduce(function (p, x) { return p + x * x; }, 0) / d.length);
      }
      return z;
    });
  }

  function kurve(res) {
    var a = res.achse, k = res.k, out = [];
    for (var i = 0; i < k.bekannt; i++) out.push([a.daten[i], 100 * k.dd[i]]);
    return out;
  }

  SA.drawdown = Object.freeze({
    HORIZONTE: HORIZONTE, EPS: EPS, RENDITEBASIS: RENDITEBASIS, quantil: quantil, minusJahre: minusJahre, stichtag: stichtag, achse: achse,
    analyse: analyse, gruppe: gruppe, grenzueberschreitend: grenzueberschreitend, zeitanteil: zeitanteil,
    vergleichAb: vergleichAb, kaplanMeier: kaplanMeier, forwardReturns: forwardReturns, kalender: kalender, kurve: kurve
  });
})();
