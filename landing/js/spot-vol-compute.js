/**
 * SeasonAlpha — Spot-Vol Beta: EINE Rechnung für /spot-vol-beta (Plan v3 mit Codex-Freigabe 2026-10-19,
 * docs/review_prompts/2026-10-19_spot_vol_beta_plan_v3.md). Reine Funktionen, kein DOM; die Seite rendert nur.
 * Wächter: scripts/verify_spot_vol_beta.py (unabhängige numpy-Referenz).
 *
 * Vertrag (Kurzfassung):
 *  * Achse = offene Sitzungen der Börse des Spot-Tickers (SA.boersenkalender.boerse; alle angebotenen Paare
 *    sind US-Titel gegen Cboe-Indizes) von der ersten gemeinsamen Zeile bis zur letzten
 *    ABGESCHLOSSENEN Sitzung E. Zeilen nach E (laufende Sitzung) zählen nicht; Zeilen an Nicht-Sitzungen
 *    (Phantomzeilen) stehen nicht auf der Achse.
 *  * Renditen nur aus dem gespeicherten log_return (Kursbasis-Wechsel zählen nicht). Rendite eines Tickers an
 *    Sitzung s = Summe der log_return seiner Zeilen nach der vorigen Sitzung bis s; fehlt seine Zeile an der vorigen
 *    Sitzung oder an s (echte Lücke), ist sie unbekannt (null). Paarrendite = beide bekannt.
 *  * Fenster (Rolling-60, RV21, Forward-h, Vortag einer Bedingung) zählen Sitzungen der Achse; jede benötigte
 *    Rendite muss bekannt sein, sonst ist das Ergebnis unbekannt.
 *  * Historienabhängiges (Rolling, expandierende Stress-Schwelle, Eintritte, Sperre) läuft auf der VOLLEN Achse;
 *    der Anzeigezeitraum filtert erst danach. Gesamt-OLS, Buckets, Badge-Quantile, Residuum: Größen des Zeitraums.
 *  * Unbestimmbares ist null bzw. {bestimmbar:false, grund}, nie 0.
 */
window.SA.__release('%%RELEASE%%');   // Releasekennung (landing/js/methode.js) — muss erste Anweisung bleiben
(function () {
  var SA = window.SA = window.SA || {};
  var ROLLING = 60, RV_N = 21, SPERRE = 10, STRESS_MIN = 252, BADGE_MIN = 60;
  var HORIZONTE = [5, 10, 20, 60];

  function K() {
    if (!SA.boersenkalender) throw new Error('SA.boersenkalender fehlt');
    return SA.boersenkalender;
  }
  function endlich(v) { return typeof v === 'number' && isFinite(v); }
  function zahl(v) { if (v == null || v === '') return null; var n = +v; return isFinite(n) ? n : null; }

  /** Quantil wie numpy (linear) über eine aufsteigend sortierte Liste; < 2 Werte → null. */
  function quantil(sortiert, p) {
    if (!sortiert || sortiert.length < 2) return null;
    var idx = (sortiert.length - 1) * p, lo = Math.floor(idx), hi = Math.ceil(idx);
    if (lo === hi) return sortiert[lo];
    return sortiert[lo] * (hi - idx) + sortiert[hi] * (idx - lo);
  }

  /** Letzte abgeschlossene Sitzung zum Zeitpunkt jetztMs: heutige Sitzung erst ab Schluss + 30 min (regulär
   *  16:00 New York — alle Paare der Seite sind US-Titel; Halbtag mit belegter Schlusszeit). */
  function letzteAbgeschlossene(jetztMs, boerse) {
    if (!boerse) throw new Error('boerse fehlt');
    var Kal = K(), h = Kal.heute(boerse, jetztMs), info = Kal.sitzungInfo(h.datum, boerse);
    if (info.offen) {
      var schluss = info.halbtag === true && info.schlusszeit ? info.schlusszeit : '16:00';
      var sm = schluss.split(':'), grenze = (+sm[0]) * 60 + (+sm[1]) + 30;
      var teile = new Intl.DateTimeFormat('en-GB', { timeZone: 'America/New_York', hour: '2-digit', minute: '2-digit',
        hourCycle: 'h23' }).formatToParts(new Date(jetztMs)), w = {};
      for (var i = 0; i < teile.length; i++) w[teile[i].type] = teile[i].value;
      if ((+w.hour) * 60 + (+w.minute) >= grenze) return h.datum;
    }
    return Kal.vorherige(h.datum, boerse, false);
  }

  /** Zeilen eines Tickers bis einschließlich E, aufsteigend, je Datum die erste: {zeilen: [{d, close, lr}], pos: {datum: i}}. */
  function zeilenIndex(zeilen, E) {
    var sortiert = (zeilen || []).filter(function (z) { return z && typeof z.date === 'string' && z.date <= E; })
      .slice().sort(function (a, b) { return a.date < b.date ? -1 : a.date > b.date ? 1 : 0; });
    var liste = [], pos = {}, vorher = null;
    for (var i = 0; i < sortiert.length; i++) {
      var z = sortiert[i], d = z.date.slice(0, 10);
      if (d === vorher) continue;   // doppelte Zeile: erste gewinnt
      var c = zahl(z.close);
      pos[d] = liste.length;
      liste.push({ d: d, close: c != null && c > 0 ? c : null, lr: zahl(z.log_return) });
      vorher = d;
    }
    return { zeilen: liste, pos: pos, erstes: liste.length ? liste[0].d : null,
             letztes: liste.length ? liste[liste.length - 1].d : null };
  }

  /** Rendite der Sitzung s seit der vorigen Sitzung vorS: Summe der gespeicherten log_return aller eigenen Zeilen
   *  nach vorS bis s. Zeilen dazwischen liegen an Nicht-Sitzungen (Phantomzeilen, z. B. ein kopierter Kurs am
   *  Feiertag) — ihre Rendite gehört zur Sitzungsrendite, die Summe ist exakt. Fehlt die Zeile an vorS oder an s,
   *  oder ist eine Rendite unbekannt, ist die Sitzungsrendite unbekannt (echte Lücke). */
  function sitzungsRendite(ix, s, vorS) {
    var j = ix.pos[s], k = ix.pos[vorS];
    if (j == null || k == null || k >= j) return null;
    var sum = 0;
    for (var m = k + 1; m <= j; m++) { if (ix.zeilen[m].lr == null) return null; sum += ix.zeilen[m].lr; }
    return sum;
  }

  /**
   * Gemeinsame Sitzungsachse. jetztMs Pflicht (Frische). Rückgabe:
   * {E, spotEnde, volEnde, sitzungen[], spLR[], voLR[], spClose[], voClose[]} — Arrays parallel zu sitzungen.
   */
  function achse(spotZeilen, volZeilen, jetztMs, boerse) {
    if (typeof jetztMs !== 'number') throw new Error('jetztMs fehlt');
    var Kal = K(), E = letzteAbgeschlossene(jetztMs, boerse);
    var sp = zeilenIndex(spotZeilen, E), vo = zeilenIndex(volZeilen, E);
    var leer = { E: E, spotEnde: sp.letztes, volEnde: vo.letztes, sitzungen: [], spLR: [], voLR: [], spClose: [], voClose: [] };
    if (!sp.erstes || !vo.erstes) return leer;
    var start = sp.erstes > vo.erstes ? sp.erstes : vo.erstes;
    if (start > E) return leer;
    var s = Kal.sitzungen(start, E, boerse);
    if (!s.length) return leer;
    var vor = Kal.vorherige(s[0], boerse, false);
    var out = { E: E, spotEnde: sp.letztes, volEnde: vo.letztes, sitzungen: s, spLR: [], voLR: [], spClose: [], voClose: [] };
    for (var i = 0; i < s.length; i++) {
      var d = s[i], vorS = i === 0 ? vor : s[i - 1];
      var ja = sp.pos[d], jb = vo.pos[d];
      out.spClose.push(ja != null ? sp.zeilen[ja].close : null);
      out.voClose.push(jb != null ? vo.zeilen[jb].close : null);
      out.spLR.push(sitzungsRendite(sp, d, vorS));
      out.voLR.push(sitzungsRendite(vo, d, vorS));
    }
    return out;
  }

  /** Renditereihe je Schalter: log oder einfach (expm1). */
  function renditen(lr, log) {
    return lr.map(function (r) { return r == null ? null : (log ? r : Math.expm1(r)); });
  }

  /** OLS y = α + βx über Paare; N < 3, Var(x)=0 oder Var(y)=0 → bestimmbar:false. */
  function ols(xs, ys) {
    var n = xs.length;
    if (n < 3) return { bestimmbar: false, grund: 'zu_wenige', n: n };
    var mx = 0, my = 0, i, x0 = xs[0], x1 = xs[0], y0 = ys[0], y1 = ys[0];
    for (i = 0; i < n; i++) {
      mx += xs[i]; my += ys[i];
      if (xs[i] < x0) x0 = xs[i]; if (xs[i] > x1) x1 = xs[i]; if (ys[i] < y0) y0 = ys[i]; if (ys[i] > y1) y1 = ys[i];
    }
    // Konstant = Spannweite 0. sxx > 0 allein genügt nicht: der Mittelwert konstanter Dezimalwerte hat Rundungsreste
    // (x = [0.1, 0.1, 0.1] ergab β ≈ 0,04 — Codex Code-R1).
    if (x0 === x1 || y0 === y1) return { bestimmbar: false, grund: 'konstant', n: n };
    mx /= n; my /= n;
    var sxx = 0, syy = 0, sxy = 0;
    for (i = 0; i < n; i++) { var dx = xs[i] - mx, dy = ys[i] - my; sxx += dx * dx; syy += dy * dy; sxy += dx * dy; }
    if (!(sxx > 0) || !(syy > 0)) return { bestimmbar: false, grund: 'konstant', n: n };
    var beta = sxy / sxx, alpha = my - beta * mx, corr = sxy / Math.sqrt(sxx * syy);
    var sse = 0;
    for (i = 0; i < n; i++) { var e = ys[i] - alpha - beta * xs[i]; sse += e * e; }
    return { bestimmbar: true, n: n, beta: beta, alpha: alpha, corr: corr, r2: corr * corr,
             s: Math.sqrt(sse / (n - 2)) };
  }

  /** Paare (x, y) an den Indizes, an denen beide bekannt sind. */
  function paare(x, y, indizes) {
    var xs = [], ys = [], ix = [];
    for (var k = 0; k < indizes.length; k++) {
      var i = indizes[k];
      if (x[i] != null && y[i] != null) { xs.push(x[i]); ys.push(y[i]); ix.push(i); }
    }
    return { xs: xs, ys: ys, ix: ix };
  }

  /** Rolling-OLS-Steigung über genau w Sitzungen; jede Paarrendite im Fenster muss bekannt sein, x nicht konstant. */
  function rolling(x, y, w) {
    w = w || ROLLING;
    var n = x.length, out = new Array(n), luecke = -1, i;
    for (i = 0; i < n; i++) out[i] = null;
    for (i = 0; i < n; i++) {
      if (x[i] == null || y[i] == null) { luecke = i; continue; }
      if (i - luecke < w) continue;
      var mx = 0, my = 0, k, x0 = x[i], x1 = x[i];
      for (k = i - w + 1; k <= i; k++) { mx += x[k]; my += y[k]; if (x[k] < x0) x0 = x[k]; if (x[k] > x1) x1 = x[k]; }
      if (x0 === x1) continue;   // konstante Spot-Renditen im Fenster: keine Steigung (Rundungsreste, s. ols)
      mx /= w; my /= w;
      var sxx = 0, sxy = 0;
      for (k = i - w + 1; k <= i; k++) { var dx = x[k] - mx; sxx += dx * dx; sxy += dx * (y[k] - my); }
      if (sxx > 0) out[i] = sxy / sxx;
    }
    return out;
  }

  /** Expandierendes Quantil p aller bekannten Werte VOR i; erst ab mind Vorwerten, sonst null. */
  function expandierendesQuantil(werte, p, mind) {
    mind = mind || STRESS_MIN;
    var n = werte.length, out = new Array(n), sortiert = [];
    for (var i = 0; i < n; i++) {
      out[i] = sortiert.length >= mind ? quantil(sortiert, p) : null;
      var v = werte[i];
      if (v != null) {
        var lo = 0, hi = sortiert.length;
        while (lo < hi) { var m = (lo + hi) >> 1; if (sortiert[m] <= v) lo = m + 1; else hi = m; }
        sortiert.splice(lo, 0, v);
      }
    }
    return out;
  }

  /** Eintritte: c[i] wahr und c[i−1] bekannt falsch; innerhalb SPERRE Sitzungen nach dem letzten akzeptierten
   *  Ereignis verworfen (nicht nachgeholt). c: Array aus true/false/null. */
  function eintritte(c, sperre) {
    sperre = sperre == null ? SPERRE : sperre;
    var ev = [], letztes = -Infinity;
    for (var i = 1; i < c.length; i++) {
      if (c[i] !== true || c[i - 1] !== false) continue;
      if (i - letztes < sperre) continue;
      ev.push(i); letztes = i;
    }
    return ev;
  }

  /** Einfache Forward-Rendite (in %) über h Sitzungen ab i aus den Spot-Renditen; jede muss bekannt sein. */
  function forward(spLR, i, h) {
    if (i + h >= spLR.length) return null;
    var s = 0;
    for (var k = i + 1; k <= i + h; k++) { if (spLR[k] == null) return null; s += spLR[k]; }
    return Math.expm1(s) * 100;
  }

  function stat(werte) {
    var v = werte.filter(function (x) { return x != null; });
    if (!v.length) return null;
    v.sort(function (a, b) { return a - b; });
    var s = 0, g = 0;
    for (var i = 0; i < v.length; i++) { s += v[i]; if (v[i] > 0) g++; }
    var med = v.length % 2 ? v[(v.length - 1) / 2] : (v[v.length / 2 - 1] + v[v.length / 2]) / 2;
    return { avg: s / v.length, median: med, win_rate: g / v.length * 100, max: v[v.length - 1], min: v[0], n: v.length };
  }

  /** RV21 (annualisiert, %) an i aus den Spot-Log-Renditen i−20..i, Stichprobenvarianz (÷ N−1). */
  function rv(spLR, i, n) {
    n = n || RV_N;
    if (i - n + 1 < 0) return null;
    var m = 0, k;
    for (k = i - n + 1; k <= i; k++) { if (spLR[k] == null) return null; m += spLR[k]; }
    m /= n;
    var q = 0;
    for (k = i - n + 1; k <= i; k++) { var d = spLR[k] - m; q += d * d; }
    return Math.sqrt(252 / (n - 1) * q) * 100;
  }

  /** Anzeigezeitraum: Start = E minus n Jahre (29.02. → 28.02.), 'max' → null. Zeitzonenfrei. */
  function zeitraumStart(E, jahre) {
    if (jahre === 'max' || jahre == null) return null;
    var j = +E.slice(0, 4) - (+jahre), md = E.slice(5);
    if (md === '02-29') md = '02-28';
    return j + '-' + md;
  }

  /** Vollständige Auswertung. opts: {jetztMs, boerse, jahre, log, spike, low, stressP (0..1)}. */
  function auswerten(spotZeilen, volZeilen, opts) {
    var a = achse(spotZeilen, volZeilen, opts.jetztMs, opts.boerse);
    var n = a.sitzungen.length;
    var x = renditen(a.spLR, !!opts.log), y = renditen(a.voLR, !!opts.log);
    var xe = renditen(a.spLR, false), ye = renditen(a.voLR, false);
    var roll = rolling(x, y, ROLLING);
    var stressQ = expandierendesQuantil(roll, opts.stressP, STRESS_MIN);
    var start = zeitraumStart(a.E, opts.jahre);
    var anz = [];
    for (var i = 0; i < n; i++) if (!start || a.sitzungen[i] >= start) anz.push(i);
    var imZeitraum = function (i) { return !start || a.sitzungen[i] >= start; };

    // Ereignisse auf der vollen Achse, danach gefiltert
    var cSpike = a.voClose.map(function (v) { return v == null ? null : v >= opts.spike; });
    var cLow = a.voClose.map(function (v) { return v == null ? null : v <= opts.low; });
    var cStress = roll.map(function (r, i) { return r == null || stressQ[i] == null ? null : r <= stressQ[i]; });
    function ereignisse(c, label) {
      var ix = eintritte(c, SPERRE).filter(imZeitraum);
      var ev = ix.map(function (i) {
        var e = { datum: a.sitzungen[i], spot: a.spClose[i], vol: a.voClose[i], beta: roll[i], schwelle: stressQ[i] };
        HORIZONTE.forEach(function (h) { e['fwd_' + h] = forward(a.spLR, i, h); });
        return e;
      });
      var st = {};
      HORIZONTE.forEach(function (h) { st[h] = stat(ev.map(function (e) { return e['fwd_' + h]; })); });
      return { label: label, n: ev.length, ereignisse: ev, stats: st };
    }

    // Gesamt-OLS des Zeitraums
    var p = paare(x, y, anz);
    var fit = ols(p.xs, p.ys);

    // Regime-Badge: Rolling an E gegen q20/q80 der Rolling-Werte im Zeitraum
    var iE = n && a.sitzungen[n - 1] === a.E ? n - 1 : -1;
    var rWerte = anz.map(function (i) { return roll[i]; }).filter(function (v) { return v != null; }).sort(function (u, v) { return u - v; });
    var badge = { regime: 'nicht_bestimmbar', aktuell: iE >= 0 ? roll[iE] : null, q20: null, q80: null, n: rWerte.length };
    if (rWerte.length >= BADGE_MIN && badge.aktuell != null) {
      badge.q20 = quantil(rWerte, 0.2); badge.q80 = quantil(rWerte, 0.8);
      if (badge.q20 !== badge.q80) {
        if (badge.aktuell > 0) badge.regime = 'positiv';
        else if (badge.aktuell <= badge.q20) badge.regime = 'staerker';
        else if (badge.aktuell >= badge.q80) badge.regime = 'schwaecher';
        else badge.regime = 'ueblich';
      }
    }

    // Letzter Tag gegen die Regression (immer einfache Renditen)
    var res = { bestimmbar: false, datum: a.E, grund: 'keine_paarrendite' };
    if (iE >= 0 && xe[iE] != null && ye[iE] != null) {
      var tr = paare(xe, ye, anz.filter(function (i) { return i !== iE; }));
      var f = ols(tr.xs, tr.ys);
      if (!f.bestimmbar) res = { bestimmbar: false, datum: a.E, grund: f.grund };
      else {
        var xE = xe[iE], yE = ye[iE], rE = yE - (f.alpha + f.beta * xE), k = 0, kg = null;
        for (var t = 0; t < tr.xs.length; t++) if (tr.ys[t] - (f.alpha + f.beta * tr.xs[t]) > rE) k++;
        if (xE < 0 && yE > 0) {
          kg = 0;
          for (t = 0; t < tr.xs.length; t++) if (tr.xs[t] > xE && tr.xs[t] < 0 && tr.ys[t] > yE) kg++;
        }
        res = { bestimmbar: true, datum: a.E, x: xE * 100, y: yE * 100, erwartet: (f.alpha + f.beta * xE) * 100,
                residuum: rE * 100, z: f.s > 0 ? rE / f.s : null, k: k, N: tr.xs.length, k_grafik: kg,
                beta: f.beta, alpha: f.alpha };
      }
    }

    // Buckets (Quintile der Vol-Schlüsse im Zeitraum), immer einfache Forward-Renditen
    var vols = anz.map(function (i) { return a.voClose[i]; }).filter(function (v) { return v != null; }).sort(function (u, v) { return u - v; });
    var buckets = null;
    if (vols.length >= 50) {
      var th = [quantil(vols, 0.2), quantil(vols, 0.4), quantil(vols, 0.6), quantil(vols, 0.8)];
      var bk = [0, 1, 2, 3, 4].map(function () { return { tage: 0, f1: [], f5: [], f20: [], f60: [] }; });
      anz.forEach(function (i) {
        var v = a.voClose[i];
        if (v == null) return;
        var b = v < th[0] ? 0 : v < th[1] ? 1 : v < th[2] ? 2 : v < th[3] ? 3 : 4;
        bk[b].tage++;
        bk[b].f1.push(forward(a.spLR, i, 1)); bk[b].f5.push(forward(a.spLR, i, 5));
        bk[b].f20.push(forward(a.spLR, i, 20)); bk[b].f60.push(forward(a.spLR, i, 60));
      });
      buckets = { grenzen: th, gesamt: vols.length, eimer: bk.map(function (b) {
        return { tage: b.tage, f1: stat(b.f1), f5: stat(b.f5), f20: stat(b.f20), f60: stat(b.f60) };
      }) };
    }

    // VRP = Vol-Schluss − RV21 am selben Paartag
    var vrp = [];
    anz.forEach(function (i) {
      var r = rv(a.spLR, i, RV_N);
      if (r == null || a.voClose[i] == null) return;
      vrp.push({ datum: a.sitzungen[i], iv: a.voClose[i], rv: r, vrp: a.voClose[i] - r });
    });

    return {
      achse: a, anzeige: anz, x: x, y: y, rolling: roll, stressSchwelle: stressQ,
      ols: fit, badge: badge, residuum: res, buckets: buckets, vrp: vrp,
      ereignisse: {
        spike: ereignisse(cSpike, 'spike'), low: ereignisse(cLow, 'low'), stress: ereignisse(cStress, 'stress')
      },
      horizonte: HORIZONTE.slice(),
      aktuell: { ausgewertet: iE >= 0 && x[iE] != null && y[iE] != null ? a.E : null, letzterPaartag: (function () {
        for (var j = n - 1; j >= 0; j--) if (x[j] != null && y[j] != null) return a.sitzungen[j];
        return null;
      })() }
    };
  }

  SA.spotVol = {
    ROLLING: ROLLING, RV_N: RV_N, SPERRE: SPERRE, STRESS_MIN: STRESS_MIN, BADGE_MIN: BADGE_MIN,
    HORIZONTE: HORIZONTE,
    quantil: quantil, letzteAbgeschlossene: letzteAbgeschlossene, achse: achse, renditen: renditen, ols: ols,
    rolling: rolling, expandierendesQuantil: expandierendesQuantil, eintritte: eintritte, forward: forward,
    stat: stat, rv: rv, zeitraumStart: zeitraumStart, auswerten: auswerten
  };
})();
