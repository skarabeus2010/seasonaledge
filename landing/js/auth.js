/**
 * SA.auth — Supabase Auth Modul (Google OAuth)
 *
 * Nutzt @supabase/supabase-js v2 (CDN).
 * Stellt Login/Logout/Session-Management bereit.
 * Nav-Button wird automatisch aktualisiert.
 */
(function() {
  'use strict';
  var SA = window.SA || (window.SA = {});

  var _client = null;
  var _user = null;
  var _listeners = [];

  // ── Public API ──────────────────────────────────────────────────────────────

  SA.auth = {
    /** Aktueller User (null wenn nicht eingeloggt) */
    get user() { return _user; },

    /** Supabase Client Instanz */
    get client() { return _client; },

    /** Ist ein User eingeloggt? */
    get isLoggedIn() { return !!_user; },

    /** Supabase-Client (nach init) fuer RPC-Calls aus Pages. */
    get client() { return _client; },

    /** Initialisierung: Client erstellen, Session wiederherstellen */
    init: function() {
      if (_client) return; // bereits initialisiert
      if (typeof supabase === 'undefined' || !supabase.createClient) {
        console.warn('[auth] Supabase JS SDK nicht geladen');
        return;
      }
      var url = (SA.supabase && SA.supabase.url) || window.__SA_SB_URL || '';
      var key = (SA.supabase && SA.supabase.key) || window.__SA_SB_KEY || '';
      if (!url || !key) {
        console.warn('[auth] Supabase Credentials fehlen');
        return;
      }

      _client = supabase.createClient(url, key);

      // Session wiederherstellen
      _client.auth.getSession().then(function(result) {
        var session = result.data && result.data.session;
        _setUser(session ? session.user : null);
      });

      // Auth-State-Changes lauschen (Login, Logout, Token-Refresh)
      _client.auth.onAuthStateChange(function(event, session) {
        _setUser(session ? session.user : null);
      });
    },

    /** Google OAuth Login (Redirect-Flow) */
    login: function() {
      if (!_client) { console.warn('[auth] Nicht initialisiert'); return; }
      _client.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: window.location.origin + '/dashboard'
        }
      });
    },

    /** Logout */
    logout: function() {
      if (!_client) return;
      _client.auth.signOut().then(function() {
        _setUser(null);
      });
    },

    /** Callback bei Auth-Status-Aenderung */
    onAuthChange: function(cb) {
      if (typeof cb === 'function') _listeners.push(cb);
    },

    /** JWT Token fuer authentifizierte API-Calls */
    getToken: function() {
      if (!_client) return null;
      var session = null;
      // Synchroner Zugriff auf gecachte Session
      try {
        var stored = localStorage.getItem('sb-' + _extractProjectRef() + '-auth-token');
        if (stored) {
          var parsed = JSON.parse(stored);
          if (parsed && parsed.access_token) return parsed.access_token;
        }
      } catch(e) { /* ignore */ }
      return null;
    }
  };

  // ── Private Helpers ─────────────────────────────────────────────────────────

  function _setUser(user) {
    var wasLoggedIn = !!_user;
    _user = user;
    var isLoggedIn = !!_user;

    // Nav-UI aktualisieren
    _updateNavUI();

    // Listeners benachrichtigen
    if (wasLoggedIn !== isLoggedIn) {
      for (var i = 0; i < _listeners.length; i++) {
        try { _listeners[i](_user); } catch(e) { console.error('[auth] Listener error:', e); }
      }
    }
  }

  function _updateNavUI() {
    var loginBtn = document.getElementById('nav-login-btn');
    var userArea = document.getElementById('nav-user-area');
    if (!loginBtn || !userArea) return;

    if (_user) {
      loginBtn.style.display = 'none';
      userArea.style.display = 'flex';

      var avatar = userArea.querySelector('.nav__avatar');
      var name = userArea.querySelector('.nav__username');
      if (avatar && _user.user_metadata && _user.user_metadata.avatar_url) {
        avatar.src = _user.user_metadata.avatar_url;
        avatar.style.display = 'block';
      }
      if (name) {
        name.textContent = _user.user_metadata
          ? (_user.user_metadata.full_name || _user.email || '').split(' ')[0]
          : 'User';
      }
    } else {
      loginBtn.style.display = '';
      userArea.style.display = 'none';
    }
  }

  function _extractProjectRef() {
    var url = (SA.supabase && SA.supabase.url) || window.__SA_SB_URL || '';
    // https://xyz.supabase.co → xyz
    var match = url.match(/\/\/([^.]+)\./);
    return match ? match[1] : '';
  }

})();
