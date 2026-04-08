/**
 * SeasonAlpha Guided Tour — Step-Definitionen
 *
 * 23 Schritte über 11 Pages. Multi-Page-Navigation via ?tour=step:N
 * Der tour.js Resume-Handler liest diesen Query-Param beim Page-Load und
 * startet die Tour ab dem passenden Step.
 *
 * Struktur jedes Steps:
 *   page            — URL-Pathname auf der dieser Step gerendert wird
 *   element         — CSS-Selector des Highlight-Targets
 *   popover         — Driver.js Popover-Config (title, description, side, align)
 *   navigateAfter   — Optional: { url, step } für automatische Navigation nach Next-Click
 *   optional        — Wenn true und Element fehlt, wird der Step übersprungen statt Tour abzubrechen
 */
window.SA = window.SA || {};

SA.TOUR_STEPS = [
  // ── Phase 1: Landing Page ────────────────────────────────────────────
  {
    page: '/',
    element: '.hero__content',
    popover: {
      title: 'Willkommen bei SeasonAlpha',
      description: 'Datengetriebene Börsenanalyse mit 131 Jahren saisonaler Marktdaten. In 23 Schritten zeigen wir dir die wichtigsten Features.',
      side: 'bottom',
      align: 'center'
    }
  },
  {
    page: '/',
    element: '.nav__cta',
    popover: {
      title: 'Dashboard ist dein Startpunkt',
      description: 'Das Dashboard bündelt alle wichtigen Signale für einen Ticker auf einer Seite — KI-Score, Crash-Ampel, Saisonalität, Events.',
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
      description: 'Wähle einen beliebigen Ticker: SPY, AAPL, ^GSPC, BTC-USD, TSLA, ^DJI, … Alle Karten aktualisieren sich automatisch.',
      side: 'right',
      align: 'start'
    }
  },
  {
    page: '/dashboard',
    element: '#trading-day-header',
    popover: {
      title: 'Wo bist du im Zyklus?',
      description: 'Der Header zeigt alle saisonalen Koordinaten: <b>TDOM</b> = Trading Day of Month (Handelstag im Monat, z. B. 6/21), <b>TWOY</b> = Trading Week of Year, <b>TDOY</b> = Trading Day of Year, <b>Q</b> = Quartal, <b>MidTerm</b> = Präsidentenzyklus-Phase (Wahljahr, Nachwahl-, Midterm-, Vorwahljahr). Börsen-spezifisch berechnet (NYSE, XETRA, LSE).',
      side: 'bottom',
      align: 'center'
    }
  },
  {
    page: '/dashboard',
    element: '#card-ki',
    popover: {
      title: 'KI-Score 0–10',
      description: 'Composite Score aus vier Sub-Scores: Musterpfad-Qualität, Trend-Projektion, Win-Rate des aktuellen Monats und Tracking-Qualität. Bullish ≥ 6,5, bearish ≤ 3,5.',
      side: 'bottom',
      align: 'start'
    }
  },
  {
    page: '/dashboard',
    element: '#card-crash',
    popover: {
      title: 'Crash-Ampel',
      description: 'Rot = erhöhtes Risiko laut Isolation Forest. Der Score 0–100 vergleicht Vol, Drawdown und Returns mit dem 252-Tage-Perzentil des Tickers.',
      side: 'bottom',
      align: 'start'
    }
  },
  {
    page: '/dashboard',
    element: '#card-year',
    popover: {
      title: 'Saisonaler Jahreschart',
      description: 'Historischer Durchschnitt mit 25./75.-Perzentil-Bändern gegen das aktuelle Jahr (gold). Der "Heute"-Marker zeigt deine Position im Jahreszyklus.',
      side: 'top',
      align: 'start'
    }
  },
  {
    page: '/dashboard',
    element: '#card-events',
    popover: {
      title: 'Nächste Events',
      description: 'FOMC-Meetings, OPEX, Vollmonde und Feiertage mit historischen Returns und Win-Rates über ein t-3 bis t+3 Fenster.',
      side: 'top',
      align: 'end'
    },
    navigateAfter: { url: '/dekadenzyklus', step: 8 }
  },

  // ── Phase 3: Dekadenzyklus ───────────────────────────────────────────
  {
    page: '/dekadenzyklus',
    element: '#chart-lines',
    popover: {
      title: 'Dekadenzyklus — 131 Jahre DJI',
      description: 'Jede Dekade (z. B. 1930er, 1990er, 2020er) ist eine eigene Kohorte. Du siehst, wie sich "Jahre mit gleicher Endziffer" statistisch ähneln — ein fundamentaler Bias den viele Marktteilnehmer übersehen.',
      side: 'top',
      align: 'center'
    },
    navigateAfter: { url: '/jahreszyklus', step: 9 },
    optional: true
  },

  // ── Phase 4: Jahreszyklus ────────────────────────────────────────────
  {
    page: '/jahreszyklus',
    element: '#chart-main',
    popover: {
      title: 'Saisonaler Jahresverlauf',
      description: 'Durchschnitt aller Jahre + Konfidenzband + 25./75.-Perzentile. Optional darunter Einzeljahre und der Gann Pressure Chart — synchronisiert via Chart-Group.',
      side: 'top',
      align: 'center'
    }
  },
  {
    page: '/jahreszyklus',
    element: '.sidebar',
    popover: {
      title: 'Sidebar-Controls',
      description: 'Ticker, Zeitraum, Glättung, Perzentil-Bänder, Cycle-Overlays, Outlier-Filter. Jede Änderung rendert alle Charts live neu.',
      side: 'right',
      align: 'start'
    }
  },
  {
    page: '/jahreszyklus',
    element: '#sec-detrend',
    popover: {
      title: 'Detrend-Indikator',
      description: 'Entfernt den linearen Jahrestrend und zeigt die reine Saisonalität auf einer 0–100-Skala (Midline 50). So erkennst du die saisonalen Hoch- und Tiefpunkte ohne vom langfristigen Aufwärtstrend verfälscht zu werden.',
      side: 'top',
      align: 'center'
    },
    navigateAfter: { url: '/zentralbanken', step: 12 },
    optional: true
  },

  // ── Phase 5: Zentralbanken (Fed / EZB / BoE / BoJ) ──────────────────
  {
    page: '/zentralbanken',
    element: '#chart-event',
    popover: {
      title: 'Notenbank-Effekt',
      description: 'Wie verhält sich dein Ticker rund um FOMC-, EZB-, BoE- oder BoJ-Entscheide? Event-Window von t-N bis t+N mit historischen Returns und Streaks.',
      side: 'top',
      align: 'center'
    },
    navigateAfter: { url: '/feiertage', step: 13 },
    optional: true
  },

  // ── Phase 6: Feiertage ──────────────────────────────────────────────
  {
    page: '/feiertage',
    element: '#chart-ranking',
    popover: {
      title: 'Feiertags-Ranking',
      description: 'Welcher Feiertag hat historisch die besten Returns? Börsen-spezifisch (NYSE, XETRA, LSE) mit Ranking-Tabelle, Heatmap und Streak-Analyse.',
      side: 'top',
      align: 'center'
    },
    navigateAfter: { url: '/trifecta', step: 14 },
    optional: true
  },

  // ── Phase 7: Januar Trifecta ────────────────────────────────────────
  {
    page: '/trifecta',
    element: '#chart-curves',
    popover: {
      title: 'Januar Trifecta',
      description: 'Das klassische Ampelsystem: Santa Claus Rally + First Five Days + January Barometer. Wenn alle drei grün sind, ist das Jahr historisch fast immer bullish.',
      side: 'top',
      align: 'center'
    },
    navigateAfter: { url: '/spot-vol-beta', step: 15 },
    optional: true
  },

  // ── Phase 8: Spot-Vol Beta ──────────────────────────────────────────
  {
    page: '/spot-vol-beta',
    element: '#chart-scatter',
    popover: {
      title: 'Spot-Vol Beta (SPX vs. VIX)',
      description: 'Wie stark reagiert der VIX auf SPX-Bewegungen? Scatter + OLS-Regression + Regime-Wendepunkte (Spikes, Complacency, Beta Stress) mit Forward Returns 5/10/20/60d.',
      side: 'top',
      align: 'center'
    },
    navigateAfter: { url: '/plain-vanilla', step: 16 },
    optional: true
  },

  // ── Phase 9: Plain Vanilla Strategien ───────────────────────────────
  {
    page: '/plain-vanilla',
    element: '#chart-equity',
    popover: {
      title: 'Plain Vanilla Strategien',
      description: '24 klassische Strategien (Sell in May, KTI, UECS, TOM, …) mit Equity-Kurve, Stats, Signifikanztest und Stop-Loss / Trailing Stop. Offene Trades werden als "OFFEN" markiert.',
      side: 'top',
      align: 'center'
    },
    navigateAfter: { url: '/ki-saisonalitaet', step: 17 },
    optional: true
  },

  // ── Phase 10: KI-Saisonalität ───────────────────────────────────────
  {
    page: '/ki-saisonalitaet',
    element: '#score-value',
    popover: {
      title: 'KI Composite Score',
      description: 'Vier Sub-Scores à 0–2,5 → Gesamt 0–10. Rechts daneben: Radar-Chart. Darunter der Musterpfad — rekalibrierte Saisonalität aus den ähnlichsten historischen Jahren.',
      side: 'bottom',
      align: 'start'
    },
    navigateAfter: { url: '/backtest-engine', step: 18 },
    optional: true
  },

  // ── Phase 11: Backtest Engine ───────────────────────────────────────
  {
    page: '/backtest-engine',
    element: '#outlier-filter',
    popover: {
      title: 'Outlier Manager',
      description: 'Extreme Ausreißer (Crash-Jahre wie 2008 oder Blasen wie 1999) können saisonale Muster verzerren. Filter via IQR, Winsorize oder Isolation Forest — auswählbar auf Monatswechsel, Mondphasen, Jahreszyklus, TDoM und Backtest.',
      side: 'right',
      align: 'start'
    }
  },
  {
    page: '/backtest-engine',
    element: '#indicator-filters',
    popover: {
      title: 'Technische Filter',
      description: 'SMA, EMA, RSI, Bollinger Bands, MACD und LBR Toby Crabel als Vor-Filter — nur Trades bei erfüllter Bedingung. Look-ahead-bias-frei: der Filter wird auf dem Vortag geprüft, nicht am Entry-Tag.',
      side: 'right',
      align: 'start'
    }
  },
  {
    page: '/backtest-engine',
    element: '#sel-event',
    popover: {
      title: 'Event-Typ wählen',
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
    navigateAfter: { url: '/dashboard?tour=done', step: 22 },
    optional: true
  },

  // ── Phase 12: Abschluss ─────────────────────────────────────────────
  {
    page: '/dashboard',
    element: '.nav__logo',
    popover: {
      title: 'Das war\'s!',
      description: 'Erkunde die 20+ Pages über das Menü: Zyklen, Events, Strategien, Scanner, Blog. Die Tour ist jederzeit über den "Tour"-Button in der Navigation wieder startbar.',
      side: 'bottom',
      align: 'start'
    }
  }
];
