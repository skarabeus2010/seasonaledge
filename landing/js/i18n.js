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

  function _detectLang() {
    var path = window.location.pathname;
    if (path === '/en/' || path === '/en' || path.indexOf('/en/') === 0) {
      _isEN = true;
      _lang = 'en';
    }
    return _lang;
  }

  function _loadJSON(lang) {
    var cacheKey = 'sa-i18n-' + lang;
    try {
      var cached = sessionStorage.getItem(cacheKey);
      if (cached) return Promise.resolve(JSON.parse(cached));
    } catch (e) {}
    return fetch('/landing/i18n/' + lang + '.json')
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
      if (val !== key) el.textContent = val;
    });
  }

  // These link prefixes are NOT rewritten to /en/ — external or already handled separately
  var _skipPrefixes = ['/en/', '/blog/', '/tools/', '/rechtliches', '/disclaimer',
                       '/app/', '/umami/', 'http', 'mailto:', '#', 'javascript:'];

  function _applyNavLinks() {
    if (!_isEN) return;
    ['nav-container', 'footer-container'].forEach(function(cid) {
      var container = document.getElementById(cid);
      if (!container) return;
      container.querySelectorAll('a[href]').forEach(function(a) {
        var href = a.getAttribute('href');
        if (!href || href.charAt(0) !== '/') return;
        var skip = _skipPrefixes.some(function(p) { return href.indexOf(p) === 0; });
        if (!skip) a.setAttribute('href', '/en' + href);
      });
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
    switchTo: switchTo,
    _onComponentLoaded: _onComponentLoaded,
    _applyDOM: _applyDOM,
    _applyNavLinks: _applyNavLinks,
    _injectHreflang: _injectHreflang,
    _updateMeta: _updateMeta
  };
})();
