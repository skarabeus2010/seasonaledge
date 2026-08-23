-- Nach dem Fix: prüft, dass kein XETRA-Ticker im Fenster einen tdoy-Stall/Sprung hat.
-- Erwartung: 0 Zeilen.
WITH x AS (
  SELECT ticker, date, tdoy,
         LAG(tdoy) OVER (PARTITION BY ticker ORDER BY date) AS prev_tdoy
  FROM prices
  WHERE (ticker LIKE '%.DE' OR ticker = '^GDAXI')
    AND date BETWEEN '2026-08-01' AND '2026-08-31'
)
SELECT ticker, date, prev_tdoy, tdoy
FROM x
WHERE prev_tdoy IS NOT NULL AND tdoy <> prev_tdoy + 1
ORDER BY ticker, date;
