// WÖRTLICHE Kopie der Lader VOR der Umstellung auf SA.kurse (git 05e6310), nur für scripts/js/probe_kurse_huellen.js.
// Nicht ändern: sie ist die Referenz "vorher" für den Vergleich der Rückgaben je Aufrufer.
'use strict';
module.exports = function (SA) {
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
    // Retry mit linearem Backoff + Jitter, damit parallel ladende Ticker nicht im
    // Gleichtakt erneut anklopfen (Thundering Herd). Ein Retry-After des Servers hat Vorrang.
    function retry(retryAfterMs) {
      var wait = (retryAfterMs != null) ? retryAfterMs
                                        : (350 * (attempt + 1) + Math.floor(Math.random() * 300));
      return new Promise(function(res) { setTimeout(res, wait); })
        .then(function() { return fetchBatch(offset, attempt + 1); });
    }
    return fetch(SA.supabase.url + '/rest/v1/prices?' + q, {
      headers: {
        'apikey': SA.supabase.key,
        'Authorization': 'Bearer ' + SA.supabase.key,
        'Range': offset + '-' + (offset + batchSize - 1),
        'Prefer': 'count=exact'
      }
    }).then(function(r) {
      // Rate-Limit (429) / Serverfehler (5xx) → Retry. Seiten wie die Watchlist feuern
      // viele parallele Batch-Requests; einzelne können gedrosselt werden. Ohne Retry
      // landete früher ein Fehler-JSON als "Zeilen" im Ergebnis.
      if (!r.ok) {
        if ((r.status === 429 || r.status >= 500) && attempt < 4) {
          var ra = parseInt(r.headers.get('retry-after'), 10);
          return retry(isNaN(ra) ? null : ra * 1000);
        }
        throw new Error('prices ' + r.status + ' (' + ticker + ')');
      }
      var contentRange = r.headers.get('content-range');
      return r.json().then(function(rows) {
        // Fehler-JSON (kein Array) NIEMALS als Zeilen anhängen — sonst kommt ein
        // kurzes/kaputtes Ergebnis raus und das UI zeigt fälschlich "Zu wenig Daten".
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
    }, function(netErr) {
      // Netzwerk-Fehler / abgebrochener Request (z.B. Tab-Ruhezustand): fetch() rejectet
      // statt ein !r.ok zu liefern → hier ebenfalls begrenzt neu versuchen (genau der
      // im Commit genannte Ruhezustand-Fall, der sonst durchgereicht würde).
      if (attempt < 4) return retry(null);
      throw netErr;
    });
  }
  return fetchBatch(0).then(function(rows) {
    if (SA.cache && rows && rows.length) SA.cache.set('prices', cacheKey, rows);
    return rows;
  });
};
var dc = {
  _vollCache: {},
  /**
   * Volle Kurshistorie per Datums-Blättern (date=gt.<letztes Datum>, 1000 je Abruf, OHNE count=exact). Grund: der
   * gemeinsame Lader SA.fetchAllPrices zählt bei JEDEM Block exakt mit; bei langen Reihen (^GSPC ab 1895, 35 000
   * Zeilen) bricht Supabase das mit HTTP 500 ab (gemessen 2026-10-09 nach 28 s). Blättern über den Index
   * (ticker, date) braucht keine Zählung und keinen wachsenden Offset. Fehler oder kein Array → Ablehnung.
   */
  ladeVollHistorie: function(ticker) {
    var self = this, jetzt = Date.now(), c = this._vollCache[ticker];
    if (c && jetzt - c.zeit < 15 * 60 * 1000) return Promise.resolve(c.zeilen);
    if (!(window.SA && SA.supabase && SA.supabase.url)) return Promise.reject(new Error('Kursquelle nicht verfügbar'));
    var alle = [];
    function seite(nach, versuch) {
      var q = 'ticker=eq.' + encodeURIComponent(ticker) + '&select=date,close,log_return,tdom,tdoy&order=date.asc&limit=1000' +
              (nach ? '&date=gt.' + nach : '');
      return fetch(SA.supabase.url + '/rest/v1/prices?' + q, {
        headers: { 'apikey': SA.supabase.key, 'Authorization': 'Bearer ' + SA.supabase.key }
      }).then(function(r) {
        if (!r.ok) {
          if ((r.status === 429 || r.status >= 500) && (versuch || 0) < 3) {
            return new Promise(function(res) { setTimeout(res, 400 * ((versuch || 0) + 1)); })
              .then(function() { return seite(nach, (versuch || 0) + 1); });
          }
          throw new Error('prices ' + r.status + ' (' + ticker + ')');
        }
        return r.json().then(function(z) {
          if (!Array.isArray(z)) throw new Error('prices non-array (' + ticker + ')');
          alle = alle.concat(z);
          return z.length === 1000 ? seite(z[z.length - 1].date, 0) : alle;
        });
      });
    }
    return seite(null, 0).then(function(z) { self._vollCache[ticker] = { zeit: Date.now(), zeilen: z }; return z; });
  },

};
return { fetchAllPrices: SA.fetchAllPrices, ladeVollHistorie: dc.ladeVollHistorie.bind(dc) };
};
