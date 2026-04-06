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

// ── Trading Day Header (wiederverwendbar) ──────────────────────────────────

/**
 * Rendert den gelben Trading-Day-Header mit TDOM + TDOY.
 * Liest TDOM/TDOY aus den Supabase-Rows (letzte Zeile).
 *
 * @param {string} elementId - ID des Header-Containers
 * @param {string} ticker - Aktueller Ticker
 * @param {Array} rows - [{date, close, tdom, tdoy}] (optional, fuer TDOM/TDOY)
 */
SA.renderTradingDayHeader = function(elementId, ticker, rows) {
  var el = document.getElementById(elementId);
  if (!el) return;

  var today = new Date();
  var weekdays = ['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'];
  var weekday = weekdays[today.getDay()];
  var dateStr = today.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });
  var pad = function(n) { return n < 10 ? '0' + n : '' + n; };
  var todayStr = today.getFullYear() + '-' + pad(today.getMonth() + 1) + '-' + pad(today.getDate());

  var tdomStr = '\u2013';
  var tdoyStr = '\u2013';

  var exchange = (window.SA && SA.holidays) ? SA.holidays.detect(ticker) : 'NYSE';
  var isTD = function(ds) {
    if (window.SA && SA.holidays) return SA.holidays.isTradingDay(ds, exchange);
    var d = new Date(ds.substring(0,4) + '/' + ds.substring(5,7) + '/' + ds.substring(8,10));
    var dow = d.getDay();
    return dow >= 1 && dow <= 5;
  };

  if (isTD(todayStr)) {
    // Heute ist ein Handelstag → TDoM/TDoY frisch berechnen vom Monats-/Jahresanfang
    var tdomCount = 0;
    var d1 = new Date(today.getFullYear(), today.getMonth(), 1);
    while (true) {
      var ds1 = d1.getFullYear() + '-' + pad(d1.getMonth()+1) + '-' + pad(d1.getDate());
      if (ds1 > todayStr) break;
      if (isTD(ds1)) tdomCount++;
      d1.setDate(d1.getDate() + 1);
    }
    var tdoyCount = 0;
    var d2 = new Date(today.getFullYear(), 0, 1);
    while (true) {
      var ds2 = d2.getFullYear() + '-' + pad(d2.getMonth()+1) + '-' + pad(d2.getDate());
      if (ds2 > todayStr) break;
      if (isTD(ds2)) tdoyCount++;
      d2.setDate(d2.getDate() + 1);
    }
    tdomStr = String(tdomCount);
    tdoyStr = String(tdoyCount);
  } else if (rows && rows.length > 0) {
    // Heute kein HT → letzten DB-Wert nehmen
    var last = rows[rows.length - 1];
    if (last.tdom != null) tdomStr = String(parseInt(last.tdom));
    if (last.tdoy != null) tdoyStr = String(parseInt(last.tdoy));
  }

  el.textContent = 'Heute: ' + weekday + ' ' + dateStr + ' \u00B7 ' + ticker +
    ' \u00B7 TDOM ' + tdomStr + ' \u00B7 TDOY ' + tdoyStr;
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
  table.dataset.sortableInit = '1';

  var parseCell = function(txt) {
    if (txt == null) return '';
    txt = String(txt).replace(/[▲▼⚠]/g, '').trim();
    // Zahl aus String extrahieren: erlaubt "-", ".", "," → Float
    var m = txt.match(/-?[\d.,]+/);
    if (m) {
      var n = parseFloat(m[0].replace(/\./g, '').replace(',', '.'));
      if (!isNaN(n)) {
        // Wenn Punkte als Dezimal: zweiter Versuch
        var n2 = parseFloat(m[0].replace(/,/g, ''));
        return !isNaN(n2) && Math.abs(n2) >= Math.abs(n) * 0.99 ? n2 : n;
      }
    }
    return txt.toLowerCase();
  };

  var ths = table.querySelectorAll('thead th');
  var state = { col: -1, dir: 'asc' };

  ths.forEach(function(th, idx) {
    th.style.cursor = 'pointer';
    th.style.userSelect = 'none';
    th.addEventListener('click', function() {
      if (state.col === idx) {
        state.dir = state.dir === 'asc' ? 'desc' : 'asc';
      } else {
        state.col = idx;
        state.dir = 'asc';
      }

      // Pfeile entfernen und am aktiven Header setzen
      ths.forEach(function(h) {
        h.innerHTML = h.innerHTML.replace(/\s*[\u25B2\u25BC]$/, '');
      });
      th.innerHTML = th.innerHTML + (state.dir === 'asc' ? ' \u25B2' : ' \u25BC');

      var tbody = table.querySelector('tbody');
      if (!tbody) return;
      var rows = Array.prototype.slice.call(tbody.querySelectorAll('tr'));
      rows.sort(function(a, b) {
        var ca = a.cells[idx] ? parseCell(a.cells[idx].textContent) : '';
        var cb = b.cells[idx] ? parseCell(b.cells[idx].textContent) : '';
        var na = typeof ca === 'number', nb = typeof cb === 'number';
        if (na && nb) return state.dir === 'asc' ? ca - cb : cb - ca;
        if (na) return state.dir === 'asc' ? -1 : 1;
        if (nb) return state.dir === 'asc' ? 1 : -1;
        return state.dir === 'asc' ? String(ca).localeCompare(cb) : String(cb).localeCompare(ca);
      });
      rows.forEach(function(r) { tbody.appendChild(r); });
    });
  });
};

window.SA = SA;
