/**
 * SeasonAlpha — Wahlen und Börse: Rechenkern der Seite /wahlen (ohne DOM).
 *
 * Eingabe: landing/data/wahlen_study.json (scripts/build_wahlen.py, Python-Kern
 * shared/elections.py). Anker, Sitzungszuordnung und Gültigkeit kommen FERTIG aus
 * Python; hier passiert nur: Auswahl der Offsets −X…+Y, Umbasierung, Renditen,
 * Aggregation (Plan docs/review_prompts/2026-10-06_wahlen_plan.md, Abschnitt 11).
 * Zwilling: shared/elections.py::aggregiere — geprüft von scripts/verify_wahlen_twin.py.
 *
 * Regeln:
 *  - Eine Wahl zählt nur, wenn ALLE Offsets −X…+Y einen Kurs haben (konstante Stichprobe
 *    über die ganze Kurve, R4-2).
 *  - Quantile linear interpoliert wie numpy (CLAUDE.md: nie Floor-Indexing).
 *  - Referenz („Jahr ohne Wahl"): nur vollständige Tripel (Wahl + beide Kontrolljahre
 *    gültig über −X…+Y); Kontrollpfade erst einzeln umbasiert, dann je Block gemittelt,
 *    dann über die Blöcke (R2-4).
 *  - Ergebnisfilter (Machtwechsel) sind rückblickend — am Einstiegstag nicht bekannt.
 */
(function (root) {
  'use strict';

  var N_DEFAULT = 60;

  function quantil(werte, q) {
    var a = werte.slice().sort(function (x, y) { return x - y; });
    if (!a.length) return null;
    var pos = (a.length - 1) * q, lo = Math.floor(pos), hi = Math.ceil(pos);
    return a[lo] + (a[hi] - a[lo]) * (pos - lo);
  }

  function mittel(werte) {
    if (!werte.length) return null;
    var s = 0;
    for (var i = 0; i < werte.length; i++) s += werte[i];
    return s / werte.length;
  }

  /** Kurswerte −x…+y aus einem Pfad, oder null, wenn ein Offset fehlt. */
  function ausschnitt(pfad, x, y, n) {
    if (!pfad || !pfad.c) return null;
    var out = [];
    for (var k = -x; k <= y; k++) {
      var v = pfad.c[n + k];
      if (v === null || v === undefined) return null;
      out.push(v);
    }
    return out;
  }

  /** Umbasierung auf 100 beim Index `basisIdx` des Ausschnitts. */
  function umbasieren(werte, basisIdx) {
    var b = werte[basisIdx];
    return werte.map(function (v) { return 100 * v / b; });
  }

  /** Datum zu einem Offset: t0 + Kalendertage (Python exportiert `tage`). */
  function datum(pfad, off, n) {
    n = n || N_DEFAULT;
    var t = pfad.tage ? pfad.tage[n + off] : null;
    if (t === null || t === undefined) return null;
    var d = new Date(pfad.t0 + 'T12:00:00Z');
    d.setUTCDate(d.getUTCDate() + t);
    return d.toISOString().slice(0, 10);
  }

  function passtFilter(w, opts) {
    if (opts.typ && opts.typ !== 'alle' && w.type !== opts.typ) return false;
    if (opts.abJahr && parseInt(w.date.slice(0, 4), 10) < opts.abJahr) return false;
    if (opts.wechsel && opts.wechsel !== 'alle') {
      var wert = wechselWert(w);
      if (wert === null) return false;                 // unbekannt fällt aus Ergebnisfiltern heraus
      if ((opts.wechsel === 'ja') !== wert) return false;
    }
    return true;
  }

  /** Rückblickendes Merkmal: Präsident = Parteiwechsel, Midterm = Wechsel der House-Mehrheit. */
  function wechselWert(w) {
    if (w.type === 'president') return (w.machtwechsel === true || w.machtwechsel === false) ? w.machtwechsel : null;
    if (w.type === 'midterm') {
      if (!w.house_before || !w.house_after) return null;
      return w.house_before !== w.house_after;
    }
    return null;
  }

  /**
   * Hauptauswertung.
   * opts: {reihe:'^GSPC', typ:'president'|'midterm'|'alle', x:20, y:20,
   *        basis:'t0'|'tx', abJahr:1928, wechsel:'alle'|'ja'|'nein'}
   */
  function auswerten(st, opts) {
    var n = st.fenster || N_DEFAULT;
    var x = opts.x, y = opts.y, reihe = opts.reihe;
    var basisIdx = opts.basis === 'tx' ? 0 : x;
    var laenge = x + y + 1;
    var wahlen = [], ausgeschlossen = [], tripel = [], live = null;

    st.wahlen.forEach(function (w) {
      if (!passtFilter(w, opts)) return;
      var r = (w.reihen || {})[reihe] || {};
      if (w.status !== 'held') {
        // Chronologisch die nächste Wahl (Codex R1: Dateireihenfolge ist 2028 vor 2026)
        if (r.pfad && (!live || w.date < live.wahl.date)) live = { wahl: w, pfad: r.pfad };
        return;
      }
      var roh = r.pfad ? ausschnitt(r.pfad, x, y, n) : null;
      if (!roh) {
        ausgeschlossen.push({ id: w.id, grund: r.ausgeschlossen || grundImFenster(r.pfad, x, y, n) });
        return;
      }
      var e = {
        id: w.id, type: w.type, date: w.date, t0: r.pfad.t0, meta: w,
        kurve: umbasieren(roh, basisIdx),
        vorlauf: 100 * (roh[x] / roh[0] - 1),
        nachlauf: 100 * (roh[laenge - 1] / roh[x] - 1),
        fenster: 100 * (roh[laenge - 1] / roh[0] - 1),
        basisDatum: datum(r.pfad, opts.basis === 'tx' ? -x : 0, n)
      };
      wahlen.push(e);
      // Referenz-Tripel: beide Kontrolljahre vollständig
      var ks = (r.kontrollen || []).map(function (k) { return k.pfad ? ausschnitt(k.pfad, x, y, n) : null; });
      if (ks.length === 2 && ks[0] && ks[1]) {
        var kk = ks.map(function (a) { return umbasieren(a, basisIdx); });
        var nach = ks.map(function (a) { return 100 * (a[laenge - 1] / a[x] - 1); });
        tripel.push({
          id: w.id,
          refKurve: kk[0].map(function (v, i) { return (v + kk[1][i]) / 2; }),
          refNachlauf: (nach[0] + nach[1]) / 2,
          wahlNachlauf: e.nachlauf
        });
      }
    });

    var kurven = { mittel: [], median: [], p25: [], p75: [], referenz: [] };
    for (var i = 0; i < laenge; i++) {
      var spalte = wahlen.map(function (e) { return e.kurve[i]; });
      kurven.mittel.push(mittel(spalte));
      kurven.median.push(quantil(spalte, 0.5));
      kurven.p25.push(quantil(spalte, 0.25));
      kurven.p75.push(quantil(spalte, 0.75));
      kurven.referenz.push(mittel(tripel.map(function (t) { return t.refKurve[i]; })));
    }
    var nachl = wahlen.map(function (e) { return e.nachlauf; });
    var kennzahlen = {
      n: wahlen.length,
      nachlauf_mittel: mittel(nachl),
      nachlauf_median: quantil(nachl, 0.5),
      vorlauf_mittel: mittel(wahlen.map(function (e) { return e.vorlauf; })),
      fenster_mittel: mittel(wahlen.map(function (e) { return e.fenster; })),
      trefferquote: nachl.length ? nachl.filter(function (v) { return v > 0; }).length / nachl.length : null,
      n_tripel: tripel.length,
      referenz_nachlauf_mittel: mittel(tripel.map(function (t) { return t.refNachlauf; })),
      differenz_mittel: mittel(tripel.map(function (t) { return t.wahlNachlauf - t.refNachlauf; }))
    };
    return {
      offsets: range(-x, y), wahlen: wahlen, ausgeschlossen: ausgeschlossen,
      kurven: kurven, kennzahlen: kennzahlen, live: liveLinie(live, x, y, n, st, reihe)
    };
  }

  function grundImFenster(pfad, x, y, n) {
    if (!pfad) return 'kein_pfad';
    for (var k = -x; k <= y; k++) {
      var g = pfad.grund && pfad.grund[String(k)];
      if (g) return g;
    }
    return 'unvollstaendig';
  }

  /** Live-Linie: auf t−X normiert (nur wenn t−X schon einen Kurs hat), Zukunft null. */
  function liveLinie(live, x, y, n, st, reihe) {
    if (!live) return null;
    var p = live.pfad, basis = p.c[n - x];
    // Datenstand bleibt auch nach dem Wahltag sichtbar, wenn der Pfad schon historisch ist (Codex R1)
    var meta = (st.reihen || {})[reihe] || {};
    var aus = { id: live.wahl.id, date: live.wahl.date, t0: p.t0, t0_projiziert: !!p.t0_projiziert,
                stichtag: p.stichtag || st.letzte_session || null,
                letzter_kurs: p.letzter_kurs || meta.letzter_kurs || null,
                basisDatum: datum(p, -x, n), kurve: null };
    if (basis === null || basis === undefined) return aus;     // Basis liegt noch in der Zukunft
    aus.kurve = [];
    for (var k = -x; k <= y; k++) {
      var v = p.c[n + k];
      aus.kurve.push(v === null || v === undefined ? null : 100 * v / basis);
    }
    return aus;
  }

  function range(a, b) { var r = []; for (var i = a; i <= b; i++) r.push(i); return r; }

  var api = { auswerten: auswerten, quantil: quantil, datum: datum, wechselWert: wechselWert };
  root.SA = root.SA || {};
  root.SA.wahlen = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : this);
