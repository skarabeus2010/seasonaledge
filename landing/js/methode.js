/**
 * methode.js — Kalendermethode, Releasekennung und Seitensperre (docs/KALENDER_UMSTELLUNG.md, V1b;
 * Entwurf docs/review_prompts/2026-10-11_kalender_v1b_entwurf*.md, freigegeben in v6).
 *
 * Wird als ERSTES eigenes Skript jeder Seite eingebunden (CDN-Skripte wie ApexCharts dürfen davor stehen).
 *
 * - SA.kalenderMethode: die Lesermethode der Seite ('alt' | 'kalender_v1'), unveränderbar.
 * - Releasekennung: jedes HTML setzt window.__SA_RELEASE, jede eigene JS-Datei prüft als ERSTE Anweisung
 *   `window.SA.__release('%%RELEASE%%')`. Diese Datei ist die einzige Ausnahme: sie prüft sich als LETZTE Anweisung,
 *   weil sie die Prüfung erst definiert. Passt eine Kennung nicht, sperrt sich die Seite endgültig.
 * - Sperre (SA.__sperre): nicht rücksetzbar. Danach: keine neue Datenanfrage (fetch-Hülle, laufende abgebrochen,
 *   Body-Lesen scheitert), kein Speicher-Schreibzugriff (localStorage/sessionStorage), keine Einfügung ins Dokument
 *   (synchrone Hüllen + Beobachter), kein Chart (ApexCharts-Hülle, alle zerstört), Dokumentinhalt durch einen
 *   Hinweis ersetzt, höchstens ein automatisches Neuladen je 120 s.
 *   Ressourcen (Bilder, Stylesheets, Fremdskripte) sind bewusst NICHT Teil der Netz-Zusage (Entwurf v6).
 *
 * Lokal (ohne Deploy) bleiben Platzhalter in HTML und Dateien stehen — gleich, also keine Sperre.
 */
(function (window) {
  'use strict';
  var SA = window.SA || (window.SA = {});
  if (SA.__release) return;                    // zweite Einbindung: nichts neu definieren (Kennung prüft die letzte Zeile)

  var METHODE = 'alt';
  var RELEASE = '%%RELEASE%%';
  var MARKE = 'sa-release-neuladen';
  var NEULADEN_SPERRE_MS = 120000;

  var gesperrt = false;
  var intern = false;                          // eigene DOM-/Speicheroperationen der Sperre
  var hinweis = null;
  var laufend = [];                            // registrierte fetch-Anfragen {ctl, fertig}
  var charts = [];

  function ReleaseFehler(grund) {
    this.name = 'ReleaseFehler';
    this.message = 'Release-Sperre: ' + grund;
    this.releaseFehler = true;
    this.stack = (new Error(this.message)).stack;
  }
  ReleaseFehler.prototype = Object.create(Error.prototype);
  ReleaseFehler.prototype.constructor = ReleaseFehler;

  function fest(name, wert) {
    Object.defineProperty(SA, name, {value: wert, writable: false, enumerable: true, configurable: false});
  }
  fest('kalenderMethode', METHODE);
  fest('release', RELEASE);
  fest('ReleaseFehler', ReleaseFehler);
  Object.defineProperty(SA, '__gesperrt', {get: function () { return gesperrt; }, enumerable: true, configurable: false});
  SA.istReleaseFehler = function (e) { return !!(e && (e instanceof ReleaseFehler || e.releaseFehler === true)); };

  // ── Datenanfragen: fetch-Hülle ────────────────────────────────────────────────────────────────────────────
  function abmelden(eintrag) {
    var i = laufend.indexOf(eintrag);
    if (i >= 0) laufend.splice(i, 1);
  }

  function huelleAntwort(antwort, eintrag) {
    ['json', 'text', 'arrayBuffer', 'blob', 'formData'].forEach(function (m) {
      if (!antwort || typeof antwort[m] !== 'function') return;
      var orig = antwort[m];
      try {
        Object.defineProperty(antwort, m, {configurable: true, value: function () {
          if (gesperrt) { abmelden(eintrag); return Promise.reject(new ReleaseFehler('Body nach Sperre')); }
          return orig.apply(antwort, arguments).then(function (wert) {
            abmelden(eintrag);
            if (gesperrt) throw new ReleaseFehler('Body nach Sperre');
            return wert;
          }, function (e) {
            abmelden(eintrag);
            if (gesperrt) throw new ReleaseFehler('Body durch Sperre abgebrochen');
            throw e;
          });
        }});
      } catch (e) { /* nicht erweiterbar: die Prüfung nach dem Auflösen fehlt dann, der Abbruch greift trotzdem */ }
    });
    if (antwort && typeof antwort.clone === 'function') {
      var origClone = antwort.clone;
      try {
        Object.defineProperty(antwort, 'clone', {configurable: true, value: function () {
          if (gesperrt) throw new ReleaseFehler('clone nach Sperre');
          var kopie = origClone.apply(antwort, arguments);
          var e2 = {ctl: eintrag.ctl};
          laufend.push(e2);
          return huelleAntwort(kopie, e2);
        }});
      } catch (e) { /* s. o. */ }
    }
    return antwort;
  }

  if (typeof window.fetch === 'function') {
    var origFetch = window.fetch;
    window.fetch = function (eingabe, optionen) {
      if (gesperrt) return Promise.reject(new ReleaseFehler('fetch nach Sperre'));
      var ctl = typeof AbortController === 'function' ? new AbortController() : null;
      var opt = {};
      if (optionen) for (var k in optionen) if (Object.prototype.hasOwnProperty.call(optionen, k)) opt[k] = optionen[k];
      if (ctl) {
        // Signal des Aufrufers: aus den Optionen ODER aus einem übergebenen Request-Objekt (fetch(new Request(u,
        // {signal}))) — sonst ersetzte unser Signal das des Requests und der Abbruch des Aufrufers käme nie an.
        var aufrufer = opt.signal || (eingabe && typeof eingabe === 'object' && eingabe.signal) || null;
        if (aufrufer) {
          if (aufrufer.aborted) ctl.abort();
          else aufrufer.addEventListener('abort', function () { ctl.abort(); });
        }
        opt.signal = ctl.signal;
      }
      var eintrag = {ctl: ctl};
      laufend.push(eintrag);
      var p;
      try {
        p = origFetch.call(window, eingabe, opt);
      } catch (e) {
        abmelden(eintrag);
        return Promise.reject(e);
      }
      return Promise.resolve(p).then(function (antwort) {
        if (gesperrt) { abmelden(eintrag); throw new ReleaseFehler('Antwort nach Sperre'); }
        return huelleAntwort(antwort, eintrag);
      }, function (e) {
        abmelden(eintrag);
        if (gesperrt) throw new ReleaseFehler('Anfrage durch Sperre abgebrochen');
        throw e;
      });
    };
  }

  // ── Dauerhafter Speicher ──────────────────────────────────────────────────────────────────────────────────
  var origSpeicher = {};
  if (typeof window.Storage === 'function' && window.Storage.prototype) {
    ['setItem', 'removeItem', 'clear'].forEach(function (m) {
      var orig = window.Storage.prototype[m];
      if (typeof orig !== 'function') return;
      origSpeicher[m] = orig;
      window.Storage.prototype[m] = function () {
        if (gesperrt && !intern) throw new ReleaseFehler('Speicher nach Sperre');
        return orig.apply(this, arguments);
      };
    });
  }

  // ── Einfügungen ins Dokument (synchron) ───────────────────────────────────────────────────────────────────
  function huelleMethode(proto, name) {
    if (!proto) return;
    var orig = proto[name];
    if (typeof orig !== 'function') return;
    proto[name] = function () {
      if (gesperrt && !intern) throw new ReleaseFehler(name + ' nach Sperre');
      return orig.apply(this, arguments);
    };
  }
  function huelleSetter(proto, name) {
    if (!proto) return;
    var d = Object.getOwnPropertyDescriptor(proto, name);
    if (!d || typeof d.set !== 'function') return;
    Object.defineProperty(proto, name, {configurable: true, enumerable: d.enumerable, get: d.get, set: function (v) {
      if (gesperrt && !intern) throw new ReleaseFehler(name + ' nach Sperre');
      return d.set.call(this, v);
    }});
  }
  if (typeof window.Node === 'function') {
    ['appendChild', 'insertBefore', 'replaceChild'].forEach(function (m) { huelleMethode(window.Node.prototype, m); });
  }
  if (typeof window.Element === 'function') {
    var EP = window.Element.prototype;
    ['append', 'prepend', 'after', 'before', 'replaceWith', 'replaceChildren', 'insertAdjacentElement',
     'insertAdjacentHTML', 'insertAdjacentText'].forEach(function (m) { huelleMethode(EP, m); });
    huelleSetter(EP, 'innerHTML');
    huelleSetter(EP, 'outerHTML');
  }
  if (typeof window.Document === 'function') {
    ['append', 'prepend', 'replaceChildren', 'write', 'writeln'].forEach(function (m) {
      huelleMethode(window.Document.prototype, m);
    });
  }

  // ── Charts ────────────────────────────────────────────────────────────────────────────────────────────────
  // ApexCharts kann vor ODER nach dieser Datei geladen werden (einige Seiten binden das CDN-Skript hinter den
  // eigenen Skripten ein). Deshalb: vorhandenes sofort hüllen, sonst die spätere Zuweisung über einen Setter.
  function huelleCharts(Orig) {
    if (typeof Orig !== 'function' || Orig.__saHuelle) return Orig;
    var Huelle = function (el, opts) {
      if (gesperrt) throw new ReleaseFehler('Chart nach Sperre');
      var c = new Orig(el, opts);
      charts.push(c);
      return c;
    };
    Huelle.prototype = Orig.prototype;
    Object.getOwnPropertyNames(Orig).forEach(function (n) {
      if (n === 'prototype' || n === 'length' || n === 'name' || n === 'caller' || n === 'arguments') return;
      try { Huelle[n] = Orig[n]; } catch (e) { /* schreibgeschützt */ }
    });
    ['render', 'updateSeries', 'updateOptions', 'appendData', 'appendSeries', 'toggleSeries', 'zoomX'].forEach(function (m) {
      var orig = Orig.prototype[m];
      if (typeof orig !== 'function') return;
      Orig.prototype[m] = function () {
        if (gesperrt) return Promise.reject(new ReleaseFehler('Chart nach Sperre'));
        return orig.apply(this, arguments);
      };
    });
    Huelle.__saHuelle = true;
    return Huelle;
  }
  var apexWert = huelleCharts(window.ApexCharts);
  try {
    Object.defineProperty(window, 'ApexCharts', {
      configurable: true, enumerable: true,
      get: function () { return apexWert; },
      set: function (v) { apexWert = huelleCharts(v); }
    });
  } catch (e) {
    if (apexWert) window.ApexCharts = apexWert;
  }

  // ── Sperre ────────────────────────────────────────────────────────────────────────────────────────────────
  function englisch() {
    try { return (window.document.documentElement.lang || '').toLowerCase().indexOf('en') === 0; } catch (e) { return false; }
  }

  function neuladen() {
    var jetzt = Date.now();
    var speicher;
    try { speicher = window.sessionStorage; if (!speicher) return false; } catch (e) { return false; }
    var alt;
    try { alt = Number(speicher.getItem(MARKE)); } catch (e) { return false; }
    if (alt && jetzt - alt < NEULADEN_SPERRE_MS) return false;
    try { intern = true; speicher.setItem(MARKE, String(jetzt)); } catch (e) { return false; } finally { intern = false; }
    try {
      var u = new window.URL(window.location.href);
      u.searchParams.set('r', String(jetzt));
      // Prüfnaht: jsdom kann nicht navigieren; die Sperrprobe zählt über window.__saNeuladen. Im Browser ungesetzt.
      if (typeof window.__saNeuladen === 'function') window.__saNeuladen(u.toString());
      else window.location.replace(u.toString());
      return true;
    } catch (e) { return false; }
  }

  function ersetzeDokument(text) {
    var doc = window.document;
    if (!doc || !doc.body) return false;
    intern = true;
    try {
      hinweis = doc.createElement('div');
      hinweis.setAttribute('role', 'alert');
      hinweis.setAttribute('data-sa-release-sperre', '1');
      hinweis.style.cssText = 'max-width:40rem;margin:4rem auto;padding:1.5rem;font:16px/1.5 system-ui,sans-serif;' +
        'color:#e8e8e8;background:#111;border:1px solid #e8a820;border-radius:8px';
      hinweis.textContent = text;
      doc.body.replaceChildren(hinweis);
    } finally { intern = false; }
    if (typeof window.MutationObserver === 'function') {
      var beobachter = new window.MutationObserver(function (aenderungen) {
        intern = true;
        try {
          aenderungen.forEach(function (a) {
            Array.prototype.forEach.call(a.addedNodes || [], function (n) {
              if (n === hinweis || (n.contains && n.contains(hinweis))) return;
              if (n.parentNode) n.parentNode.removeChild(n);
            });
          });
        } finally { intern = false; }
      });
      beobachter.observe(doc.documentElement, {childList: true, subtree: true});
    }
    return true;
  }

  SA.__sperre = function (grund) {
    if (gesperrt) return;
    gesperrt = true;
    // Netz: laufende Anfragen abbrechen
    laufend.slice().forEach(function (e) { try { if (e.ctl) e.ctl.abort(); } catch (x) { /* weiter */ } });
    laufend.length = 0;
    // Charts zerstören
    charts.forEach(function (c) { try { if (c && typeof c.destroy === 'function') c.destroy(); } catch (x) { /* weiter */ } });
    charts.length = 0;
    if (SA.kurse && typeof SA.kurse._abbrechenAlle === 'function') {
      try { SA.kurse._abbrechenAlle(); } catch (x) { /* weiter */ }
    }
    var en = englisch();
    var automatisch = neuladen();
    var text = automatisch
      ? (en ? 'This page is outdated and is being reloaded.' : 'Seite veraltet — wird neu geladen.')
      : (en ? 'This page is outdated. Please reload it.' : 'Seite veraltet — bitte neu laden.');
    if (!ersetzeDokument(text) && window.document && window.document.addEventListener) {
      window.document.addEventListener('DOMContentLoaded', function () { ersetzeDokument(text); });
    }
    try { if (window.console) window.console.warn('[SA] Release-Sperre:', grund); } catch (x) { /* weiter */ }
  };

  SA.__release = function (kennung) {
    if (gesperrt) throw new ReleaseFehler('Seite gesperrt');
    if (kennung !== window.__SA_RELEASE) {
      var grund = 'Kennung ' + kennung + ' passt nicht zur Seite (' + window.__SA_RELEASE + ')';
      SA.__sperre(grund);
      throw new ReleaseFehler(grund);
    }
  };
})(window);
window.SA.__release('%%RELEASE%%');
