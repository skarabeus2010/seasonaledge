/**
 * SeasonAlpha — App Framework (Vanilla JS)
 * =========================================
 * Gemeinsamer Code fuer alle Pages:
 * - Component-Loader (Nav + Footer)
 * - Supabase REST API Client
 * - Burger-Menu Toggle
 * - Dropdown Hover/Click
 */

// ── Component Loader ────────────────────────────────────────────────────────

function loadComponent(containerId, url) {
  var el = document.getElementById(containerId);
  if (!el) return;
  fetch(url)
    .then(function(r) { return r.text(); })
    .then(function(html) {
      el.innerHTML = html;
      // Nav-Events nach dem Laden initialisieren
      if (containerId === 'nav-container') initNav();
    })
    .catch(function(e) { console.warn('Component load failed:', url, e); });
}

document.addEventListener('DOMContentLoaded', function() {
  loadComponent('nav-container', '/landing/components/nav.html');
  loadComponent('footer-container', '/landing/components/footer.html');
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

SA.initTickerInput = function(inputId, datalistId, onSelect) {
  var input = document.getElementById(inputId);
  var dl = document.getElementById(datalistId);
  if (!input) return;

  // Focus → Text markieren (sofort ueberschreibbar)
  input.addEventListener('focus', function() { this.select(); });

  // Enter → Callback
  input.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (onSelect) onSelect(input.value.trim().toUpperCase());
    }
  });

  // Datalist-Auswahl → Callback
  input.addEventListener('change', function() {
    if (onSelect) onSelect(input.value.trim().toUpperCase());
  });

  // Ticker-Liste laden (einmal, dann gecached)
  if (!dl) return;
  if (SA._tickerCache) {
    _populateDatalist(dl, SA._tickerCache);
    return;
  }
  fetch('/landing/data/tickers.json')
    .then(function(r) { return r.json(); })
    .then(function(tickers) {
      SA._tickerCache = tickers;
      _populateDatalist(dl, tickers);
    })
    .catch(function() {});
};

function _populateDatalist(dl, tickers) {
  if (dl.children.length > 0) return; // bereits gefuellt
  for (var i = 0; i < tickers.length; i++) {
    var opt = document.createElement('option');
    opt.value = tickers[i].t;
    opt.textContent = tickers[i].n + ' (' + tickers[i].t + ')';
    dl.appendChild(opt);
  }
}

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
  var allRows = [];
  var batchSize = 1000;
  function fetchBatch(offset) {
    var q = 'ticker=eq.' + encodeURIComponent(ticker) + '&select=date,close,log_return,tdom,tdoy&order=date' + (extraFilter || '');
    return fetch(SA.supabase.url + '/rest/v1/prices?' + q, {
      headers: {
        'apikey': SA.supabase.key,
        'Authorization': 'Bearer ' + SA.supabase.key,
        'Range': offset + '-' + (offset + batchSize - 1),
        'Prefer': 'count=exact'
      }
    }).then(function(r) {
      var contentRange = r.headers.get('content-range');
      return r.json().then(function(rows) {
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
  return fetchBatch(0);
};

window.SA = SA;
