// Probe für scripts/verify_spot_vol_beta.py: führt landing/js/spot-vol-compute.js (SA.spotVol) mit dem echten
// Börsenkalender aus. Eingabe als JSON auf stdin, Ausgabe JSON auf stdout. Keine eigene Rechnung hier.
'use strict';
const fs = require('fs');
const path = require('path');
const wurzel = process.argv[2] || path.join(__dirname, '..', '..', 'landing');
global.window = global;
window.SA = { __release: function () {} };
require(path.join(wurzel, 'js', 'boersenkalender.js'));
require(path.join(wurzel, 'js', 'spot-vol-compute.js'));
const V = window.SA.spotVol;

const ein = JSON.parse(fs.readFileSync(0, 'utf8'));
const aus = { tz_offset_min: new Date(Date.UTC(2026, 0, 15, 12)).getTimezoneOffset(), faelle: {} };
function fang(f) { try { return f(); } catch (e) { return { fehler: String(e && e.message || e) }; } }

(ein.auswertungen || []).forEach(function (a) {
  aus.faelle[a.name] = fang(function () {
    const r = V.auswerten(a.spot, a.vol, a.opts);
    return {
      achse: r.achse, anzeige: r.anzeige, rolling: r.rolling, stressSchwelle: r.stressSchwelle, ols: r.ols,
      badge: r.badge, residuum: r.residuum, buckets: r.buckets, vrp: r.vrp, aktuell: r.aktuell,
      ereignisse: {
        spike: r.ereignisse.spike.ereignisse, low: r.ereignisse.low.ereignisse, stress: r.ereignisse.stress.ereignisse,
        stats_spike: r.ereignisse.spike.stats, stats_stress: r.ereignisse.stress.stats
      }
    };
  });
});
aus.frische = (ein.frische || []).map(function (ms) { return fang(function () { return V.letzteAbgeschlossene(ms, 'NYSE'); }); });
aus.eintritte = (ein.eintritte || []).map(function (c) { return V.eintritte(c[0], c[1]); });
aus.ols = (ein.ols || []).map(function (p) { return V.ols(p[0], p[1]); });
aus.zeitraum = (ein.zeitraum || []).map(function (p) { return V.zeitraumStart(p[0], p[1]); });
aus.quantil = (ein.quantil || []).map(function (p) { return V.quantil(p[0], p[1]); });
process.stdout.write(JSON.stringify(aus));
