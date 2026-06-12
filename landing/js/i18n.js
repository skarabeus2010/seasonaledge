/**
 * SeasonAlpha — i18n (Internationalization)
 * ==========================================
 * Client-side i18n via URL detection (/en/ prefix).
 * DE is the default — no JSON needed for German.
 * EN: fetches /landing/i18n/en.json, applies [data-i18n] attributes.
 *
 * Usage:
 *   SA.i18n.init()         — called once in DOMContentLoaded
 *   SA.i18n.t(key)         — returns translated string or key as fallback
 *   SA.i18n.switchTo(lang) — navigates to /en/... or /.../
 */

var SA = window.SA || (window.SA = {});

SA.i18n = (function() {
  var _lang = 'de';
  var _data = {};
  var _isEN = false;

  // Paths that have no EN equivalent — never auto-redirect here
  var _noAutoRedirect = ['/blog/', '/tools/', '/rechtliches', '/disclaimer', '/app/', '/umami/'];

  function _detectLang() {
    var path = window.location.pathname;

    // Already on an EN URL
    if (path === '/en/' || path === '/en' || path.indexOf('/en/') === 0) {
      _isEN = true;
      _lang = 'en';
      try { localStorage.setItem('sa_lang', 'en'); } catch (e) {}
      return _lang;
    }

    // Explicit user preference stored from a previous visit or switchTo() call
    var stored;
    try { stored = localStorage.getItem('sa_lang'); } catch (e) {}
    if (stored === 'en') {
      var canRedirect = !_noAutoRedirect.some(function(p) { return path.indexOf(p) === 0; });
      if (canRedirect) {
        window.location.replace('/en' + (path === '/' ? '/' : path));
      }
      return 'en';
    }
    if (stored === 'de') return 'de';

    // First visit: detect browser language
    var browserLang = ((navigator.language || navigator.userLanguage) || '').toLowerCase();
    if (browserLang.indexOf('en') === 0) {
      var canAutoRedirect = !_noAutoRedirect.some(function(p) { return path.indexOf(p) === 0; });
      if (canAutoRedirect) {
        try { localStorage.setItem('sa_lang', 'en'); } catch (e) {}
        window.location.replace('/en' + (path === '/' ? '/' : path));
      }
      return 'en';
    }

    return _lang; // 'de'
  }

  // Bump this version whenever en.json gains new keys — busts sessionStorage cache
  var _JSON_VER = 'v3';

  function _loadJSON(lang) {
    var cacheKey = 'sa-i18n-' + _JSON_VER + '-' + lang;
    try {
      var cached = sessionStorage.getItem(cacheKey);
      if (cached) return Promise.resolve(JSON.parse(cached));
    } catch (e) {}
    return fetch('/landing/i18n/' + lang + '.json?v=' + _JSON_VER)
      .then(function(r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function(data) {
        try { sessionStorage.setItem(cacheKey, JSON.stringify(data)); } catch (e) {}
        return data;
      });
  }

  function t(key) {
    return (_data[key] !== undefined) ? _data[key] : key;
  }

  function _applyDOM() {
    document.querySelectorAll('[data-i18n]').forEach(function(el) {
      var key = el.getAttribute('data-i18n');
      var val = t(key);
      if (val === key) return;

      // Check if element has child elements (e.g. <input> inside <label>, <svg> inside <button>)
      var hasElementChild = false;
      for (var i = 0; i < el.childNodes.length; i++) {
        if (el.childNodes[i].nodeType === 1) { hasElementChild = true; break; }
      }

      if (!hasElementChild) {
        el.textContent = val;
      } else {
        // Mixed content (e.g. <label><input> Text</label>): update last text node only,
        // preserving leading whitespace so the visual gap after the checkbox remains.
        for (var j = el.childNodes.length - 1; j >= 0; j--) {
          if (el.childNodes[j].nodeType === 3) {
            var orig = el.childNodes[j].nodeValue;
            var lead = orig.match(/^\s+/);
            el.childNodes[j].nodeValue = (lead ? lead[0] : '') + val;
            break;
          }
        }
      }
    });
  }

  // These link prefixes are NOT rewritten to /en/ — external or already handled separately
  var _skipPrefixes = ['/en/', '/blog/', '/tools/', '/rechtliches', '/disclaimer',
                       '/app/', '/umami/', 'http', 'mailto:', '#', 'javascript:'];

  function _applyNavLinks() {
    if (!_isEN) return;
    document.querySelectorAll('a[href]').forEach(function(a) {
      var href = a.getAttribute('href');
      if (!href || href.charAt(0) !== '/') return;
      var skip = _skipPrefixes.some(function(p) { return href.indexOf(p) === 0; });
      if (!skip) a.setAttribute('href', '/en' + href);
    });
  }

  function _updateLangSwitch() {
    document.querySelectorAll('.nav__lang-btn').forEach(function(btn) {
      btn.classList.toggle('active', btn.getAttribute('data-lang') === _lang);
    });
  }

  function _injectHreflang() {
    if (!_isEN) return;
    var path = window.location.pathname;
    var dePath = path.replace(/^\/en/, '') || '/';

    document.querySelectorAll('link[hreflang]').forEach(function(l) { l.remove(); });

    function addLink(lang, href) {
      var link = document.createElement('link');
      link.rel = 'alternate';
      link.hreflang = lang;
      link.href = 'https://seasonalpha.ai' + href;
      document.head.appendChild(link);
    }
    addLink('de', dePath);
    addLink('en', path);
    addLink('x-default', dePath);
  }

  // EN page titles and meta descriptions, keyed by DE path (without /en prefix).
  // Maintains all 31 feature pages + home. Used by _updatePageTitle().
  var _EN_PAGE_META = {
    '/': {
      title: 'SeasonAlpha — Seasonal Stock Market Patterns with 131 Years of Data',
      desc:  'Analyse seasonal patterns for 270+ tickers: AI Score, Decade Cycle, Annual Cycle, OPEX, Moon Phases, Central Bank Effect and more. Free & Premium.'
    },
    '/dashboard': {
      title: 'Ticker Dashboard — Seasonality at a Glance | SeasonAlpha',
      desc:  'All seasonal signals for your ticker in one view: AI Score, Crash Signal, Annual Chart, TruePath pattern path, Strategies and Events.'
    },
    '/dekadenzyklus': {
      title: 'Decade Cycle — 131 Years of Dow Jones Patterns | SeasonAlpha',
      desc:  'Decade cycle analysis for stocks and indices: average path by final digit of the year, Anomaly Radar and pattern matching over 131 years of data.'
    },
    '/jahreszyklus': {
      title: 'Annual Cycle — Seasonal Market Patterns | SeasonAlpha',
      desc:  'Seasonal annual progression for 270+ tickers: monthly & quarterly performance, percentile bands, TruePath pattern matching and significance test.'
    },
    '/monatszyklus': {
      title: 'Monthly Cycle — Intra-Month Seasonality | SeasonAlpha',
      desc:  'Intra-month seasonality: average returns by calendar week, two-week split, monthly heatmap and statistical significance per ticker.'
    },
    '/wochentage': {
      title: 'Weekday Effect — Best Trading Day of the Week | SeasonAlpha',
      desc:  'Weekday performance analysis: average return, win rate and overnight/intraday split per weekday. Weekend effect and monthly breakdown.'
    },
    '/monatswechsel': {
      title: 'Turn-of-Month Effect — TOM Trading | SeasonAlpha',
      desc:  'Turn-of-Month effect: returns in the days before and after month-end. Seasonality, significance test and streak analysis per ticker.'
    },
    '/mondphasen': {
      title: 'Moon Phases & Markets — Full/New Moon Effect | SeasonAlpha',
      desc:  'Moon phase analysis for stocks and indices: average returns around full moon, new moon, first and last quarter. Heatmap and Super Moon effect.'
    },
    '/kriegszeiten': {
      title: 'War Times — Stock Markets in Conflict | SeasonAlpha',
      desc:  'How markets react to wars: event-window analysis, max drawdown after conflict start and annual returns during war years for major US conflicts.'
    },
    '/plain-vanilla': {
      title: 'Plain Vanilla Strategies — 24 Seasonal Trades | SeasonAlpha',
      desc:  '24 rule-based seasonal trading strategies with fixed entry and exit dates. CAGR, max drawdown, win rate and Sharpe ratio for each strategy.'
    },
    '/trifecta': {
      title: 'January Trifecta — SCR + FFD + JanB Signal | SeasonAlpha',
      desc:  'January Trifecta: three signals combined into a full-year forecast indicator. Historical win rate > 80% when all three signals are met.'
    },
    '/intermarket-shocks': {
      title: 'Intermarket Shocks — Trigger-Target Analysis | SeasonAlpha',
      desc:  'When Asset A drops or surges by X% — how does Asset B react? Event-window, scatter plot, seasonal breakdown and heatmap for any ticker pair.'
    },
    '/sektor-rotation': {
      title: 'Sector Rotation — 23 US Sector ETFs | SeasonAlpha',
      desc:  'Which US sectors historically perform best in which month? Seasonal heatmap, cumulative annual chart and win-rate matrix for 23 sector ETFs.'
    },
    '/overnight': {
      title: 'Overnight vs Intraday — Split Analysis | SeasonAlpha',
      desc:  'Where does performance come from — overnight (Close to Open) or intraday (Open to Close)? Monthly and weekday breakdown for any ticker.'
    },
    '/zentralbanken': {
      title: 'Central Bank Effect — Fed, ECB & Event-Trading | SeasonAlpha',
      desc:  'Market reaction around central bank meetings (Fed, ECB). Event-window analysis, hike vs. cut comparison and Polymarket Fed-path forecasts for 2026.'
    },
    '/feiertage': {
      title: 'Holiday Effect — Trading Around Exchange Holidays | SeasonAlpha',
      desc:  'Returns before and after stock exchange holidays: NYSE, XETRA and LSE specific. Holiday ranking, heatmap and next upcoming trading holidays.'
    },
    '/tdom-analyse': {
      title: 'TDoM Analysis — Trading Day of the Month | SeasonAlpha',
      desc:  'Average return, win rate and heatmap per trading day of the month. Exchange-specific (NYSE/XETRA/LSE) — analyses the true trading calendar, not calendar days.'
    },
    '/spot-vol-beta': {
      title: 'Spot-Vol Beta — SPX vs VIX Regression | SeasonAlpha',
      desc:  'Rolling OLS regression between spot returns and implied volatility changes. Measures how strongly volatility reacts to price movements per ticker.'
    },
    '/opex': {
      title: 'OPEX Analysis — Triple Witching & Monthly Expiry | SeasonAlpha',
      desc:  'Seasonal patterns around monthly options expiration (3rd Friday) and Triple Witching (Mar/Jun/Sep/Dec). Event-window, volatility and historical OPEX calendar.'
    },
    '/ki-saisonalitaet': {
      title: 'AI Seasonality — Composite Score & Pattern Path | SeasonAlpha',
      desc:  'AI Composite Score (0–10) combining four sub-scores: seasonality, drawdown, volatility and momentum. TruePath pattern matching with sigma cone projection.'
    },
    '/backtest-engine': {
      title: 'Backtest Engine — Event-Trading Optimisation | SeasonAlpha',
      desc:  'Test seasonal entry signals: OPEX, FOMC, Moon Phases, Holidays. Equity curve, trade table, metrics (CAGR, Sharpe, Max DD) and look-ahead-bias-free filtering.'
    },
    '/polymarket': {
      title: 'Polymarket Forecasts — Fed Cuts 2026 & Crypto | SeasonAlpha',
      desc:  'Prediction market probabilities alongside historical seasonality. Fed rate path, BTC/ETH targets and macro risk markets — Brier score calibration included.'
    },
    '/dividend-kalender': {
      title: 'Dividend Effect — Price Behaviour Around Ex-Date | SeasonAlpha',
      desc:  'How do stock prices move around ex-dividend dates? Event-window analysis, average return and max drawdown for dividend-paying stocks and ETFs.'
    },
    '/earnings-kalender': {
      title: 'Earnings Effect — Price Movement & Volatility | SeasonAlpha',
      desc:  'Market reaction around quarterly earnings releases: event-window, volatility spike, best and worst post-earnings reactions per ticker.'
    },
    '/risikozyklus': {
      title: 'Risk Cycle — Drawdown & Volatility | SeasonAlpha',
      desc:  'Seasonal risk analysis: drawdown heatmap, rolling volatility by month and quarter, percentile bands and historical worst drawdown periods.'
    },
    '/vixpiration': {
      title: 'VIXpiration — VIX Expiry Calendar & Analysis | SeasonAlpha',
      desc:  'Seasonal patterns around VIX settlement (30 days before OPEX Friday). Event-window, volatility reaction and exchange-holiday-adjusted calendar.'
    },
    '/scanner': {
      title: 'Seasonal Scanner — All Tickers by AI Score | SeasonAlpha',
      desc:  'All 270+ tickers sorted by AI Composite Score. Filter by category, signal, win rate and score range. Weekly updated seasonal edge overview.'
    },
    '/pricing': {
      title: 'Pricing — Free & Premium Plans | SeasonAlpha',
      desc:  'SeasonAlpha Free vs Premium: compare features, pricing and what unlocks with a Premium subscription. No credit card required to get started.'
    },
    '/profile': {
      title: 'My Profile — SeasonAlpha',
      desc:  'Manage your SeasonAlpha account: subscription status, watchlist, newsletter settings and daily briefing preferences.'
    },
    '/watchlist': {
      title: 'My Watchlist — AI Score & Signals | SeasonAlpha',
      desc:  'Your personal ticker watchlist with AI Composite Score, current regime signal and seasonal context. Up to 50 tickers, cloud-synced.'
    },
    '/unsubscribe': {
      title: 'Unsubscribe — SeasonAlpha',
      desc:  'Unsubscribe from the SeasonAlpha newsletter or daily morning briefing.'
    }
  };

  function _updatePageTitle() {
    if (!_isEN) return;
    var path = window.location.pathname.replace(/^\/en/, '') || '/';
    if (path !== '/' && path.slice(-1) === '/') path = path.slice(0, -1);
    var meta = _EN_PAGE_META[path];
    if (!meta) return;

    document.title = meta.title;

    var el;
    el = document.querySelector('meta[property="og:title"]');
    if (el) el.setAttribute('content', meta.title);
    el = document.querySelector('meta[name="twitter:title"]');
    if (el) el.setAttribute('content', meta.title);

    if (meta.desc) {
      el = document.querySelector('meta[name="description"]');
      if (el) el.setAttribute('content', meta.desc);
      el = document.querySelector('meta[property="og:description"]');
      if (el) el.setAttribute('content', meta.desc);
      el = document.querySelector('meta[name="twitter:description"]');
      if (el) el.setAttribute('content', meta.desc);
    }
  }

  function _updateMeta() {
    if (!_isEN) return;
    document.documentElement.lang = 'en';
    var ogLocale = document.querySelector('meta[property="og:locale"]');
    if (ogLocale) ogLocale.setAttribute('content', 'en_US');
    var canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) {
      var href = canonical.getAttribute('href') || '';
      if (href && href.indexOf('/en/') === -1 && href.indexOf('seasonalpha.ai') !== -1) {
        canonical.setAttribute('href', href.replace('https://seasonalpha.ai', 'https://seasonalpha.ai/en'));
      }
    }
    _updatePageTitle();
  }

  function _applyAll() {
    _applyDOM();
    _applyNavLinks();
    _updateLangSwitch();
    _updateMeta();
    _injectHreflang();
  }

  // Called from loadComponent() after nav or footer HTML is injected
  function _onComponentLoaded(containerId) {
    if (!_isEN) return;
    // If JSON is already loaded, apply immediately
    if (Object.keys(_data).length) {
      _applyDOM();
      _applyNavLinks();
      _updateLangSwitch();
    }
    // If JSON not yet loaded, _applyAll() will run when it arrives (see init())
  }

  function switchTo(lang) {
    var path = window.location.pathname;
    var newPath;
    if (lang === 'en') {
      if (path === '/en/' || path === '/en' || path.indexOf('/en/') === 0) return;
      newPath = '/en' + (path === '/' ? '/' : path);
    } else {
      newPath = path.replace(/^\/en/, '') || '/';
    }
    try { localStorage.setItem('sa_lang', lang); } catch (e) {}
    window.location.href = newPath;
  }

  function init() {
    _detectLang();
    if (!_isEN) {
      // Still update lang switch to mark DE as active
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', _updateLangSwitch);
      } else {
        _updateLangSwitch();
      }
      // Hook into component load to update lang switch in nav
      return;
    }
    _loadJSON('en')
      .then(function(data) {
        _data = data;
        _applyAll();
      })
      .catch(function(e) {
        console.warn('[SA.i18n] Failed to load en.json', e);
      });
  }

  return {
    init: init,
    t: t,
    isEN: function() { return _isEN; },
    switchTo: switchTo,
    _onComponentLoaded: _onComponentLoaded,
    _applyDOM: _applyDOM,
    _applyNavLinks: _applyNavLinks,
    _injectHreflang: _injectHreflang,
    _updateMeta: _updateMeta,
    _updatePageTitle: _updatePageTitle
  };
})();
