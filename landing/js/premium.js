/**
 * SA.premium — Tier-Check + Feature-Gating
 * ==========================================
 * Prüft den Abo-Tier des Users (free/premium) via Supabase RPC
 * und bietet Gate-Funktionen für Premium-Features.
 *
 * Nutzung auf Pages:
 *   <div data-premium="true"> ... </div>
 *   → Wird automatisch mit Blur-Overlay + Upgrade-CTA versehen wenn User free ist.
 *
 * Oder programmatisch:
 *   if (SA.premium.isPremium()) { ... }
 *   SA.premium.gate(element)          // Overlay auf Element
 *   SA.premium.gateAll()              // Alle [data-premium] gaten
 *
 * Tier wird 1× pro Session geladen und im sessionStorage gecached (5min TTL).
 */
;(function() {
  'use strict';

  var CACHE_KEY = 'sa_tier';
  var CACHE_TTL = 5 * 60 * 1000; // 5 Minuten

  var _tier = null;       // 'free' | 'premium'
  var _loaded = false;
  var _listeners = [];

  // ── CSS für Gate-Overlay (einmalig injiziert) ──────────────────
  var _cssInjected = false;
  function injectCSS() {
    if (_cssInjected) return;
    _cssInjected = true;
    var style = document.createElement('style');
    style.textContent =
      '.sa-premium-gate{position:relative;overflow:hidden}' +
      '.sa-premium-gate>*:not(.sa-gate-overlay){filter:blur(6px);pointer-events:none;user-select:none}' +
      '.sa-gate-overlay{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;' +
        'background:rgba(0,0,0,.65);backdrop-filter:blur(2px);z-index:50;border-radius:inherit;padding:1.5rem;text-align:center}' +
      '.sa-gate-overlay .sa-gate-icon{font-size:1.5rem;margin-bottom:.5rem;opacity:.8}' +
      '.sa-gate-overlay .sa-gate-title{font-family:var(--f-d,sans-serif);font-size:.9375rem;font-weight:700;color:var(--text,#fff);margin-bottom:.25rem}' +
      '.sa-gate-overlay .sa-gate-desc{font-size:.8125rem;color:var(--muted,#888);margin-bottom:.75rem;max-width:280px;line-height:1.5}' +
      '.sa-gate-overlay .sa-gate-btn{display:inline-flex;align-items:center;gap:.4rem;padding:.5rem 1.25rem;' +
        'background:var(--accent,#e8a820);color:#000;font-size:.8125rem;font-weight:600;border:none;border-radius:6px;' +
        'cursor:pointer;text-decoration:none;transition:opacity .15s}' +
      '.sa-gate-overlay .sa-gate-btn:hover{opacity:.85}';
    document.head.appendChild(style);
  }

  // ── Tier laden ─────────────────────────────────────────────────
  function loadTier(callback) {
    // 1) Cache prüfen
    try {
      var cached = sessionStorage.getItem(CACHE_KEY);
      if (cached) {
        var parsed = JSON.parse(cached);
        if (parsed.ts && Date.now() - parsed.ts < CACHE_TTL) {
          _tier = parsed.tier;
          _loaded = true;
          if (callback) callback(_tier);
          return;
        }
      }
    } catch (e) { /* ignore */ }

    // 2) Nicht eingeloggt → free
    if (!window.supabase || typeof window.supabase.auth === 'undefined') {
      setTier('free');
      if (callback) callback(_tier);
      return;
    }

    // Session prüfen
    window.supabase.auth.getSession().then(function(res) {
      var session = res && res.data && res.data.session;
      if (!session) {
        setTier('free');
        if (callback) callback(_tier);
        return;
      }

      // 3) RPC aufrufen
      window.supabase.rpc('get_my_tier').then(function(rpcRes) {
        var tier = (rpcRes && rpcRes.data) || 'free';
        setTier(tier);
        if (callback) callback(_tier);
      }).catch(function() {
        setTier('free');
        if (callback) callback(_tier);
      });
    }).catch(function() {
      setTier('free');
      if (callback) callback(_tier);
    });
  }

  function setTier(tier) {
    _tier = tier;
    _loaded = true;
    try {
      sessionStorage.setItem(CACHE_KEY, JSON.stringify({ tier: tier, ts: Date.now() }));
    } catch (e) { /* ignore */ }
    // Listeners benachrichtigen
    for (var i = 0; i < _listeners.length; i++) {
      try { _listeners[i](tier); } catch (e) { /* ignore */ }
    }
  }

  // ── Gate-Funktionen ────────────────────────────────────────────

  /**
   * Overlay auf ein Element legen (Blur + Upgrade-CTA)
   * @param {HTMLElement} el - Das zu gatende Element
   * @param {object} [opts] - { title, description }
   */
  function gate(el, opts) {
    if (!el || el.classList.contains('sa-premium-gate')) return;
    opts = opts || {};

    var _en = !!(SA.i18n && SA.i18n.isEN && SA.i18n.isEN());
    injectCSS();
    el.classList.add('sa-premium-gate');

    var overlay = document.createElement('div');
    overlay.className = 'sa-gate-overlay';
    overlay.innerHTML =
      '<div class="sa-gate-icon">' +
        '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color:var(--accent,#e8a820)">' +
          '<rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>' +
        '</svg>' +
      '</div>' +
      '<div class="sa-gate-title">' + (opts.title || (_en ? SA.i18n.t('prem.gate_title') : 'Premium-Feature')) + '</div>' +
      '<div class="sa-gate-desc">' + (opts.description || (_en ? SA.i18n.t('prem.gate_desc') : 'Dieses Feature ist Teil von SeasonAlpha Premium.')) + '</div>' +
      '<a class="sa-gate-btn" href="/pricing">' + (_en ? SA.i18n.t('prem.gate_btn') : 'Upgrade ansehen') + '</a>';

    el.appendChild(overlay);
  }

  /**
   * Alle [data-premium="true"] Elemente gaten (wenn User free ist)
   */
  function gateAll() {
    if (_tier === 'premium') return;

    var _en = !!(SA.i18n && SA.i18n.isEN && SA.i18n.isEN());
    var els = document.querySelectorAll('[data-premium="true"]');
    for (var i = 0; i < els.length; i++) {
      var el = els[i];
      gate(el, {
        title: el.getAttribute('data-premium-title') || (_en ? SA.i18n.t('prem.gate_title') : 'Premium-Feature'),
        description: el.getAttribute('data-premium-desc') || (_en ? SA.i18n.t('prem.gate_desc') : 'Dieses Feature ist Teil von SeasonAlpha Premium.')
      });
    }
  }

  /**
   * Gate entfernen (z.B. nach Upgrade)
   */
  function ungate(el) {
    if (!el) return;
    el.classList.remove('sa-premium-gate');
    var overlay = el.querySelector('.sa-gate-overlay');
    if (overlay) overlay.remove();
  }

  function ungateAll() {
    var els = document.querySelectorAll('.sa-premium-gate');
    for (var i = 0; i < els.length; i++) {
      ungate(els[i]);
    }
  }

  // ── Public API ─────────────────────────────────────────────────
  window.SA = window.SA || {};
  window.SA.premium = {
    /** Tier laden (async). Callback erhält 'free' oder 'premium' */
    load: loadTier,
    /** Tier synchron lesen (null wenn noch nicht geladen) */
    getTier: function() { return _tier; },
    /** Ist der User Premium? */
    isPremium: function() { return _tier === 'premium'; },
    /** Ist der User Free? */
    isFree: function() { return _tier !== 'premium'; },
    /** Listener für Tier-Änderungen */
    onTierChange: function(fn) { _listeners.push(fn); },
    /** Element gaten */
    gate: gate,
    /** Alle [data-premium] gaten */
    gateAll: gateAll,
    /** Gate entfernen */
    ungate: ungate,
    ungateAll: ungateAll,
    /** Tier manuell setzen (für Tests: SA.premium.setTier('premium')) */
    setTier: setTier
  };

  // Auto-Init: Tier laden + gateAll nach DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
      loadTier(function() { gateAll(); });
    });
  } else {
    loadTier(function() { gateAll(); });
  }
})();
