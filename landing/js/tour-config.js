/**
 * SeasonAlpha Guided Tour — Step-Definitionen
 *
 * 26 Schritte über 13 Pages. Multi-Page-Navigation via ?tour=step:N
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
  // ── Phase 1: Landing Page — Willkommen + Login ───────────────────────
  {
    page: '/',
    element: '.hero__content',
    popover: {
      title: 'Willkommen bei SeasonAlpha',
      description: 'Datengetriebene Börsenanalyse mit 131 Jahren saisonaler Marktdaten. In 26 Schritten zeigen wir dir die wichtigsten Features.',
      side: 'bottom',
      align: 'center'
    }
  },
  {
    page: '/',
    element: '#nav-login-btn',
    popover: {
      title: 'Anmelden mit Google',
      description: 'Optional: Mit Google-Login bekommst du eine <b>Cloud-Watchlist</b>, die zwischen deinen Geräten synchronisiert, und Zugriff auf dein persönliches Profil unter <b>/profile</b>. Ohne Login funktioniert alles auch — deine Watchlist bleibt dann nur lokal im Browser.',
      side: 'bottom',
      align: 'end'
    },
    navigateAfter: { url: '/scanner', step: 2 },
    optional: true
  },

  // ── Phase 2: Scanner ─────────────────────────────────────────────────
  {
    page: '/scanner',
    element: '#sel-search',
    popover: {
      title: 'Saisonal-Scanner — 269 Ticker',
      description: 'Der wöchentlich aktualisierte Scanner zeigt dir alle Ticker mit aktuellem <b>KI-Score</b>, Signal (Bullish/Neutral/Bearish), Win-Rate und Monatsrendite. Filtere nach Signal, Kategorie oder Mindest-Score — die Tabelle aktualisiert sich live.',
      side: 'right',
      align: 'start'
    },
    navigateAfter: { url: '/watchlist', step: 3 },
    optional: true
  },

  // ── Phase 3: Watchliste ──────────────────────────────────────────────
  {
    page: '/watchlist',
    element: '#wl-add-btn',
    popover: {
      title: 'Watchliste — deine Favoriten-Ticker',
      description: 'Ticker per <b>+</b> hinzufügen oder über den Stern auf jeder Analyse-Seite markieren. Jede Karte zeigt den aktuellen KI-Score, 2-Wochen-Saisonalität, Drawdown und das nächste Strategie-Signal. Eingeloggt: Cloud-Sync zwischen Geräten. Gast: rein lokal im Browser.',
      side: 'right',
      align: 'start'
    },
    navigateAfter: { url: '/dashboard', step: 4 },
    optional: true
  },

  // ── Phase 4: Dashboard ───────────────────────────────────────────────
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
    navigateAfter: { url: '/dekadenzyklus', step: 10 }
  },

  // ── Phase 5: Dekadenzyklus ───────────────────────────────────────────
  {
    page: '/dekadenzyklus',
    element: '#chart-lines',
    popover: {
      title: 'Dekadenzyklus — 131 Jahre DJI',
      description: 'Jede Dekade (z. B. 1930er, 1990er, 2020er) ist eine eigene Kohorte. Du siehst, wie sich "Jahre mit gleicher Endziffer" statistisch ähneln — ein fundamentaler Bias den viele Marktteilnehmer übersehen.',
      side: 'top',
      align: 'center'
    },
    navigateAfter: { url: '/jahreszyklus', step: 11 },
    optional: true
  },

  // ── Phase 6: Jahreszyklus ────────────────────────────────────────────
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
    navigateAfter: { url: '/zentralbanken', step: 14 },
    optional: true
  },

  // ── Phase 7: Zentralbanken (Fed / EZB / BoE / BoJ) ──────────────────
  {
    page: '/zentralbanken',
    element: '#chart-event',
    popover: {
      title: 'Notenbank-Effekt',
      description: 'Wie verhält sich dein Ticker rund um FOMC-, EZB-, BoE- oder BoJ-Entscheide? Event-Window von t-N bis t+N mit historischen Returns und Streaks.',
      side: 'top',
      align: 'center'
    },
    navigateAfter: { url: '/feiertage', step: 15 },
    optional: true
  },

  // ── Phase 8: Feiertage ──────────────────────────────────────────────
  {
    page: '/feiertage',
    element: '#chart-ranking',
    popover: {
      title: 'Feiertags-Ranking',
      description: 'Welcher Feiertag hat historisch die besten Returns? Börsen-spezifisch (NYSE, XETRA, LSE) mit Ranking-Tabelle, Heatmap und Streak-Analyse.',
      side: 'top',
      align: 'center'
    },
    navigateAfter: { url: '/trifecta', step: 16 },
    optional: true
  },

  // ── Phase 9: Januar Trifecta ────────────────────────────────────────
  {
    page: '/trifecta',
    element: '#chart-curves',
    popover: {
      title: 'Januar Trifecta',
      description: 'Das klassische Ampelsystem: Santa Claus Rally + First Five Days + January Barometer. Wenn alle drei grün sind, ist das Jahr historisch fast immer bullish.',
      side: 'top',
      align: 'center'
    },
    navigateAfter: { url: '/spot-vol-beta', step: 17 },
    optional: true
  },

  // ── Phase 10: Spot-Vol Beta ─────────────────────────────────────────
  {
    page: '/spot-vol-beta',
    element: '#chart-scatter',
    popover: {
      title: 'Spot-Vol Beta (SPX vs. VIX)',
      description: 'Wie stark reagiert der VIX auf SPX-Bewegungen? Scatter + OLS-Regression + Regime-Wendepunkte (Spikes, Complacency, Beta Stress) mit Forward Returns 5/10/20/60d.',
      side: 'top',
      align: 'center'
    },
    navigateAfter: { url: '/plain-vanilla', step: 18 },
    optional: true
  },

  // ── Phase 11: Plain Vanilla Strategien ──────────────────────────────
  {
    page: '/plain-vanilla',
    element: '#chart-equity',
    popover: {
      title: 'Plain Vanilla Strategien',
      description: '24 klassische Strategien (Sell in May, KTI, UECS, TOM, …) mit Equity-Kurve, Stats, Signifikanztest und Stop-Loss / Trailing Stop. Offene Trades werden als "OFFEN" markiert.',
      side: 'top',
      align: 'center'
    },
    navigateAfter: { url: '/ki-saisonalitaet', step: 19 },
    optional: true
  },

  // ── Phase 12: KI-Saisonalität ───────────────────────────────────────
  {
    page: '/ki-saisonalitaet',
    element: '#score-value',
    popover: {
      title: 'KI Composite Score',
      description: 'Vier Sub-Scores à 0–2,5 → Gesamt 0–10. Rechts daneben: Radar-Chart. Darunter der Musterpfad — rekalibrierte Saisonalität aus den ähnlichsten historischen Jahren.',
      side: 'bottom',
      align: 'start'
    },
    navigateAfter: { url: '/backtest-engine', step: 20 },
    optional: true
  },

  // ── Phase 13: Backtest Engine ───────────────────────────────────────
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
    navigateAfter: { url: '/dashboard?tour=done', step: 25 },
    optional: true
  },

  // ── Phase 14: Abschluss ─────────────────────────────────────────────
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

/**
 * English translations for SA.TOUR_STEPS popovers.
 * Index-aligned with SA.TOUR_STEPS — only title + description needed.
 * tour.js merges these when the URL starts with /en/.
 */
SA.TOUR_STEPS_EN = [
  // 0 — Landing: Welcome
  { title: 'Welcome to SeasonAlpha', description: 'Data-driven market analysis with 131 years of seasonal data. In 26 steps we\'ll show you the most important features.' },
  // 1 — Landing: Sign In
  { title: 'Sign In with Google', description: 'Optional: Google login gives you a <b>Cloud Watchlist</b> that syncs across your devices, plus access to your personal profile at <b>/profile</b>. Everything works without login too — your watchlist is then stored locally in the browser.' },
  // 2 — Scanner
  { title: 'Seasonal Scanner — 269 Tickers', description: 'The weekly-updated scanner shows all tickers with the current <b>AI Score</b>, signal (Bullish/Neutral/Bearish), win rate and monthly return. Filter by signal, category or minimum score — the table updates live.' },
  // 3 — Watchlist
  { title: 'Watchlist — Your Favourite Tickers', description: 'Add tickers via <b>+</b> or use the star icon on any analysis page. Each card shows the current AI Score, 2-week seasonality, drawdown and the next strategy signal. Logged in: cloud sync across devices. Guest: local browser storage only.' },
  // 4 — Dashboard: Ticker
  { title: 'Ticker Selection', description: 'Choose any ticker: SPY, AAPL, ^GSPC, BTC-USD, TSLA, ^DJI, … All cards update automatically.' },
  // 5 — Dashboard: Header
  { title: 'Where Are You in the Cycle?', description: 'The header shows all seasonal coordinates: <b>TDOM</b> = Trading Day of Month (e.g. 6/21), <b>TWOY</b> = Trading Week of Year, <b>TDOY</b> = Trading Day of Year, <b>Q</b> = Quarter, <b>MidTerm</b> = Presidential cycle phase (Election, Post-Election, Midterm, Pre-Election). Exchange-specific calculation (NYSE, XETRA, LSE).' },
  // 6 — Dashboard: AI Score
  { title: 'AI Score 0–10', description: 'Composite score from four sub-scores: pattern path quality, trend projection, win rate for the current month, and tracking quality. Bullish ≥ 6.5, bearish ≤ 3.5.' },
  // 7 — Dashboard: Crash
  { title: 'Crash Signal', description: 'Red = elevated risk according to Isolation Forest. The score 0–100 compares volatility, drawdown and returns against the 252-day percentile of the ticker.' },
  // 8 — Dashboard: Year chart
  { title: 'Seasonal Annual Chart', description: 'Historical average with 25th/75th percentile bands vs. the current year (gold). The "Today" marker shows your position in the annual cycle.' },
  // 9 — Dashboard: Events
  { title: 'Upcoming Events', description: 'FOMC meetings, OPEX, full moons and public holidays with historical returns and win rates over a t-3 to t+3 window.' },
  // 10 — Decade cycle
  { title: 'Decade Cycle — 131 Years DJI', description: 'Each decade (e.g. 1930s, 1990s, 2020s) is its own cohort. You can see how "years with the same final digit" statistically resemble each other — a fundamental bias that many market participants overlook.' },
  // 11 — Jahreszyklus: chart
  { title: 'Seasonal Annual Progression', description: 'Average of all years + confidence band + 25th/75th percentiles. Optionally: individual years below and the Gann Pressure Chart — synchronised via chart group.' },
  // 12 — Jahreszyklus: sidebar
  { title: 'Sidebar Controls', description: 'Ticker, period, smoothing, percentile bands, cycle overlays, outlier filter. Every change re-renders all charts live.' },
  // 13 — Jahreszyklus: detrend
  { title: 'Detrend Indicator', description: 'Removes the linear annual trend and shows pure seasonality on a 0–100 scale (midline 50). This lets you identify seasonal highs and lows without distortion from the long-term uptrend.' },
  // 14 — Zentralbanken
  { title: 'Central Bank Effect', description: 'How does your ticker behave around FOMC, ECB, BoE or BoJ decisions? Event window from t-N to t+N with historical returns and streaks.' },
  // 15 — Feiertage
  { title: 'Holiday Ranking', description: 'Which holiday has historically delivered the best returns? Exchange-specific (NYSE, XETRA, LSE) with ranking table, heatmap and streak analysis.' },
  // 16 — Trifecta
  { title: 'January Trifecta', description: 'The classic traffic-light system: Santa Claus Rally + First Five Days + January Barometer. When all three are green, the year has historically been almost always bullish.' },
  // 17 — Spot-Vol Beta
  { title: 'Spot-Vol Beta (SPX vs. VIX)', description: 'How strongly does VIX react to SPX moves? Scatter + OLS regression + regime turning points (spikes, complacency, beta stress) with forward returns 5/10/20/60d.' },
  // 18 — Plain Vanilla
  { title: 'Plain Vanilla Strategies', description: '24 classic strategies (Sell in May, KTI, UECS, TOM, …) with equity curve, stats, significance test and stop-loss / trailing stop. Open trades are marked as "OPEN".' },
  // 19 — KI-Saisonalität
  { title: 'AI Composite Score', description: 'Four sub-scores of 0–2.5 → total 0–10. Next to it: radar chart. Below: the pattern path — recalibrated seasonality from the most similar historical years.' },
  // 20 — Backtest: Outlier
  { title: 'Outlier Manager', description: 'Extreme outliers (crash years like 2008 or bubbles like 1999) can distort seasonal patterns. Filter via IQR, Winsorize or Isolation Forest — selectable for month-end, lunar phases, annual cycle, TDoM and backtest.' },
  // 21 — Backtest: Tech filter
  { title: 'Technical Filters', description: 'SMA, EMA, RSI, Bollinger Bands, MACD and LBR Toby Crabel as pre-filters — only trades when the condition is met. Look-ahead-bias-free: the filter is checked on the prior day, not on the entry day.' },
  // 22 — Backtest: Event type
  { title: 'Choose Event Type', description: 'FOMC meetings, OPEX, lunar phases, public holidays, month-start or Trifecta. The engine calculates entry/exit + KPIs fully automatically.' },
  // 23 — Backtest: Tabs
  { title: '4 Backtest Modes', description: 'Single backtest, parameter optimisation (grid search + heatmap), walk-forward (expanding window) and event relevance (t-test + Cohen\'s d).' },
  // 24 — Dashboard: Done
  { title: 'That\'s it!', description: 'Explore the 20+ pages via the menu: Cycles, Events, Strategies, Scanner, Blog. The tour can be restarted at any time via the "Tour" button in the navigation.' }
];
