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

window.SA = SA;
