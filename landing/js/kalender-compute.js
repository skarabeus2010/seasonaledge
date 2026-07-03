/**
 * SeasonAlpha Marktkalender — Compute + Render + Export
 * Auth-Gate + Premium-Gate + Supabase personalized events + ICS export
 */
(function () {
  'use strict';

  var _events   = [];   // from market_calendar.json (static)
  var _personal = [];   // from Supabase (dividends/earnings for watchlist)
  var _year     = new Date().getFullYear();
  var _month    = new Date().getMonth(); // 0-11
  var _isPremium = false;

  var FREE_TYPES    = ['fomc', 'opex', 'triple'];
  var PREMIUM_TYPES = ['ecb', 'boe', 'boj', 'snb', 'boc', 'rba', 'rbnz',
                       'fullmoon', 'newmoon', 'holiday', 'dividend', 'earnings'];

  var CHIP_LABELS = {
    fomc: 'FOMC', opex: 'OPEX', triple: 'Triple Witching',
    ecb: 'EZB', boe: 'BoE', boj: 'BoJ', snb: 'SNB', boc: 'BoC',
    rba: 'RBA', rbnz: 'RBNZ',
    fullmoon: 'Vollmond', newmoon: 'Neumond',
    holiday: 'Feiertag', dividend: 'Div', earnings: 'Earnings',
  };

  var MONTH_NAMES_DE = ['Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'];
  var MONTH_NAMES_EN = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var DOW_DE = ['Mo','Di','Mi','Do','Fr','Sa','So'];
  var DOW_EN = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];

  // ── Public API ──────────────────────────────────────────────────────
  window.SA = window.SA || {};
  SA.Kalender = {
    init:        init,
    switchMonth: switchMonth,
    exportICS:   exportICS,
  };

  // ── Init ────────────────────────────────────────────────────────────
  function init() {
    _waitForAuth();
  }

  function _waitForAuth() {
    if (!window.SA || !SA.auth) { setTimeout(_waitForAuth, 100); return; }
    var user = SA.auth.user;
    if (!user) {
      _showGate();
      // Re-check on auth change
      SA.auth.onAuthChange(function (u) { if (u) { _onAuthed(); } });
      return;
    }
    _checkTierThenBoot();
  }

  function _checkTierThenBoot() {
    if (window.supabase) {
      window.supabase.rpc('get_my_tier').then(function (res) {
        _isPremium = !!(res && res.data === 'premium');
        _onAuthed();
      }).catch(function () { _onAuthed(); });
    } else {
      _onAuthed();
    }
  }

  function _onAuthed() {
    _hideGate();
    _showApp();
    _updateTierUI();
    _buildTabs();
    _buildDowHeader();
    _loadStaticEvents().then(function () {
      _render();
      _loadPersonalized(_year, _month);
    });
  }

  // ── Static event fetch ──────────────────────────────────────────────
  function _loadStaticEvents() {
    return fetch('/data/market_calendar.json')
      .then(function (r) { return r.json(); })
      .then(function (data) { _events = data || []; })
      .catch(function () { _events = []; });
  }

  // ── Personalized (Supabase) ─────────────────────────────────────────
  function _loadPersonalized(year, month) {
    if (!_isPremium || !window.supabase) return;
    var tickers = ['DIA', 'USO'];
    if (SA.watchlist && SA.watchlist.get) {
      SA.watchlist.get().forEach(function (item) {
        if (tickers.indexOf(item.ticker) < 0) tickers.push(item.ticker);
      });
    }
    if (!tickers.length) return;

    var m1 = String(month + 1).padStart(2, '0');
    var monthStart = year + '-' + m1 + '-01';
    var nextM = month === 11 ? (year + 1) + '-01-01'
              : year + '-' + String(month + 2).padStart(2, '0') + '-01';

    _personal = [];
    window.supabase.from('dividend_events')
      .select('ticker,ex_date,amount,currency')
      .gte('ex_date', monthStart)
      .lt('ex_date', nextM)
      .in('ticker', tickers)
      .then(function (res) {
        (res.data || []).forEach(function (d) {
          _personal.push({
            date:   d.ex_date,
            type:   'dividend',
            name:   d.ticker + ' Div',
            detail: d.amount != null
              ? (parseFloat(d.amount).toFixed(2) + ' ' + (d.currency || 'USD'))
              : '',
          });
        });
        _render();
      }).catch(function () {});

    window.supabase.from('earnings_events')
      .select('ticker,report_date,eps_estimate')
      .gte('report_date', monthStart)
      .lt('report_date', nextM)
      .in('ticker', tickers)
      .then(function (res) {
        (res.data || []).forEach(function (d) {
          _personal.push({
            date:   d.report_date,
            type:   'earnings',
            name:   d.ticker + ' Earn.',
            detail: d.eps_estimate != null ? ('EPS ~' + parseFloat(d.eps_estimate).toFixed(2)) : '',
          });
        });
        _render();
      }).catch(function () {});
  }

  // ── Render ──────────────────────────────────────────────────────────
  function _render() {
    var grid = document.getElementById('kal-grid');
    if (!grid) return;

    var allEvents = _events.concat(_personal);

    var firstDay   = new Date(_year, _month, 1);
    var lastDate   = new Date(_year, _month + 1, 0).getDate();
    var startOffset = (firstDay.getDay() + 6) % 7; // Mo=0 … So=6

    var today = new Date();
    var todayStr = today.getFullYear() + '-'
      + String(today.getMonth() + 1).padStart(2, '0') + '-'
      + String(today.getDate()).padStart(2, '0');

    var html = '';

    // Prefix: previous month days
    var prevLast = new Date(_year, _month, 0).getDate();
    for (var i = startOffset; i > 0; i--) {
      html += '<div class="kal-day kal-day--other"><span class="kal-day-num">'
            + (prevLast - i + 1) + '</span></div>';
    }

    // Current month
    for (var d = 1; d <= lastDate; d++) {
      var dateStr = _year + '-' + String(_month + 1).padStart(2, '0') + '-' + String(d).padStart(2, '0');
      var isToday = dateStr === todayStr;
      var dayEvs  = allEvents.filter(function (e) { return e.date === dateStr; });

      html += '<div class="kal-day' + (isToday ? ' kal-day--today' : '') + '">';
      html += '<span class="kal-day-num">' + d + '</span>';

      var shown = 0;
      dayEvs.forEach(function (ev) {
        var isPremEv = PREMIUM_TYPES.indexOf(ev.type) >= 0;
        var locked   = isPremEv && !_isPremium;
        if (shown < 3) {
          var label = (ev.name || CHIP_LABELS[ev.type] || ev.type);
          var title = (ev.detail ? ev.detail : label);
          html += '<span class="kal-chip kal-chip--' + ev.type
                + (locked ? ' kal-chip--locked' : '')
                + '" title="' + _esc(title) + '">'
                + (locked ? '🔒 ' : '') + _esc(label)
                + '</span>';
          shown++;
        } else if (shown === 3) {
          var rem = dayEvs.length - 3;
          html += '<span class="kal-chip kal-chip--more">+' + rem + '</span>';
          shown++;
        }
      });

      html += '</div>';
    }

    // Suffix: next month days
    var total  = startOffset + lastDate;
    var suffix = total % 7 === 0 ? 0 : 7 - (total % 7);
    for (var j = 1; j <= suffix; j++) {
      html += '<div class="kal-day kal-day--other"><span class="kal-day-num">' + j + '</span></div>';
    }

    grid.innerHTML = html;

    // Update month/year display
    var lang = (window.SA && SA.i18n && SA.i18n.current) || 'de';
    var mnames = lang === 'en' ? MONTH_NAMES_EN : MONTH_NAMES_DE;
    var titleEl = document.getElementById('kal-month-title');
    if (titleEl) titleEl.textContent = mnames[_month] + ' ' + _year;
  }

  // ── Tabs ────────────────────────────────────────────────────────────
  function _buildTabs() {
    var tabs = document.getElementById('kal-tabs');
    if (!tabs) return;
    var lang  = (window.SA && SA.i18n && SA.i18n.current) || 'de';
    var mnames = lang === 'en' ? MONTH_NAMES_EN : MONTH_NAMES_DE;
    tabs.innerHTML = '';
    for (var m = 0; m < 12; m++) {
      var btn = document.createElement('button');
      btn.className = 'kal-tab' + (m === _month ? ' kal-tab--active' : '');
      btn.textContent = mnames[m];
      btn.dataset.month = m;
      btn.addEventListener('click', _onTabClick);
      tabs.appendChild(btn);
    }
    // Year nav
    var yearNav = document.getElementById('kal-year-nav');
    if (yearNav) {
      document.getElementById('kal-year-display').textContent = _year;
    }
  }

  function _buildDowHeader() {
    var header = document.getElementById('kal-dow-header');
    if (!header) return;
    var lang = (window.SA && SA.i18n && SA.i18n.current) || 'de';
    var days = lang === 'en' ? DOW_EN : DOW_DE;
    header.innerHTML = days.map(function (d) {
      return '<div class="kal-dow">' + d + '</div>';
    }).join('');
  }

  function _onTabClick(e) {
    var m = parseInt(e.currentTarget.dataset.month, 10);
    switchMonth(_year, m);
  }

  function switchMonth(year, month) {
    _year  = year;
    _month = month;
    // Update active tab
    var tabs = document.querySelectorAll('.kal-tab');
    for (var i = 0; i < tabs.length; i++) {
      tabs[i].classList.toggle('kal-tab--active', parseInt(tabs[i].dataset.month, 10) === month);
    }
    _personal = [];
    _render();
    _loadPersonalized(year, month);
  }

  // ── Year navigation ─────────────────────────────────────────────────
  function changeYear(delta) {
    _year += delta;
    var yearEl = document.getElementById('kal-year-display');
    if (yearEl) yearEl.textContent = _year;
    _personal = [];
    _render();
    _loadPersonalized(_year, _month);
  }
  // Expose for inline onclick
  SA.Kalender.changeYear = changeYear;

  // ── ICS client-side export ──────────────────────────────────────────
  function exportICS() {
    var m1 = String(_month + 1).padStart(2, '0');
    var monthStart = _year + '-' + m1 + '-01';
    var nextM = _month === 11
      ? (_year + 1) + '-01-01'
      : _year + '-' + String(_month + 2).padStart(2, '0') + '-01';

    var evs = _events.concat(_personal).filter(function (e) {
      return e.date >= monthStart && e.date < nextM;
    });

    var lines = [
      'BEGIN:VCALENDAR', 'VERSION:2.0',
      'PRODID:-//SeasonAlpha//MarktKalender//DE',
      'CALSCALE:GREGORIAN',
    ];
    evs.forEach(function (ev) {
      var dt    = ev.date.replace(/-/g, '');
      var d2    = new Date(ev.date);
      d2.setDate(d2.getDate() + 1);
      var dtEnd = d2.toISOString().slice(0, 10).replace(/-/g, '');
      var summ  = (ev.detail ? ev.name + ' — ' + ev.detail : ev.name);
      lines.push(
        'BEGIN:VEVENT',
        'DTSTART;VALUE=DATE:' + dt,
        'DTEND;VALUE=DATE:' + dtEnd,
        'SUMMARY:' + summ,
        'UID:' + ev.type + '-' + dt + '@seasonalpha.ai',
        'END:VEVENT'
      );
    });
    lines.push('END:VCALENDAR');

    var blob = new Blob([lines.join('\r\n')], { type: 'text/calendar;charset=utf-8' });
    var url  = URL.createObjectURL(blob);
    var a    = document.createElement('a');
    a.href = url;
    a.download = 'marktkalender-' + _year + '-' + m1 + '.ics';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // ── UI helpers ──────────────────────────────────────────────────────
  function _showGate() {
    var gate = document.getElementById('kal-auth-gate');
    var app  = document.getElementById('kal-app');
    if (gate) gate.style.display = 'flex';
    if (app)  app.style.display  = 'none';
  }

  function _hideGate() {
    var gate = document.getElementById('kal-auth-gate');
    if (gate) gate.style.display = 'none';
  }

  function _showApp() {
    var app = document.getElementById('kal-app');
    if (app) app.style.display = 'block';
  }

  function _updateTierUI() {
    var banner   = document.getElementById('kal-free-banner');
    var exportEl = document.getElementById('kal-export');
    if (banner)   banner.style.display   = _isPremium ? 'none' : 'flex';
    if (exportEl) exportEl.style.display = _isPremium ? 'block' : 'none';
  }

  function _esc(s) {
    return String(s || '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;')
      .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

})();
