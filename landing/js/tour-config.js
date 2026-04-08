/**
 * SeasonAlpha Guided Tour — Step-Definitionen
 *
 * 13 Schritte ueber 5 Pages. Multi-Page-Navigation via ?tour=step:N
 * Der tour.js Resume-Handler liest diesen Query-Param beim Page-Load und
 * startet die Tour ab dem passenden Step.
 *
 * Struktur jedes Steps:
 *   page            — URL-Pathname auf der dieser Step gerendert wird (fuer Validierung)
 *   element         — CSS-Selector des Highlight-Targets
 *   popover         — Driver.js Popover-Config (title, description, side, align)
 *   navigateAfter   — Optional: { url, step } fuer automatische Navigation nach Next-Click
 *   optional        — Wenn true und Element fehlt, wird der Step uebersprungen statt Tour abzubrechen
 */
window.SA = window.SA || {};

SA.TOUR_STEPS = [
  // ── Phase 1: Landing Page ────────────────────────────────────────────
  {
    page: '/',
    element: '.hero__content',
    popover: {
      title: 'Willkommen bei SeasonAlpha',
      description: 'Datengetriebene Boersenanalyse mit 131 Jahren saisonaler Marktdaten. In 13 Schritten zeigen wir dir die wichtigsten Features.',
      side: 'bottom',
      align: 'center'
    }
  },
  {
    page: '/',
    element: '.nav__cta',
    popover: {
      title: 'Dashboard ist dein Startpunkt',
      description: 'Das Dashboard buendelt alle wichtigen Signale fuer einen Ticker auf einer Seite — KI-Score, Crash-Ampel, Saisonalitaet, Events.',
      side: 'bottom',
      align: 'end'
    },
    navigateAfter: { url: '/dashboard', step: 2 }
  },

  // ── Phase 2: Dashboard ───────────────────────────────────────────────
  {
    page: '/dashboard',
    element: '#ticker-input',
    popover: {
      title: 'Ticker-Auswahl',
      description: 'Waehle einen beliebigen Ticker: SPY, AAPL, ^GSPC, BTC-USD, TSLA, ^DJI, ... Alle Cards aktualisieren sich automatisch.',
      side: 'right',
      align: 'start'
    }
  },
  {
    page: '/dashboard',
    element: '#card-ki',
    popover: {
      title: 'KI-Score 0-10',
      description: 'Composite Score aus 4 Sub-Scores: Musterpfad-Qualitaet, Trend-Projektion, Win-Rate aktueller Monat, Tracking-Qualitaet. Bullish ≥6.5, Bearish ≤3.5.',
      side: 'bottom',
      align: 'start'
    }
  },
  {
    page: '/dashboard',
    element: '#card-crash',
    popover: {
      title: 'Crash-Ampel',
      description: 'Rot = erhoehtes Risiko laut Isolation Forest. Der Score 0-100 vergleicht Vol/DD/Return-Features mit dem 252-Tage-Perzentil des Tickers.',
      side: 'bottom',
      align: 'start'
    }
  },
  {
    page: '/dashboard',
    element: '#card-year',
    popover: {
      title: 'Saisonaler Jahreschart',
      description: 'Historischer Durchschnitt mit 25./75. Perzentil-Baendern vs. aktuelles Jahr (gold). "Heute"-Marker zeigt die aktuelle Position im Jahreszyklus.',
      side: 'top',
      align: 'start'
    }
  },
  {
    page: '/dashboard',
    element: '#card-events',
    popover: {
      title: 'Naechste Events',
      description: 'FOMC, OPEX, Vollmonde und Feiertage mit historischen Returns und Win-Rates ueber ein t-3 bis t+3 Fenster.',
      side: 'top',
      align: 'end'
    },
    navigateAfter: { url: '/jahreszyklus', step: 7 }
  },

  // ── Phase 3: Jahreszyklus ────────────────────────────────────────────
  {
    page: '/jahreszyklus',
    element: '.sidebar',
    popover: {
      title: 'Sidebar-Controls',
      description: 'Ticker, Zeitraum, Glaettung, Perzentil-Baender, Cycle-Overlays, Outlier-Filter. Jede Aenderung rendert alle Charts live neu.',
      side: 'right',
      align: 'start'
    }
  },
  {
    page: '/jahreszyklus',
    element: '#chart-main',
    popover: {
      title: 'Saisonaler Hauptchart',
      description: 'Durchschnitt aller Jahre + Konfidenzband + 25./75. Perzentile. Optional Einzeljahre + Gann Pressure-Chart synchronisiert darunter.',
      side: 'top',
      align: 'center'
    }
  },
  {
    page: '/jahreszyklus',
    element: '#sec-drawdown',
    popover: {
      title: 'Drawdown & Risiko',
      description: 'Wann passieren historisch die groessten Ruecksetzer? Drawdown-Kurve, Worst-DD-Tabelle und Rolling-Volatilitaet pro Zyklus.',
      side: 'top',
      align: 'center'
    },
    navigateAfter: { url: '/backtest-engine', step: 10 },
    optional: true
  },

  // ── Phase 4: Backtest Engine ─────────────────────────────────────────
  {
    page: '/backtest-engine',
    element: '#sel-event',
    popover: {
      title: 'Event-Typ waehlen',
      description: 'FOMC-Meetings, OPEX, Mondphasen, Feiertage, Monatsanfang oder Trifecta. Die Engine rechnet Entry/Exit + KPIs vollautomatisch.',
      side: 'right',
      align: 'start'
    }
  },
  {
    page: '/backtest-engine',
    element: '#tab-nav',
    popover: {
      title: '4 Backtest-Modi',
      description: 'Einzel-Backtest, Parameter-Optimierung (Grid-Search + Heatmap), Walk-Forward (Expanding Window) und Event-Relevanz (t-Test + Cohen\'s d).',
      side: 'bottom',
      align: 'center'
    },
    navigateAfter: { url: '/dashboard?tour=done', step: 12 },
    optional: true
  },

  // ── Phase 5: Abschluss ───────────────────────────────────────────────
  {
    page: '/dashboard',
    element: '.nav__logo',
    popover: {
      title: 'Das war\'s!',
      description: 'Erkunde die 20+ Pages ueber das Menue: Zyklen, Events, Strategien, Scanner, Blog. Die Tour ist jederzeit ueber den "Tour"-Button in der Nav wieder startbar.',
      side: 'bottom',
      align: 'start'
    }
  }
];
