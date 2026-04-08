/**
 * SeasonAlpha Guided Tour — Driver.js Wrapper + Multi-Page Resume
 *
 * Laedt Driver.js v1.3.1 lazy vom CDN (nur bei Tour-Start), mapped die
 * SA.TOUR_STEPS Konfiguration auf Driver-Steps und unterstuetzt Page-Wechsel
 * via ?tour=step:N Query-Parameter.
 *
 * Nutzung:
 *   <script src="/landing/js/tour-config.js"></script>
 *   <script src="/landing/js/tour.js"></script>
 *   <button onclick="SA.tour.start(0)">Tour starten</button>
 *
 * Auto-Resume: Wenn eine Page mit ?tour=step:N geladen wird, startet die
 * Tour automatisch nach DOMContentLoaded + kurzer Stabilisierungspause.
 */
(function(){
  window.SA = window.SA || {};

  var DRIVER_JS_URL = 'https://cdn.jsdelivr.net/npm/driver.js@1.3.1/dist/driver.js.iife.js';
  var DRIVER_CSS_URL = 'https://cdn.jsdelivr.net/npm/driver.js@1.3.1/dist/driver.css';
  var LS_KEY = 'sa-tour-completed';
  var RESUME_DELAY_MS = 650; // Zeit fuer Charts/Async-Renders nach DOMContentLoaded

  var _loadPromise = null;

  function _loadDriverJS() {
    if (_loadPromise) return _loadPromise;
    _loadPromise = new Promise(function(resolve, reject) {
      // CSS
      if (!document.querySelector('link[data-sa-tour-css]')) {
        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = DRIVER_CSS_URL;
        link.setAttribute('data-sa-tour-css', '1');
        document.head.appendChild(link);
      }
      // JS
      if (window.driver && window.driver.js && window.driver.js.driver) {
        resolve(window.driver.js.driver);
        return;
      }
      var s = document.createElement('script');
      s.src = DRIVER_JS_URL;
      s.async = true;
      s.onload = function() {
        if (window.driver && window.driver.js && window.driver.js.driver) {
          resolve(window.driver.js.driver);
        } else {
          reject(new Error('Driver.js loaded but global driver missing'));
        }
      };
      s.onerror = function() { reject(new Error('Failed to load Driver.js from CDN')); };
      document.head.appendChild(s);
    });
    return _loadPromise;
  }

  /**
   * Filter globale TOUR_STEPS auf Steps die auf der AKTUELLEN Page liegen.
   * Gibt { filteredSteps, startIndex, tourStartIndexInFull } zurueck.
   */
  function _stepsForCurrentPage(fromStep) {
    var all = SA.TOUR_STEPS || [];
    var path = window.location.pathname;
    // Normalize trailing slash
    if (path.length > 1 && path.charAt(path.length - 1) === '/') path = path.slice(0, -1);

    var filtered = [];
    var indexMap = []; // filteredIndex → fullIndex
    for (var i = 0; i < all.length; i++) {
      var s = all[i];
      var sp = s.page;
      if (sp.length > 1 && sp.charAt(sp.length - 1) === '/') sp = sp.slice(0, -1);
      if (sp === path) {
        filtered.push(s);
        indexMap.push(i);
      }
    }

    // Finde startIndex innerhalb der gefilterten Liste
    var startIdx = 0;
    for (var j = 0; j < indexMap.length; j++) {
      if (indexMap[j] >= fromStep) { startIdx = j; break; }
      startIdx = j + 1; // Fallback: nach Ende
    }
    if (startIdx >= filtered.length) startIdx = Math.max(0, filtered.length - 1);

    return { steps: filtered, indexMap: indexMap, startIndex: startIdx };
  }

  function _mapStepToDriver(step, fullIndex) {
    var driverStep = {
      element: step.element,
      popover: {
        title: step.popover.title || '',
        description: step.popover.description || '',
        side: step.popover.side || 'bottom',
        align: step.popover.align || 'start'
      }
    };
    // onNextClick Handler fuer Navigation zum naechsten Page
    if (step.navigateAfter) {
      driverStep.popover.onNextClick = function() {
        var target = step.navigateAfter.url;
        var stepIdx = step.navigateAfter.step;
        var sep = target.indexOf('?') >= 0 ? '&' : '?';
        window.location.href = target + sep + 'tour=step:' + stepIdx;
      };
    }
    return driverStep;
  }

  SA.tour = {
    /**
     * Startet die Tour. fromStep ist der Index in der globalen SA.TOUR_STEPS Liste.
     * Die Tour filtert auf die aktuelle Page und startet am ersten passenden Step >= fromStep.
     */
    start: function(fromStep) {
      if (typeof fromStep !== 'number') fromStep = 0;
      if (!SA.TOUR_STEPS || !SA.TOUR_STEPS.length) {
        console.warn('[SA.tour] SA.TOUR_STEPS missing — include tour-config.js');
        return;
      }
      _loadDriverJS().then(function(driverFn) {
        var page = _stepsForCurrentPage(fromStep);
        if (!page.steps.length) {
          console.warn('[SA.tour] No steps for current page', window.location.pathname);
          return;
        }
        // Pre-check Anchor existiert
        var firstEl = document.querySelector(page.steps[page.startIndex].element);
        if (!firstEl) {
          // Wenn Anchor fehlt und Step optional → skip naechster
          if (page.steps[page.startIndex].optional && page.startIndex + 1 < page.steps.length) {
            page.startIndex += 1;
          }
        }

        var driverSteps = [];
        for (var i = 0; i < page.steps.length; i++) {
          driverSteps.push(_mapStepToDriver(page.steps[i], page.indexMap[i]));
        }

        var d = driverFn({
          showProgress: true,
          allowClose: true,
          overlayOpacity: 0.72,
          stagePadding: 6,
          stageRadius: 8,
          smoothScroll: true,
          animate: true,
          progressText: 'Schritt {{current}} von ' + SA.TOUR_STEPS.length,
          nextBtnText: 'Weiter →',
          prevBtnText: '← Zurueck',
          doneBtnText: 'Fertig',
          onDestroyed: function() {
            try { localStorage.setItem(LS_KEY, new Date().toISOString().slice(0,10)); } catch(e){}
            // Clear ?tour= param from URL after completion
            if (window.location.search.indexOf('tour=') >= 0) {
              try { history.replaceState(null, '', window.location.pathname); } catch(e){}
            }
          }
        });
        d.setSteps(driverSteps);
        d.drive(page.startIndex);
      }).catch(function(err) {
        console.error('[SA.tour] Failed to start tour:', err);
        alert('Tour konnte nicht geladen werden. Pruefe die Internetverbindung.');
      });
    },

    /** Manueller Reset (Debug / "Tour erneut anzeigen") */
    reset: function() {
      try { localStorage.removeItem(LS_KEY); } catch(e){}
    },

    /** True wenn Tour schon einmal abgeschlossen wurde */
    wasCompleted: function() {
      try { return !!localStorage.getItem(LS_KEY); } catch(e){ return false; }
    },

    _checkResumeFromUrl: function() {
      var params = new URLSearchParams(window.location.search);
      var tourParam = params.get('tour');
      if (!tourParam) return;
      if (tourParam === 'done') {
        // Finaler Step auf Dashboard
        setTimeout(function(){ SA.tour.start(12); }, RESUME_DELAY_MS);
        return;
      }
      if (tourParam.indexOf('step:') === 0) {
        var step = parseInt(tourParam.split(':')[1], 10);
        if (!isNaN(step)) {
          setTimeout(function(){ SA.tour.start(step); }, RESUME_DELAY_MS);
        }
      }
    }
  };

  // Auto-Resume bei Page-Load mit ?tour=step:N
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', SA.tour._checkResumeFromUrl);
  } else {
    SA.tour._checkResumeFromUrl();
  }
})();
