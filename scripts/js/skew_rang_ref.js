/* Unabhaengige JS-Referenz des Skew-Rangs (Plan v3/v4 B3) — nach der SPEZIFIKATION geschrieben, nicht aus
   landing/pages/skew.html kopiert (die alte Seitenrechnung schnitt das Fenster an der Uhr ab und liess aeltere Tage
   nachruecken). Gegenstueck: shared/skew_rang.py. Aufruf: node skew_rang_ref.js <eingabe.json>
   Eingabe {hist, session}; Ausgabe {ticker: {"92": {...}, ...}} wie rang_gesamt. */
'use strict';
var FENSTER = [92, 183, 365], MIN_NORM = 20;

function gueltig(x) { return typeof x === 'number' && isFinite(x); }
function halbHoch(v) { return Math.floor(v + 0.5); }
function minusTage(iso, n) {
  var d = new Date(Date.UTC(+iso.slice(0, 4), +iso.slice(5, 7) - 1, +iso.slice(8, 10)));
  d.setUTCDate(d.getUTCDate() - n);
  return d.toISOString().slice(0, 10);
}
function auswertung(reihe) {            // reihe: Werte aufsteigend, letzter = Session
  var x = reihe[reihe.length - 1], lo = Infinity, hi = -Infinity, unter = 0;
  for (var i = 0; i < reihe.length; i++) {
    if (reihe[i] < lo) lo = reihe[i];
    if (reihe[i] > hi) hi = reihe[i];
    if (i < reihe.length - 1 && reihe[i] < x) unter++;
  }
  return { rank: hi === lo ? 50 : halbHoch((x - lo) / (hi - lo) * 100),
           pctl: halbHoch(unter / (reihe.length - 1) * 100), wert: x };
}
function datumOk(d) {                 // genau YYYY-MM-DD und ein echtes Kalenderdatum
  if (typeof d !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(d)) return false;
  var t = new Date(Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10)));
  return t.toISOString().slice(0, 10) === d;
}
function differenz(a, b, f) { return gueltig(a) && gueltig(b) ? (a - b) * f : null; }

function rangTicker(arr, session, fenster) {
  var ab = minusTage(session, fenster), z = [], gesehen = {}, doppelt = false;
  (arr || []).forEach(function (e) {
    if (!e || !datumOk(e.date) || !(e.cm_mode === 'cm' || e.cm_mode === 'cm_extrap') || e.date > session) return;
    if (gesehen[e.date]) doppelt = true;          // Duplikat irgendwo bis S sperrt den ganzen Ticker
    gesehen[e.date] = 1;
    if (e.date >= ab) z.push({ d: e.date, e: e });
  });
  if (doppelt) return null;
  z.sort(function (a, b) { return a.d < b.d ? -1 : a.d > b.d ? 1 : 0; });
  var aus = {}, metr = {
    rr: function (e) { return differenz(e.call_iv, e.put_iv, 1); },
    iv: function (e) { return gueltig(e.call_iv) && gueltig(e.put_iv) ? (e.put_iv + e.call_iv) / 2 : null; },
    skew: function (e) { return e.skew_pts; }
  };
  Object.keys(metr).forEach(function (m) {
    var werte = [], letztesDatum = null;
    z.forEach(function (r) { var v = metr[m](r.e); if (gueltig(v)) { werte.push(v); letztesDatum = r.d; } });
    if (werte.length >= MIN_NORM && letztesDatum === session) {
      var a = auswertung(werte); aus[m] = { n: werte.length, rank: a.rank, pctl: a.pctl, wert: a.wert };
    }
  });
  var cz = [], pz = [], letzt = null;
  z.forEach(function (r) {
    var c = gueltig(r.e.call_zeta_pts) ? r.e.call_zeta_pts : differenz(r.e.call_iv, r.e.iv_atm, 100);
    var p = gueltig(r.e.put_zeta_pts) ? r.e.put_zeta_pts : differenz(r.e.put_iv, r.e.iv_atm, 100);
    if (gueltig(c) && gueltig(p)) { cz.push(c); pz.push(p); letzt = r.d; }
  });
  if (cz.length >= MIN_NORM && letzt === session) {
    var ac = auswertung(cz), ap = auswertung(pz);
    aus.zeta = { n: cz.length, cz: ac, pz: ap };
  }
  return aus;
}

function rangGesamt(hist, session) {
  var out = {};
  Object.keys(hist || {}).forEach(function (t) {
    if (t.indexOf('__') === 0 || !Array.isArray(hist[t])) return;
    var je = {};
    FENSTER.forEach(function (f) {
      var r = rangTicker(hist[t], session, f);
      if (r && Object.keys(r).length) je[String(f)] = r;
    });
    if (Object.keys(je).length) out[t] = je;
  });
  return out;
}

module.exports = { rangTicker: rangTicker, rangGesamt: rangGesamt };
if (require.main === module) {
  var ein = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
  process.stdout.write(JSON.stringify(rangGesamt(ein.hist, ein.session)));
}
