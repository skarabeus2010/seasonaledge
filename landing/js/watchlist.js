/**
 * landing/js/watchlist.js — SA.watchlist Storage + Events API
 *
 * Local-First Watchlist-Modul für SeasonAlpha. Speichert bis zu 50 Ticker
 * im localStorage, emittiert Events bei Änderungen (inkl. Cross-Tab-Sync
 * über storage-Event).
 *
 * Die Persistence-Schicht ist bewusst isoliert, damit sie später durch einen
 * Supabase-Backend ersetzt werden kann (wenn Feature #4 Auth kommt). Die
 * öffentliche API (`get`, `add`, `remove`, `toggle`, `has`, `count`, `on`,
 * `off`) bleibt beim Backend-Tausch identisch.
 *
 * Schema v1:
 *   {
 *     version: 1,
 *     created_at: ISO-String,
 *     updated_at: ISO-String,
 *     items: [ { ticker: "AAPL", added_at: ISO, note: "" }, ... ],
 *     sort: { key: "added_at", dir: "desc" }
 *   }
 *
 * Events (window.dispatchEvent):
 *   - sa-watchlist-changed       → immer wenn sich items ändern (add/remove/clear)
 *   - sa-watchlist-added         → nur bei add (detail: {ticker})
 *   - sa-watchlist-removed       → nur bei remove (detail: {ticker})
 *
 * Quick-Test in der DevTools-Console:
 *   SA.watchlist.add('AAPL')
 *   SA.watchlist.has('AAPL')      → true
 *   SA.watchlist.count()          → 1
 *   SA.watchlist.get()            → [{ticker: "AAPL", added_at: "...", note: ""}]
 *   SA.watchlist.toggle('AAPL')   → {removed: true, added: false}
 *   SA.watchlist.clear()
 */
(function() {
  window.SA = window.SA || {};

  var STORAGE_KEY = 'sa-watchlist-v1';
  var SCHEMA_VERSION = 1;
  var MAX_ITEMS = 50;

  var listeners = {
    'changed': [],
    'added': [],
    'removed': []
  };

  // ── Internal Storage Helpers ──────────────────────────────────
  function _initial() {
    var now = new Date().toISOString();
    return {
      version: SCHEMA_VERSION,
      created_at: now,
      updated_at: now,
      items: [],
      sort: { key: 'added_at', dir: 'desc' }
    };
  }

  function _read() {
    try {
      var raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return _initial();
      var data = JSON.parse(raw);
      // Schema-Validierung mit Fallback
      if (!data || typeof data !== 'object' || !Array.isArray(data.items)) {
        return _initial();
      }
      // Future Schema-Migration kann hier einhängen (version < SCHEMA_VERSION)
      return data;
    } catch (e) {
      return _initial();
    }
  }

  function _write(data) {
    try {
      data.updated_at = new Date().toISOString();
      localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
      return true;
    } catch (e) {
      // Quota exceeded oder Privacy-Mode
      console.warn('[SA.watchlist] localStorage write failed:', e);
      return false;
    }
  }

  function _normalize(ticker) {
    return (ticker || '').toString().trim().toUpperCase();
  }

  function _emit(event, detail) {
    // Internal subscribers
    var list = listeners[event];
    if (list) {
      for (var i = 0; i < list.length; i++) {
        try { list[i](detail || {}); }
        catch (e) { console.error('[SA.watchlist] listener error:', e); }
      }
    }
    // Window-Event (für Cross-Component Kommunikation)
    try {
      window.dispatchEvent(new CustomEvent('sa-watchlist-' + event, { detail: detail || {} }));
    } catch (e) { /* IE-Edge-Case */ }
  }

  // ── Public API ────────────────────────────────────────────────
  var api = {
    /**
     * Gibt alle Items als Array zurück (in der gespeicherten Reihenfolge).
     * Format: [{ticker, added_at, note}, ...]
     */
    get: function() {
      return _read().items.slice();  // Kopie, damit Consumer nicht mutieren kann
    },

    /**
     * Prüft ob ein Ticker in der Watchlist ist.
     */
    has: function(ticker) {
      var t = _normalize(ticker);
      if (!t) return false;
      var items = _read().items;
      for (var i = 0; i < items.length; i++) {
        if (items[i].ticker === t) return true;
      }
      return false;
    },

    /**
     * Anzahl Items.
     */
    count: function() {
      return _read().items.length;
    },

    /**
     * Fügt einen Ticker hinzu. Gibt true zurück wenn neu, false wenn bereits
     * vorhanden oder Limit erreicht.
     */
    add: function(ticker, opts) {
      var t = _normalize(ticker);
      if (!t) return false;

      var data = _read();
      // Duplikat-Check
      for (var i = 0; i < data.items.length; i++) {
        if (data.items[i].ticker === t) return false;
      }
      // Limit-Check
      if (data.items.length >= MAX_ITEMS) {
        console.warn('[SA.watchlist] MAX_ITEMS erreicht:', MAX_ITEMS);
        _emit('changed', { action: 'limit-reached', ticker: t, count: data.items.length });
        return false;
      }
      // Neuen Item einfügen
      data.items.push({
        ticker: t,
        added_at: new Date().toISOString(),
        note: (opts && opts.note) || ''
      });
      if (!_write(data)) return false;

      _emit('added', { ticker: t, count: data.items.length });
      _emit('changed', { action: 'add', ticker: t, count: data.items.length });
      return true;
    },

    /**
     * Entfernt einen Ticker. Gibt true zurück wenn entfernt, false wenn nicht
     * vorhanden.
     */
    remove: function(ticker) {
      var t = _normalize(ticker);
      if (!t) return false;

      var data = _read();
      var idx = -1;
      for (var i = 0; i < data.items.length; i++) {
        if (data.items[i].ticker === t) { idx = i; break; }
      }
      if (idx === -1) return false;

      data.items.splice(idx, 1);
      if (!_write(data)) return false;

      _emit('removed', { ticker: t, count: data.items.length });
      _emit('changed', { action: 'remove', ticker: t, count: data.items.length });
      return true;
    },

    /**
     * Toggle: Fügt hinzu wenn nicht da, entfernt wenn da.
     * Returns: { added: bool, removed: bool, count: int }
     */
    toggle: function(ticker) {
      if (this.has(ticker)) {
        var removed = this.remove(ticker);
        return { added: false, removed: removed, count: this.count() };
      } else {
        var added = this.add(ticker);
        return { added: added, removed: false, count: this.count() };
      }
    },

    /**
     * Leert die komplette Watchlist.
     */
    clear: function() {
      var data = _initial();
      if (!_write(data)) return false;
      _emit('changed', { action: 'clear', count: 0 });
      return true;
    },

    /**
     * Event-Subscription. Gültige Events: 'changed', 'added', 'removed'.
     * Der Handler bekommt ein detail-Objekt (siehe jeweilige Emitter).
     */
    on: function(event, handler) {
      if (!listeners[event] || typeof handler !== 'function') return;
      listeners[event].push(handler);
    },

    /**
     * Event-Unsubscription.
     */
    off: function(event, handler) {
      if (!listeners[event]) return;
      listeners[event] = listeners[event].filter(function(h) { return h !== handler; });
    },

    /**
     * Sort-Präferenz speichern (wird von watchlist.html genutzt).
     */
    setSort: function(key, dir) {
      var data = _read();
      data.sort = { key: key, dir: dir || 'desc' };
      _write(data);
    },

    getSort: function() {
      return _read().sort || { key: 'added_at', dir: 'desc' };
    },

    // ── Migration-API für späteren Auth-Upgrade (Phase 2) ────────
    _export: function() {
      return _read();
    },

    _import: function(data) {
      if (!data || !Array.isArray(data.items)) return false;
      var sanitized = _initial();
      sanitized.items = data.items.slice(0, MAX_ITEMS).map(function(item) {
        return {
          ticker: _normalize(item.ticker),
          added_at: item.added_at || new Date().toISOString(),
          note: item.note || ''
        };
      }).filter(function(item) { return !!item.ticker; });
      if (data.sort) sanitized.sort = data.sort;
      var ok = _write(sanitized);
      if (ok) _emit('changed', { action: 'import', count: sanitized.items.length });
      return ok;
    },

    _backend: 'localStorage',
    _maxItems: MAX_ITEMS,
    _schemaVersion: SCHEMA_VERSION
  };

  // Cross-Tab-Sync via storage-Event
  // Wenn ein anderer Tab die Watchlist ändert, re-emittieren wir 'changed'
  // damit die UI dieses Tabs sich aktualisiert.
  window.addEventListener('storage', function(e) {
    if (e.key === STORAGE_KEY && e.newValue !== e.oldValue) {
      var count = 0;
      try { count = (JSON.parse(e.newValue || '{}').items || []).length; } catch (_) {}
      _emit('changed', { action: 'cross-tab', count: count });
    }
  });

  SA.watchlist = api;
})();
