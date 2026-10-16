/* Unabhaengige JS-Referenz des Skew-Rangs (Plan v3/v4 B3) — nach der SPEZIFIKATION geschrieben, nicht aus
   landing/pages/skew.html kopiert (die alte Seitenrechnung schnitt das Fenster an der Uhr ab und liess aeltere Tage
   nachruecken). Gegenstueck: shared/skew_rang.py. Aufruf: node skew_rang_ref.js <eingabe.json>
   Eingabe {hist, session[, mit_status]}; Ausgabe {ticker: {"92": {...}, ...}} wie rang_gesamt, mit mit_status
   {rang, status} (status wie rang_status_gesamt). B3b: ivrv, neu_rand, vorher_datum, sprung, Verfuegbarkeit. */
'use strict';
var FENSTER = [92, 183, 365], MIN_NORM = 20, SPRUNG = 5, RV_MIN = 0.01;

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
function ivrv(iv, rv) { return gueltig(iv) && gueltig(rv) && iv > 0 && rv >= RV_MIN ? iv / rv : null; }
function mitte(xs) {
  var s = xs.slice().sort(function (a, b) { return a - b; }), m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}
function zusatz(werte, daten) {        // werte/daten: gueltige Beobachtungen aufsteigend, letzte = Session
  var x = werte[werte.length - 1], hi = -Infinity, lo = Infinity, d = [], aus = { vorher_datum: daten[daten.length - 2] };
  for (var i = 0; i < werte.length - 1; i++) { hi = Math.max(hi, werte[i]); lo = Math.min(lo, werte[i]); }
  if (x > hi) aus.neu_rand = 'hoch'; else if (x < lo) aus.neu_rand = 'tief';
  for (var j = 1; j < werte.length; j++) d.push(Math.abs(werte[j] - werte[j - 1]));
  var med = mitte(d);
  if (med === 0) aus.sprung_beurteilbar = false; else if (d[d.length - 1] > SPRUNG * med) aus.sprung = true;
  return aus;
}
var METR = {
  rr: function (e) { return differenz(e.call_iv, e.put_iv, 1); },
  iv: function (e) { return gueltig(e.call_iv) && gueltig(e.put_iv) ? (e.put_iv + e.call_iv) / 2 : null; },
  skew: function (e) { return e.skew_pts; },
  ivrv: function (e) { return ivrv(e.iv_atm, e.rv_1m); }
};
function zeilenBis(arr, session) {    // normierte Zeilen mit gueltigem Datum bis S; null bei Duplikat
  var z = [], gesehen = {}, doppelt = false;
  (arr || []).forEach(function (e) {
    if (!e || !datumOk(e.date) || !(e.cm_mode === 'cm' || e.cm_mode === 'cm_extrap') || e.date > session) return;
    if (gesehen[e.date]) doppelt = true;
    gesehen[e.date] = 1;
    z.push({ d: e.date, e: e });
  });
  if (doppelt) return null;
  z.sort(function (a, b) { return a.d < b.d ? -1 : a.d > b.d ? 1 : 0; });
  return z;
}
function statusTicker(arr, session, fenster) {
  var alle = zeilenBis(arr, session);
  if (alle === null) return { '*': { status: 'gesperrt' } };
  if (!alle.length) return {};
  var ab = minusTage(session, fenster), z = alle.filter(function (r) { return r.d >= ab; }), aus = {};
  Object.keys(METR).forEach(function (m) {
    var n = 0, letzt = null;
    z.forEach(function (r) { if (gueltig(METR[m](r.e))) { n++; letzt = r.d; } });
    if (letzt === session) { if (n < MIN_NORM) aus[m] = { n: n, status: 'zu_kurz' }; }
    else aus[m] = { n: n, status: 'kein_wert' };
  });
  return aus;
}

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
  var aus = {};
  Object.keys(METR).forEach(function (m) {
    var werte = [], daten = [], letztesDatum = null;
    z.forEach(function (r) { var v = METR[m](r.e); if (gueltig(v)) { werte.push(v); daten.push(r.d); letztesDatum = r.d; } });
    if (werte.length >= MIN_NORM && letztesDatum === session) {
      var a = auswertung(werte), o = { n: werte.length, rank: a.rank, pctl: a.pctl, wert: a.wert }, zs = zusatz(werte, daten);
      Object.keys(zs).forEach(function (k) { o[k] = zs[k]; });
      aus[m] = o;
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

function statusGesamt(hist, session) {
  var out = {};
  Object.keys(hist || {}).forEach(function (t) {
    if (t.indexOf('__') === 0 || !Array.isArray(hist[t])) return;
    var je = {};
    FENSTER.forEach(function (f) { var s = statusTicker(hist[t], session, f); if (Object.keys(s).length) je[String(f)] = s; });
    if (Object.keys(je).length) out[t] = je;
  });
  return out;
}

module.exports = { rangTicker: rangTicker, rangGesamt: rangGesamt, statusGesamt: statusGesamt };
if (require.main === module) {
  var ein = JSON.parse(require('fs').readFileSync(process.argv[2], 'utf8'));
  process.stdout.write(JSON.stringify(ein.mit_status ? { rang: rangGesamt(ein.hist, ein.session),
    status: statusGesamt(ein.hist, ein.session) } : rangGesamt(ein.hist, ein.session)));
}
