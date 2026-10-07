#!/usr/bin/env node
/**
 * probe_i18n_sprache.js — Regressionstest für landing/js/i18n.js (SEO-Plan Phase 1b, G1/G2).
 *
 * Führt den ECHTEN i18n.js mit einem kleinen DOM-Nachbau aus und prüft:
 *   1. Keine automatische Sprachweiterleitung: bei jeder Kombination aus Seite,
 *      Browsersprache und gespeicherter Präferenz bleibt die URL unverändert
 *      (kein location.replace / kein href-Wechsel beim Laden).
 *   2. Die Seitensprache folgt der URL.
 *   3. Nachgeladene Links (wie loadComponent -> _onComponentLoaded/_applyNavLinks)
 *      werden auf EN-Seiten nur umgeschrieben, wenn es die EN-Fassung gibt.
 *   4. switchTo() wechselt nie auf eine erfundene URL; der Sprachknopf ist ohne
 *      Gegenstück deaktiviert; mit hreflang-Gegenstück (Blog) wird dieses genutzt.
 *
 *   node scripts/js/probe_i18n_sprache.js [pfad/zu/i18n.js]
 * Exit 0 = alles grün, 1 = Fehler. Gegen den Stand vor 2026-09-30 muss er rot sein.
 */
'use strict';
const fs = require('fs');
const path = require('path');

const QUELLE = process.argv[2] || path.join(__dirname, '..', '..', 'landing', 'js', 'i18n.js');
const CODE = fs.readFileSync(QUELLE, 'utf8');

function element(attrs) {
  const a = Object.assign({}, attrs);
  const klassen = new Set();
  return {
    disabled: false,
    title: a.title || '',
    // Attribute UND gesetzte Eigenschaften (i18n.js setzt link.rel/.hreflang/.href direkt)
    getAttribute(k) { return k in a ? a[k] : (typeof this[k] === 'string' ? this[k] : null); },
    setAttribute: (k, v) => { a[k] = String(v); },
    removeAttribute: (k) => { delete a[k]; },
    classList: { toggle: (k, an) => (an ? klassen.add(k) : klassen.delete(k)), contains: (k) => klassen.has(k) },
    remove() { this._entfernt = true; },
    _attrs: a,
  };
}

const EN_JSON = JSON.parse(fs.readFileSync(path.join(__dirname, '..', '..', 'landing', 'i18n', 'en.json'), 'utf8'));
const warte = () => new Promise((r) => setTimeout(r, 0));

async function lade({ pfad, sprache, gespeichert, links = [], hreflang = {}, jsonLaden = true }) {
  const navigation = [];
  const anker = links.map((h) => element({ href: h }));
  const knoepfe = [element({ 'data-lang': 'de' }), element({ 'data-lang': 'en' })];
  const kopfLinks = Object.entries(hreflang).map(([l, h]) => element({ rel: 'alternate', hreflang: l, href: h }));
  const speicher = new Map(gespeichert ? [['sa_lang', gespeichert]] : []);
  const location = {
    pathname: pfad,
    replace: (u) => navigation.push(['replace', u]),
    set href(u) { navigation.push(['href', u]); },
    get href() { return 'https://seasonalpha.ai' + pfad; },
  };
  const document = {
    readyState: 'complete',
    documentElement: element({}),
    head: { appendChild: (el) => kopfLinks.push(el) },
    addEventListener() {},
    title: '',
    querySelectorAll(sel) {
      if (sel === 'a[href]') return anker;
      if (sel === '.nav__lang-btn') return knoepfe;
      if (sel === 'link[hreflang]') return kopfLinks.filter((l) => !l._entfernt);
      return [];
    },
    querySelector(sel) {
      const m = /hreflang="([a-z-]+)"/.exec(sel);
      if (sel.startsWith('link[rel="alternate"]') && m) {
        return kopfLinks.find((l) => !l._entfernt && l.getAttribute('hreflang') === m[1]) || null;
      }
      return element({});   // Meta-/Titel-Elemente: harmloser Platzhalter
    },
    createElement: () => element({}),
  };
  const window = { location, SA: undefined };
  const sandbox = {
    window, document, location,
    navigator: { language: sprache, userLanguage: sprache },
    localStorage: { getItem: (k) => (speicher.has(k) ? speicher.get(k) : null), setItem: (k, v) => speicher.set(k, v) },
    sessionStorage: { getItem: () => null, setItem() {} },
    // en.json wird wirklich geladen -> voller Ladepfad (_applyAll, _injectHreflang)
    fetch: () => (jsonLaden ? Promise.resolve({ ok: true, json: () => Promise.resolve(EN_JSON) })
                            : new Promise(() => {})),
    console: { warn() {}, log() {} },
  };
  const fn = new Function(...Object.keys(sandbox), CODE + '\nreturn window.SA || SA;');
  const SA = fn(...Object.values(sandbox));
  SA.i18n.init();
  SA.i18n._onComponentLoaded('nav-container');   // Komponente VOR dem JSON
  for (let i = 0; i < 5; i++) await warte();     // JSON-Laden abschliessen
  SA.i18n._onComponentLoaded('footer-container'); // Komponente NACH dem JSON
  return { SA, navigation, anker, knoepfe, kopfLinks };
}

const fehler = [];
function pruefe(bedingung, text) { if (!bedingung) fehler.push(text); }
const nav = (r) => JSON.stringify(r.navigation);

(async () => {
  // 1 + 2: keine Weiterleitung beim Laden, Sprache folgt der URL (voller Ladepfad inkl. JSON)
  const seiten = ['/', '/scanner', '/crash-fruehwarnung', '/ueber-uns', '/pricing', '/blog/was-ist-saisonalitaet/',
                  '/en/', '/en/scanner'];
  for (const pfad of seiten) {
    for (const sprache of ['en-US', 'de-DE']) {
      for (const gespeichert of [null, 'en', 'de']) {
        let r;
        try { r = await lade({ pfad, sprache, gespeichert }); }
        catch (e) { fehler.push(`${pfad}: Ausnahme ${e.message}`); continue; }
        pruefe(r.navigation.length === 0,
          `${pfad} (Browser ${sprache}, gespeichert ${gespeichert}): Weiterleitung beim Laden ${nav(r)}`);
        pruefe(r.SA.i18n.isEN() === pfad.startsWith('/en'),
          `${pfad} (Browser ${sprache}, gespeichert ${gespeichert}): Sprache passt nicht zur URL`);
      }
    }
  }

  // 3: Links aus nachgeladenen Komponenten auf einer EN-Seite (vor + nach JSON geladen)
  {
    const r = await lade({ pfad: '/en/skew', sprache: 'en-US',
      links: ['/scanner', '/crash-fruehwarnung', '/ueber-uns', '/congress', '/index-effekt', '/dashboard?t=AAPL', '/', '/blog/', '/en/skew'] });
    const ist = r.anker.map((a) => a.getAttribute('href'));
    const soll = ['/en/scanner', '/crash-fruehwarnung', '/ueber-uns', '/congress', '/index-effekt', '/en/dashboard?t=AAPL', '/en/', '/blog/', '/en/skew'];
    pruefe(JSON.stringify(ist) === JSON.stringify(soll), `Link-Umschreibung: ${JSON.stringify(ist)} statt ${JSON.stringify(soll)}`);
  }

  // 4: Sprachumschalter
  {
    const r = await lade({ pfad: '/crash-fruehwarnung', sprache: 'de-DE' });
    r.SA.i18n.switchTo('en');
    pruefe(r.navigation.length === 0, `switchTo('en') auf /crash-fruehwarnung: ${nav(r)} statt kein Wechsel`);
    pruefe(r.knoepfe[1].disabled === true, 'EN-Knopf auf /crash-fruehwarnung nicht deaktiviert');
  }
  {
    const r = await lade({ pfad: '/ueber-uns', sprache: 'de-DE' });
    r.SA.i18n.switchTo('en');
    pruefe(r.navigation.length === 0, `switchTo('en') auf /ueber-uns: ${nav(r)}`);
  }
  {
    const r = await lade({ pfad: '/scanner', sprache: 'de-DE' });
    r.SA.i18n.switchTo('en');
    pruefe(nav(r) === JSON.stringify([['href', '/en/scanner']]), `switchTo('en') auf /scanner: ${nav(r)} statt /en/scanner`);
    pruefe(r.knoepfe[1].disabled === false, 'EN-Knopf auf /scanner fälschlich deaktiviert');
  }
  {
    // gebackene Sprachpaare mit abweichendem Slug: nach dem JSON-Laden unverändert, Wechsel dorthin
    const r = await lade({ pfad: '/en/blog/what-is-seasonality/', sprache: 'en-US',
      hreflang: { en: 'https://seasonalpha.ai/en/blog/what-is-seasonality/', de: 'https://seasonalpha.ai/blog/was-ist-saisonalitaet/' } });
    r.SA.i18n.switchTo('de');
    pruefe(nav(r) === JSON.stringify([['href', '/blog/was-ist-saisonalitaet/']]),
      `switchTo('de') mit gebackenem Paar: ${nav(r)} statt /blog/was-ist-saisonalitaet/`);
  }
  {
    // EN-Seite ohne DE-Paar: kein Wechsel, Knopf deaktiviert
    const r = await lade({ pfad: '/en/blog/nur-englisch/', sprache: 'en-US' });
    r.SA.i18n.switchTo('de');
    pruefe(r.navigation.length === 0, `switchTo('de') ohne DE-Paar: ${nav(r)} statt kein Wechsel`);
    pruefe(r.knoepfe[0].disabled === true, 'DE-Knopf ohne Gegenstück nicht deaktiviert');
  }
  {
    const r = await lade({ pfad: '/en/scanner', sprache: 'en-US' });
    r.SA.i18n.switchTo('de');
    pruefe(nav(r) === JSON.stringify([['href', '/scanner']]), `switchTo('de') auf /en/scanner: ${nav(r)} statt /scanner`);
  }

  // 5: per JS gebaute Links (Scanner/Watchlist) in der Seitensprache
  {
    const en = await lade({ pfad: '/en/watchlist', sprache: 'en-US' });
    const de = await lade({ pfad: '/watchlist', sprache: 'en-US' });
    const pf = (r, p) => (typeof r.SA.i18n.pfad === 'function' ? r.SA.i18n.pfad(p) : '(fehlt)');
    pruefe(pf(en, '/dashboard') === '/en/dashboard', `pfad('/dashboard') auf EN: ${pf(en, '/dashboard')}`);
    pruefe(pf(en, '/crash-fruehwarnung') === '/crash-fruehwarnung', `pfad() ohne EN-Fassung: ${pf(en, '/crash-fruehwarnung')}`);
    pruefe(pf(de, '/dashboard') === '/dashboard', `pfad('/dashboard') auf DE: ${pf(de, '/dashboard')}`);
  }

  // 6: abweichende EN-Adresse (_EN_SLUGS: /wahlen -> /en/elections), in beide Richtungen
  {
    const r = await lade({ pfad: '/en/skew', sprache: 'en-US', links: ['/wahlen', '/wahlen/', '/wahlen?snapshot=x', '/wahlen#faq'] });
    const ist = r.anker.map((a) => a.getAttribute('href'));
    const soll = ['/en/elections', '/en/elections', '/en/elections?snapshot=x', '/en/elections#faq'];
    pruefe(JSON.stringify(ist) === JSON.stringify(soll), `EN-Slug Links: ${JSON.stringify(ist)} statt ${JSON.stringify(soll)}`);
    pruefe(r.SA.i18n.pfad('/wahlen') === '/en/elections', `pfad('/wahlen') auf EN: ${r.SA.i18n.pfad('/wahlen')}`);
  }
  {
    const r = await lade({ pfad: '/wahlen', sprache: 'de-DE' });
    r.SA.i18n.switchTo('en');
    pruefe(nav(r) === JSON.stringify([['href', '/en/elections']]), `switchTo('en') auf /wahlen: ${nav(r)} statt /en/elections`);
  }
  {
    const r = await lade({ pfad: '/en/elections', sprache: 'en-US' });
    r.SA.i18n.switchTo('de');
    pruefe(nav(r) === JSON.stringify([['href', '/wahlen']]), `switchTo('de') auf /en/elections: ${nav(r)} statt /wahlen`);
    pruefe(r.knoepfe[0].disabled === false, 'DE-Knopf auf /en/elections fälschlich deaktiviert');
    const hl = r.kopfLinks.filter((l) => !l._entfernt).map((l) => [l.getAttribute('hreflang'), l.getAttribute('href')]);
    pruefe(JSON.stringify(hl) === JSON.stringify([['de', 'https://seasonalpha.ai/wahlen'], ['en', 'https://seasonalpha.ai/en/elections'],
      ['x-default', 'https://seasonalpha.ai/wahlen']]), `hreflang auf /en/elections: ${JSON.stringify(hl)}`);
  }
  {
    const r = await lade({ pfad: '/en/wahlen', sprache: 'en-US' });   // alte Adresse (nginx leitet um): kein Paar erfinden
    r.SA.i18n.switchTo('de');
    pruefe(nav(r) === JSON.stringify([['href', '/wahlen']]) || r.navigation.length === 0, `switchTo('de') auf /en/wahlen: ${nav(r)}`);
  }

  for (const f of fehler) console.log('  FEHLER ' + f);
  console.log(`probe_i18n_sprache: ${fehler.length} Fehler (${path.basename(QUELLE)})`);
  process.exit(fehler.length ? 1 : 0);
})();
