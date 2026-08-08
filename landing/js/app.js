/**
 * SeasonAlpha — App Framework (Vanilla JS)
 * =========================================
 * Gemeinsamer Code fuer alle Pages:
 * - Cache (localStorage mit TTL)
 * - Component-Loader (Nav + Footer)
 * - Supabase REST API Client (mit Cache)
 * - Burger-Menu Toggle
 * - Dropdown Hover/Click
 */

var SA = window.SA || (window.SA = {});

// ── Client-Side Cache ──────────────────────────────────────────────────────
// localStorage mit TTL. Spart Supabase-Fetches bei Page-Wechseln — essenziell
// für die Guided Tour und generelle Cross-Page-Navigation. Bei stale data
// (> TTL) wird neu gefetcht. Quota-full → purge + retry.

SA.cache = (function() {
  var PREFIX = 'sa-cache-';
  var DEFAULT_TTL_MS = 15 * 60 * 1000;  // 15 Minuten

  function keyOf(ns, k) { return PREFIX + ns + ':' + k; }

  function purgeAll() {
    try {
      for (var i = localStorage.length - 1; i >= 0; i--) {
        var kk = localStorage.key(i);
        if (kk && kk.indexOf(PREFIX) === 0) localStorage.removeItem(kk);
      }
    } catch (e) { /* ignore */ }
  }

  function get(ns, k) {
    try {
      var raw = localStorage.getItem(keyOf(ns, k));
      if (!raw) return null;
      var obj = JSON.parse(raw);
      var ttl = obj.ttl || DEFAULT_TTL_MS;
      if (Date.now() - obj.ts > ttl) {
        localStorage.removeItem(keyOf(ns, k));
        return null;
      }
      return obj.data;
    } catch (e) { return null; }
  }

  function set(ns, k, data, ttlMs) {
    try {
      localStorage.setItem(keyOf(ns, k), JSON.stringify({
        ts: Date.now(), ttl: ttlMs || DEFAULT_TTL_MS, data: data
      }));
      return true;
    } catch (e) {
      // Quota exceeded → purge sa-cache-* und retry einmal
      console.warn('[SA.cache] quota full, purging');
      purgeAll();
      try {
        localStorage.setItem(keyOf(ns, k), JSON.stringify({
          ts: Date.now(), ttl: ttlMs || DEFAULT_TTL_MS, data: data
        }));
        return true;
      } catch (e2) { return false; }
    }
  }

  function invalidate(ns) {
    try {
      var prefix = PREFIX + ns + ':';
      for (var i = localStorage.length - 1; i >= 0; i--) {
        var kk = localStorage.key(i);
        if (kk && kk.indexOf(prefix) === 0) localStorage.removeItem(kk);
      }
    } catch (e) { /* ignore */ }
  }

  return {
    get: get, set: set, invalidate: invalidate, purge: purgeAll,
    DEFAULT_TTL_MS: DEFAULT_TTL_MS
  };
})();

// ── Tour-Mode Detection (für Performance-Optimierungen) ────────────────────
// Wenn die URL `?tour=...` enthält, aktivieren wir einen Lite-Mode:
// Chart-Animations off (charts.js), evtl. weitere Optimierungen in Zukunft.
SA.TOUR_MODE = false;
try {
  SA.TOUR_MODE = /[?&]tour=/.test(location.search);
} catch (e) { /* ignore */ }

// ── Component Loader ────────────────────────────────────────────────────────

function loadComponent(containerId, url) {
  var el = document.getElementById(containerId);
  if (!el) return;
  fetch(url)
    .then(function(r) { return r.text(); })
    .then(function(html) {
      el.innerHTML = html;
      if (containerId === 'nav-container') initNav();
      if (SA.i18n && SA.i18n._onComponentLoaded) SA.i18n._onComponentLoaded(containerId);
    })
    .catch(function(e) { console.warn('Component load failed:', url, e); });
}

function loadAnalytics() {
  fetch('/landing/components/analytics.html')
    .then(function(r) { return r.text(); })
    .then(function(html) {
      var tmp = document.createElement('div');
      tmp.innerHTML = html.trim();
      var scripts = tmp.querySelectorAll('script');
      for (var i = 0; i < scripts.length; i++) {
        var s = document.createElement('script');
        if (scripts[i].src) { s.src = scripts[i].src; s.defer = true; }
        for (var j = 0; j < scripts[i].attributes.length; j++) {
          var a = scripts[i].attributes[j];
          if (a.name !== 'src') s.setAttribute(a.name, a.value);
        }
        if (!scripts[i].src && scripts[i].textContent) s.textContent = scripts[i].textContent;
        document.head.appendChild(s);
      }
    })
    .catch(function() { /* analytics optional */ });
}

document.addEventListener('DOMContentLoaded', function() {
  if (SA.i18n && SA.i18n.init) SA.i18n.init();
  loadComponent('nav-container', '/landing/components/nav.html');
  loadComponent('footer-container', '/landing/components/footer.html');
  initSidebarToggle();
  loadAnalytics();
  // Auth nach Nav-Load initialisieren (Nav-Elemente muessen im DOM sein)
  setTimeout(function() { if (SA.auth && SA.auth.init) SA.auth.init(); }, 300);
});


// ── Nav Events ──────────────────────────────────────────────────────────────

function initNav() {
  // Burger toggle
  var burger = document.getElementById('nav-burger');
  var links = document.getElementById('nav-links');
  if (burger && links) {
    burger.addEventListener('click', function() {
      links.classList.toggle('open');
    });
  }

  // Dropdown hover (desktop) + click (mobile)
  document.querySelectorAll('.nav__dd > button').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      var dd = btn.parentElement;
      var isOpen = dd.classList.contains('open');
      // Alle schliessen
      document.querySelectorAll('.nav__dd').forEach(function(d) { d.classList.remove('open'); });
      if (!isOpen) dd.classList.add('open');
    });
  });

  // Klick ausserhalb schliesst Dropdowns
  document.addEventListener('click', function(e) {
    if (!e.target.closest('.nav__dd')) {
      document.querySelectorAll('.nav__dd').forEach(function(d) { d.classList.remove('open'); });
    }
  });
}


// ── Sidebar Collapse Toggle ─────────────────────────────────────────────────
// Fuegt einen einklappbaren Sidebar-Toggle auf allen Pages mit <aside class="sidebar"> ein.
// - Wide (>=1280px): Push-Modus. Collapsed -> Grid schrumpft auf 0 1fr, Content expandiert.
// - Narrow (<1280px): Overlay-Modus. Sidebar slidet von links rein, Backdrop dahinter.
// - State via localStorage ('sa-sidebar-collapsed'), persistiert ueber Page-Wechsel.
// - Default-State: >=1280px sichtbar, <1280px versteckt (Breakpoint-basiert wenn kein LS-Wert).
function initSidebarToggle() {
  var sidebar = document.querySelector('.sidebar');
  if (!sidebar) return; // Dashboard & Co haben keine Sidebar -> kein Toggle

  var STORAGE_KEY = 'sa-sidebar-collapsed';
  var BREAKPOINT = 1280;

  // Initial-State bestimmen
  var stored = null;
  try { stored = localStorage.getItem(STORAGE_KEY); } catch (e) {}
  var initialCollapsed;
  if (stored === 'true') initialCollapsed = true;
  else if (stored === 'false') initialCollapsed = false;
  else initialCollapsed = window.innerWidth < BREAKPOINT;

  if (initialCollapsed) document.body.classList.add('sa-sidebar-collapsed');

  // Toggle-Button
  var _en = !!(SA.i18n && SA.i18n.isEN && SA.i18n.isEN());
  var btn = document.createElement('button');
  btn.className = 'sa-sb-toggle';
  btn.type = 'button';
  btn.setAttribute('aria-label', _en ? SA.i18n.t('app.sidebar_toggle_aria') : 'Sidebar ein- oder ausblenden');
  btn.setAttribute('title', _en ? SA.i18n.t('app.sidebar_toggle_title') : 'Sidebar ein-/ausblenden');
  document.body.appendChild(btn);

  // Backdrop (nur auf Narrow Screens via CSS sichtbar)
  var backdrop = document.createElement('div');
  backdrop.className = 'sa-sb-backdrop';
  backdrop.setAttribute('aria-hidden', 'true');
  document.body.appendChild(backdrop);

  function setCollapsed(collapsed) {
    document.body.classList.toggle('sa-sidebar-collapsed', collapsed);
    try { localStorage.setItem(STORAGE_KEY, String(collapsed)); } catch (e) {}
  }
  function toggle() {
    setCollapsed(!document.body.classList.contains('sa-sidebar-collapsed'));
  }

  btn.addEventListener('click', toggle);
  backdrop.addEventListener('click', function() {
    if (window.innerWidth < BREAKPOINT) setCollapsed(true);
  });
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && window.innerWidth < BREAKPOINT) {
      if (!document.body.classList.contains('sa-sidebar-collapsed')) setCollapsed(true);
    }
  });
}


// ── Supabase REST API Client ────────────────────────────────────────────────

var SA = window.SA || {};
SA.supabase = {
  url: window.__SA_SB_URL || '',
  key: window.__SA_SB_KEY || '',

  /**
   * GET Request an Supabase REST API.
   * @param {string} table - Tabellenname (z.B. 'prices')
   * @param {string} query - Query-String (z.B. 'ticker=eq.AAPL&date=gte.2020-01-01')
   * @returns {Promise<Array>}
   */
  get: function(table, query) {
    var url = this.url + '/rest/v1/' + table;
    if (query) url += '?' + query;
    return fetch(url, {
      headers: {
        'apikey': this.key,
        'Authorization': 'Bearer ' + this.key,
        'Content-Type': 'application/json'
      }
    }).then(function(r) { return r.json(); });
  },

  /**
   * GET mit Offset-Pagination. PostgREST cappt jede Antwort auf max_rows
   * (default 1000), unabhaengig vom limit-Query-Param. Dieser Helper
   * paginiert via offset=N bis keine weiteren Rows mehr kommen.
   *
   * Die base-Query MUSS ein deterministisches order enthalten, sonst
   * koennen Zeilen ueber Batches dupliziert/weggelassen werden.
   *
   * @param {string} table
   * @param {string} query - Base-Query ohne offset/limit (order empfohlen)
   * @param {number} pageSize - Rows pro Batch (<=1000 wegen Server-Limit)
   * @returns {Promise<Array>}
   */
  getAll: function(table, query, pageSize) {
    var self = this;
    var PAGE = Math.min(pageSize || 1000, 1000);
    var results = [];
    function fetchPage(offset) {
      var q = (query || '') + (query ? '&' : '') + 'offset=' + offset + '&limit=' + PAGE;
      return self.get(table, q).then(function(rows) {
        if (!Array.isArray(rows)) return results;
        results.push.apply(results, rows);
        if (rows.length < PAGE) return results;
        return fetchPage(offset + PAGE);
      });
    }
    return fetchPage(0);
  },

  /**
   * POST (Insert) an Supabase REST API.
   * @param {string} table - Tabellenname
   * @param {Object} data - Zu speichernde Daten
   * @returns {Promise}
   */
  post: function(table, data) {
    return fetch(this.url + '/rest/v1/' + table, {
      method: 'POST',
      headers: {
        'apikey': this.key,
        'Authorization': 'Bearer ' + this.key,
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
      },
      body: JSON.stringify(data)
    });
  }
};

// ── Ticker-Input (wiederverwendbar) ────────────────────────────────────────

/**
 * Initialisiert ein Ticker-Input mit Autocomplete (Datalist) + Focus-Select.
 *
 * Laedt tickers.json einmal (263 Ticker mit Namen), cached im SA-Objekt.
 * Bei Focus wird der Text markiert (sofort ueberschreibbar).
 * Bei Enter oder Datalist-Auswahl wird der Callback aufgerufen.
 *
 * @param {string} inputId    - ID des <input> Elements
 * @param {string} datalistId - ID des <datalist> Elements
 * @param {function} onSelect - Callback(ticker) bei Auswahl
 *
 * Beispiel:
 *   <input type="text" id="ticker-input" value="^DJI" list="ticker-list">
 *   <datalist id="ticker-list"></datalist>
 *   SA.initTickerInput('ticker-input', 'ticker-list', function(ticker) {
 *     loadTicker(ticker);
 *   });
 */
SA._tickerCache = null;

// Custom-Substring-Autocomplete (ersetzt das native <datalist>, das je nach
// Browser nur Prefix matcht / Optionen kappt). Matcht Ticker UND Name,
// case-insensitiv, Prefix-Treffer zuerst. Signatur bleibt kompatibel.
SA.initTickerInput = function(inputId, datalistId, onSelect) {
  var input = document.getElementById(inputId);
  if (!input) return;
  input.removeAttribute('list');            // natives datalist deaktivieren
  input.setAttribute('autocomplete', 'off');

  function commit(val) {
    if (onSelect) onSelect(String(val == null ? input.value : val).trim().toUpperCase());
  }

  input.addEventListener('focus', function() { this.select(); });

  var box = document.createElement('div');
  box.className = 'sa-ac-box';
  box.style.cssText = 'position:absolute;z-index:99999;display:none;max-height:320px;'
    + 'overflow-y:auto;background:#0a0a0e;border:1px solid #2a2a35;border-radius:8px;'
    + 'margin-top:2px;box-shadow:0 8px 24px rgba(0,0,0,.5);'
    + 'font-family:var(--f-m,ui-monospace,monospace);';
  document.body.appendChild(box);
  var matches = [], active = -1;

  function place() {
    var r = input.getBoundingClientRect();
    box.style.left = (window.scrollX + r.left) + 'px';
    box.style.top = (window.scrollY + r.bottom) + 'px';
    box.style.width = Math.max(r.width, 220) + 'px';
  }
  function hide() { box.style.display = 'none'; active = -1; }
  function render() {
    if (!matches.length) { hide(); return; }
    var html = '';
    for (var i = 0; i < matches.length; i++) {
      var m = matches[i];
      html += '<div class="sa-ac-row" data-idx="' + i + '" style="padding:7px 10px;'
        + 'cursor:pointer;font-size:12px;white-space:nowrap;overflow:hidden;'
        + 'text-overflow:ellipsis;border-bottom:1px solid #15151c;'
        + (i === active ? 'background:#1a1a23;' : '') + '">'
        + '<b style="color:#e8a820">' + m.t + '</b> '
        + '<span style="color:#9ca3af">' + (m.n || '') + '</span></div>';
    }
    box.innerHTML = html;
    place();
    box.style.display = 'block';
  }
  function pick(i) {
    var m = matches[i];
    if (!m) return;
    input.value = m.t;
    hide();
    commit(m.t);
  }
  function filter() {
    var q = input.value.trim().toUpperCase();
    var data = SA._tickerCache || [];
    if (!q) { matches = []; hide(); return; }
    var pre = [], sub = [];
    for (var i = 0; i < data.length; i++) {
      var t = (data[i].t || '').toUpperCase();
      var n = (data[i].n || '').toUpperCase();
      if (t.indexOf(q) === 0) pre.push(data[i]);
      else if (t.indexOf(q) > 0 || n.indexOf(q) >= 0) sub.push(data[i]);
    }
    matches = pre.concat(sub).slice(0, 60);
    active = matches.length ? 0 : -1;
    render();
  }

  input.addEventListener('input', filter);
  input.addEventListener('keydown', function(e) {
    var open = box.style.display === 'block' && matches.length;
    if (open && e.key === 'ArrowDown') { e.preventDefault(); active = (active + 1) % matches.length; render(); }
    else if (open && e.key === 'ArrowUp') { e.preventDefault(); active = (active - 1 + matches.length) % matches.length; render(); }
    else if (e.key === 'Enter') { e.preventDefault(); if (open && active >= 0) pick(active); else { hide(); commit(); } }
    else if (e.key === 'Escape') { hide(); }
  });
  box.addEventListener('mousedown', function(e) {
    var row = e.target.closest ? e.target.closest('.sa-ac-row') : null;
    if (row) { e.preventDefault(); pick(parseInt(row.getAttribute('data-idx'), 10)); }
  });
  input.addEventListener('blur', function() { setTimeout(hide, 150); });
  window.addEventListener('scroll', function() { if (box.style.display === 'block') place(); }, true);
  window.addEventListener('resize', function() { if (box.style.display === 'block') place(); });

  // Ticker-Liste laden (einmal, dann gecached)
  if (SA._tickerCache) return;
  fetch('/landing/data/tickers.json')
    .then(function(r) { return r.json(); })
    .then(function(tickers) { SA._tickerCache = tickers; })
    .catch(function() {});
};

/**
 * Laedt alle Preise eines Tickers aus Supabase (paginiert, 1000er Batches).
 * @param {string} ticker
 * @returns {Promise<Array>} [{date, close, log_return, tdom, tdoy}, ...]
 */
/**
 * @param {string} ticker
 * @param {string} extraFilter - optionaler Supabase-Filter (z.B. "&date=gte.2000-01-01")
 */
SA.fetchAllPrices = function(ticker, extraFilter) {
  // Cache-first: 15-min TTL reicht — Nightly Refresh aktualisiert Preisdaten
  // ohnehin nur 1x täglich. Bei Tour-Mode oder Page-Navigation: instant Hit.
  var cacheKey = ticker + '|' + (extraFilter || '');
  if (SA.cache) {
    var cached = SA.cache.get('prices', cacheKey);
    if (cached) return Promise.resolve(cached);
  }

  var allRows = [];
  var batchSize = 1000;
  function fetchBatch(offset, attempt) {
    attempt = attempt || 0;
    var q = 'ticker=eq.' + encodeURIComponent(ticker) + '&select=date,close,log_return,tdom,tdoy&order=date' + (extraFilter || '');
    return fetch(SA.supabase.url + '/rest/v1/prices?' + q, {
      headers: {
        'apikey': SA.supabase.key,
        'Authorization': 'Bearer ' + SA.supabase.key,
        'Range': offset + '-' + (offset + batchSize - 1),
        'Prefer': 'count=exact'
      }
    }).then(function(r) {
      // Rate-Limit (429) / Serverfehler (5xx) → Retry mit Backoff. Seiten wie die
      // Watchlist feuern viele parallele Batch-Requests; einzelne koennen gedrosselt
      // werden. Ohne Retry landete frueher ein Fehler-JSON als "Zeilen" im Ergebnis.
      if (!r.ok) {
        if ((r.status === 429 || r.status >= 500) && attempt < 4) {
          return new Promise(function(res) { setTimeout(res, 350 * (attempt + 1)); })
            .then(function() { return fetchBatch(offset, attempt + 1); });
        }
        throw new Error('prices ' + r.status + ' (' + ticker + ')');
      }
      var contentRange = r.headers.get('content-range');
      return r.json().then(function(rows) {
        // Fehler-JSON (kein Array) NIEMALS als Zeilen anhaengen — sonst kommt ein
        // kurzes/kaputtes Ergebnis raus und das UI zeigt faelschlich "Zu wenig Daten".
        if (!Array.isArray(rows)) throw new Error('prices non-array (' + ticker + ')');
        allRows = allRows.concat(rows);
        if (contentRange) {
          var parts = contentRange.split('/');
          var total = parseInt(parts[1]);
          if (allRows.length < total) return fetchBatch(allRows.length);
        } else if (rows.length === batchSize) {
          return fetchBatch(allRows.length);
        }
        return allRows;
      });
    });
  }
  return fetchBatch(0).then(function(rows) {
    if (SA.cache && rows && rows.length) SA.cache.set('prices', cacheKey, rows);
    return rows;
  });
};

// ── Trading Day Header (wiederverwendbar) ──────────────────────────────────

/**
 * Rendert den gelben Trading-Day-Header.
 *
 * Format: Heute: Mo 07.04.2026 · ^GSPC · TDOM 4/21 · TWOY 15/53 · TDOY 65/252 · Q2 · MidTerm
 *
 * Berechnet TDOM/TDOY/TWOY frisch vom Monats-/Jahresanfang und nutzt
 * SA.holidays.isTradingDay() um boersenspezifische Feiertage zu beruecksichtigen.
 *
 * @param {string|HTMLElement} elementOrId - ID des Header-Containers ODER das Element selbst
 * @param {string} ticker - Aktueller Ticker
 * @param {Array} [rows] - optional, fallback fuer Nicht-Handelstage
 */
SA.renderTradingDayHeader = function(elementOrId, ticker, rows) {
  var el = (typeof elementOrId === 'string')
    ? document.getElementById(elementOrId)
    : elementOrId;
  if (!el) return;

  var isEN = window.location.pathname.indexOf('/en/') === 0 || window.location.pathname === '/en';
  var weekdays = isEN
    ? ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    : ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
  var pad = function(n) { return n < 10 ? '0' + n : '' + n; };
  var today = new Date();
  var weekday = weekdays[today.getDay()];
  var dateStr = isEN
    ? today.toLocaleDateString('en-US', { month: '2-digit', day: '2-digit', year: 'numeric' })
    : today.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
  var todayStr = today.getFullYear() + '-' + pad(today.getMonth() + 1) + '-' + pad(today.getDate());

  // Boerse via Ticker-Mapping
  var exchange = (window.SA && SA.holidays) ? SA.holidays.detect(ticker || '') : 'NYSE';
  var isTD = function(ds) {
    if (window.SA && SA.holidays) return SA.holidays.isTradingDay(ds, exchange);
    var d = new Date(ds.substring(0,4) + '/' + ds.substring(5,7) + '/' + ds.substring(8,10));
    var dow = d.getDay();
    return dow >= 1 && dow <= 5;
  };

  // TDOM (current/total) — iteriere durch den aktuellen Monat
  var tdomCount = 0, tdomTotal = 0;
  var d1 = new Date(today.getFullYear(), today.getMonth(), 1);
  while (d1.getMonth() === today.getMonth()) {
    var ds1 = d1.getFullYear() + '-' + pad(d1.getMonth()+1) + '-' + pad(d1.getDate());
    if (isTD(ds1)) {
      tdomTotal++;
      if (ds1 <= todayStr) tdomCount++;
    }
    d1.setDate(d1.getDate() + 1);
  }

  // TDOY (current/total) — iteriere durch das aktuelle Jahr
  var tdoyCount = 0, tdoyTotal = 0;
  var d2 = new Date(today.getFullYear(), 0, 1);
  while (d2.getFullYear() === today.getFullYear()) {
    var ds2 = d2.getFullYear() + '-' + pad(d2.getMonth()+1) + '-' + pad(d2.getDate());
    if (isTD(ds2)) {
      tdoyTotal++;
      if (ds2 <= todayStr) tdoyCount++;
    }
    d2.setDate(d2.getDate() + 1);
  }

  // Fallback: wenn heute kein HT und rows mit tdom/tdoy vorhanden, nutze die
  if (!isTD(todayStr) && rows && rows.length > 0) {
    var last = rows[rows.length - 1];
    if (last.tdom != null) tdomCount = parseInt(last.tdom);
    if (last.tdoy != null) tdoyCount = parseInt(last.tdoy);
  }

  // TWOY (ISO-Wochenzahl, current/total)
  var isoWeek = function(date) {
    var d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
    var dayNum = d.getUTCDay() || 7;
    d.setUTCDate(d.getUTCDate() + 4 - dayNum);
    var yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil((((d - yearStart)/86400000) + 1)/7);
  };
  var twoyCount = isoWeek(today);
  var twoyTotal = isoWeek(new Date(today.getFullYear(), 11, 28)); // 28. Dez liegt immer in der letzten ISO-Woche

  // Quartal
  var quarter = Math.floor(today.getMonth()/3) + 1;

  // Cycle Year: 1=Election (Wahljahr), 2=Post-Election, 3=MidTerm, 4=Pre-Election
  // Formel: ((year - 2020) % 4 + 4) % 4 + 1, da 2020 = Election Year (Trump)
  var cycle = ((today.getFullYear() - 2020) % 4 + 4) % 4 + 1;
  var cycleNames = { 1: 'Election', 2: 'Post-Election', 3: 'MidTerm', 4: 'Pre-Election' };

  // Header-Zeile zusammenbauen — neue Reihenfolge: TDOM · TWOY · TDOY · Q · Cycle
  el.textContent = (isEN ? 'Today: ' : 'Heute: ') + weekday + ' ' + dateStr + ' \u00B7 ' + (ticker || '') +
    ' \u00B7 TDOM ' + tdomCount + '/' + tdomTotal +
    ' \u00B7 TWOY ' + twoyCount + '/' + twoyTotal +
    ' \u00B7 TDOY ' + tdoyCount + '/' + tdoyTotal +
    ' \u00B7 Q' + quarter +
    ' \u00B7 ' + cycleNames[cycle];
};

// ── Sortable Tables (wiederverwendbar) ──────────────────────────────────────

/**
 * Macht eine Tabelle sortierbar durch Klick auf <th>.
 * - Erkennt Zahlen automatisch (inkl. %, $, Komma, -)
 * - Click toggelt asc/desc, Pfeil wird angehaengt
 * - Idempotent: doppelter Aufruf bricht nicht
 *
 * @param {HTMLElement|string} tableOrId - <table> Element oder dessen ID
 */
SA.makeSortable = function(tableOrId) {
  var table = typeof tableOrId === 'string' ? document.getElementById(tableOrId) : tableOrId;
  if (!table || table.dataset.sortableInit === '1') return;

  // Header-Zellen finden: entweder <thead th> oder erste Zeile mit <th>
  var ths = table.querySelectorAll('thead th');
  var headerRow = null;
  if (!ths.length) {
    var firstRow = table.querySelector('tr');
    if (firstRow && firstRow.querySelector('th')) {
      ths = firstRow.querySelectorAll('th');
      headerRow = firstRow;
    }
  }
  if (!ths.length) return;
  table.dataset.sortableInit = '1';

  var parseCell = function(txt) {
    if (txt == null) return '';
    txt = String(txt).replace(/[\u25B2\u25BC\u26A0]/g, '').trim();
    if (!txt || txt === '\u2013' || txt === '-' || txt === '\u2014') return null;
    // Datum YYYY-MM-DD
    if (/^\d{4}-\d{2}-\d{2}$/.test(txt)) return txt; // lexikografisch = chronologisch
    // Zahl aus String extrahieren
    var m = txt.match(/-?[\d.,]+/);
    if (m) {
      var s = m[0];
      // Heuristik: wenn ein Komma und danach 1-3 Ziffern → deutsche Zahl
      var n;
      if (/,\d{1,3}$/.test(s) && !/\.\d/.test(s)) {
        n = parseFloat(s.replace(/\./g, '').replace(',', '.'));
      } else {
        n = parseFloat(s.replace(/,/g, ''));
      }
      if (!isNaN(n)) return n;
    }
    return txt.toLowerCase();
  };

  var state = { col: -1, dir: 'asc' };

  // Sortierbare Rows bestimmen: alles in tbody, oder alle tr's ausser headerRow
  var getRows = function() {
    var tbody = table.querySelector('tbody');
    if (tbody) return Array.prototype.slice.call(tbody.querySelectorAll(':scope > tr'));
    // Keine tbody: alle tr's direkt im table (ausser Header)
    var all = Array.prototype.slice.call(table.querySelectorAll(':scope > tr'));
    return all.filter(function(r) { return r !== headerRow; });
  };

  // Container (tbody oder table) fuer appendChild
  var getContainer = function() {
    return table.querySelector('tbody') || table;
  };

  ths.forEach(function(th, idx) {
    th.style.cursor = 'pointer';
    th.style.userSelect = 'none';
    if (!th.title) { var _en2 = !!(SA.i18n && SA.i18n.isEN && SA.i18n.isEN()); th.title = _en2 ? SA.i18n.t('app.sort_click') : 'Klicken zum Sortieren'; }
    th.addEventListener('click', function() {
      if (state.col === idx) {
        state.dir = state.dir === 'asc' ? 'desc' : 'asc';
      } else {
        state.col = idx;
        state.dir = 'desc'; // Erstklick meist interessanter absteigend
      }

      ths.forEach(function(h) {
        h.innerHTML = h.innerHTML.replace(/\s*[\u25B2\u25BC]$/, '');
      });
      th.innerHTML = th.innerHTML + (state.dir === 'asc' ? ' \u25B2' : ' \u25BC');

      var rows = getRows();
      rows.sort(function(a, b) {
        var ca = a.cells[idx] ? parseCell(a.cells[idx].textContent) : null;
        var cb = b.cells[idx] ? parseCell(b.cells[idx].textContent) : null;
        if (ca == null && cb == null) return 0;
        if (ca == null) return 1;  // Null immer hinten
        if (cb == null) return -1;
        var na = typeof ca === 'number', nb = typeof cb === 'number';
        if (na && nb) return state.dir === 'asc' ? ca - cb : cb - ca;
        if (na) return state.dir === 'asc' ? -1 : 1;
        if (nb) return state.dir === 'asc' ? 1 : -1;
        return state.dir === 'asc' ? String(ca).localeCompare(cb) : String(cb).localeCompare(ca);
      });
      var container = getContainer();
      rows.forEach(function(r) { container.appendChild(r); });
    });
  });
};

/**
 * Auto-init: beobachtet DOM und macht jede neu eingefuegte <table> mit <thead>
 * automatisch sortierbar. Zero-Touch fuer alle Pages.
 *
 * Opt-out: <table data-no-sort="1"> wird ignoriert.
 */
SA._hasHeader = function(t) {
  if (t.querySelector('thead th')) return true;
  var firstRow = t.querySelector('tr');
  return !!(firstRow && firstRow.querySelector('th'));
};

SA._autoSortInit = function() {
  // Initialer Scan
  document.querySelectorAll('table').forEach(function(t) {
    if (SA._hasHeader(t) && !t.dataset.noSort) SA.makeSortable(t);
  });

  if (!window.MutationObserver) return;
  var obs = new MutationObserver(function(mutations) {
    for (var i = 0; i < mutations.length; i++) {
      var added = mutations[i].addedNodes;
      for (var j = 0; j < added.length; j++) {
        var n = added[j];
        if (n.nodeType !== 1) continue;
        if (n.tagName === 'TABLE' && SA._hasHeader(n) && !n.dataset.noSort) {
          SA.makeSortable(n);
        }
        if (n.querySelectorAll) {
          n.querySelectorAll('table').forEach(function(t) {
            if (SA._hasHeader(t) && !t.dataset.noSort) SA.makeSortable(t);
          });
        }
      }
    }
  });
  obs.observe(document.body, { childList: true, subtree: true });
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', SA._autoSortInit);
} else {
  SA._autoSortInit();
}

window.SA = SA;
