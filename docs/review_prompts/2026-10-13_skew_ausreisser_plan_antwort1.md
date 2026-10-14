**Der Entwurf ist in dieser Form noch nicht freigabefähig.** Die fehlende Extrapolationsbegrenzung ist bestätigt. Die feste Flügelschranke, die Gewichtdefinition und die Gleichheit von Live und Backfill brauchen jedoch Korrekturen.

Geprüft: `HEAD = origin/master = 88c02ff`. Keine Dateien verändert; die vorhandene unversionierte Entwurfsdatei blieb unangetastet.

**1. Messungen: teilweise bestätigt, Rohdatenprüfung offen**

`options_skew_history.json` und `options_skew.json` fehlen lokal. Der öffentliche Abruf war über die verfügbaren Zugriffe nicht möglich. Deshalb sind **Einzelzeilen, Quantile, Monatsmediane, Fallzahlen und Rangverschiebungen nicht unabhängig reproduziert**.

Prüfbar und bestätigt sind:

- Die angegebenen Quotienten: **1,31 %**, **4,12 %** und **0,88 %**.
- Die Gewichte: `[39,67] → −0,3214`, `[18,25] → 1,7143`.
- Aus deinen gerundeten Beispielen folgen MS putZeta **−21,4**, callZeta **+3,5** und XLF callZeta **−10,7 Vol-Punkte**.
- Standard ist tatsächlich **Rank / 365 Tage**; `_rank` entspricht deiner Formel. [landing/pages/skew.html:220](C:/dev/Seasonaledge/landing/pages/skew.html:220), [landing/pages/skew.html:258](C:/dev/Seasonaledge/landing/pages/skew.html:258)
- Radar-RR ist `call_iv − put_iv`; gespeichertes `skew_pts` hat das **umgekehrte Vorzeichen**. Das entspricht der veröffentlichten RR-Definition von SpotGamma. [landing/pages/skew.html:367](C:/dev/Seasonaledge/landing/pages/skew.html:367), [scripts/backfill_skew_massive.py:410](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:410), [SpotGamma-Definition](https://support.spotgamma.com/hc/en-us/articles/39936624524691-What-is-Guided-View-in-Compass)

Zusätzlicher Vergleichspunkt: **Die Radar-Y-Achse rankt `(put_iv + call_iv)/2`, nicht ATM-IV.** Eine Übereinstimmung der RR-Definition beweist deshalb noch keine identische Radarberechnung. Reihenfolge und Quadranten vom 09.10. bleiben ohne Vergleichssnapshot ungeprüft.

Für die Wiederholbarkeit fehlen außerdem: Dateihash, Session, exakter Stichtag, MAD roh oder mit Faktor `1,4826`, Behandlung von MAD = 0, Quantilmethode und genaue Ausschlussregel beim Rangvergleich. „> 6 MAD“ kennzeichnet statistische Auffälligkeit, noch keinen Messfehler.

**2. Ursachen: bestätigt, aber anders gewichtet**

| Vermutung | Befund |
|---|---|
| Unbegrenztes Extrapolationsgewicht | **Bestätigt.** `cm_interp` begrenzt weder Gewicht noch fertige IV; geprüft wird lediglich positive Zielvarianz. Die Aufrufer begrenzen die Entfernung der nächsten Stützstelle auf 15 Tage. [shared/black_scholes.py:107](C:/dev/Seasonaledge/shared/black_scholes.py:107), [scripts/compute_options_skew.py:567](C:/dev/Seasonaledge/scripts/compute_options_skew.py:567) |
| `got[:2]` als Ausreißerquelle | **Vorhanden, aber im regulären Pfad offenbar unerreichbar.** Bei mindestens zwei gültigen DTE zwischen 7 und 75 liefert spätestens Pool `alle` ein Paar. Eine Prüfung aller 2.346 DTE-Paare fand keine Ausnahme. Entfernen ist sinnvoll, als Ursache der beobachteten Punkte bislang unbelegt. [scripts/backfill_skew_massive.py:362](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:362), [shared/black_scholes.py:663](C:/dev/Seasonaledge/shared/black_scholes.py:663) |
| Keine Prüfung der fertigen Zeile | **Im Kern bestätigt.** Es gibt keine abschließende Flügel-/ATM-Prüfung. Auf Leg-Ebene existieren allerdings zusätzlich IV-, Smile-, Paritäts- und Deltafilter. [shared/black_scholes.py:350](C:/dev/Seasonaledge/shared/black_scholes.py:350), [shared/black_scholes.py:489](C:/dev/Seasonaledge/shared/black_scholes.py:489) |
| Earnings als legitime Erklärung | **Grundsätzlich möglich, für diese Fälle unbewiesen.** Negative Zetas allein rechtfertigen keinen Ausschluss. |

Der wichtigere Backfill-Unterschied: `_reconstruct` wählt zunächst ein Paar und bricht bei dessen Fehlschlag ab. Live versucht weitere Gruppen. Zusätzlich generiert Backfill Gruppen erneut aus den gelungenen Legs und lädt vorher lediglich die ersten drei geplanten Gruppen. **Eine gemeinsame Prüffunktion allein garantiert somit keine gleiche Entscheidung.** [scripts/backfill_skew_massive.py:278](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:278), [scripts/backfill_skew_massive.py:362](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:362), [scripts/compute_options_skew.py:558](C:/dev/Seasonaledge/scripts/compute_options_skew.py:558)

Weitere zu prüfende Quellen:

- **Spot und Preiszeitpunkt:** Sessiongleichheit wird inzwischen geprüft. Tages-Schlusskurse einzelner Optionen können innerhalb derselben Session trotzdem zu unterschiedlichen Zeitpunkten gehandelt worden sein. [scripts/compute_options_skew.py:481](C:/dev/Seasonaledge/scripts/compute_options_skew.py:481), [scripts/compute_options_skew.py:692](C:/dev/Seasonaledge/scripts/compute_options_skew.py:692)
- **Dividenden, Ausübung und Parität:** Modellannahmen sind `r = 0,045`, `q = 0`; die Paritätsprüfung betrifft nur den ATM-Ankerbereich und ersetzt keine vollständige Prüfung amerikanischer Optionen. [shared/black_scholes.py:21](C:/dev/Seasonaledge/shared/black_scholes.py:21), [shared/black_scholes.py:387](C:/dev/Seasonaledge/shared/black_scholes.py:387)
- **Verfallswoche:** Poolwechsel, fehlende Legs und Eventtermine zwischen Stützstellen sind konkrete Kandidaten. Aus `cm_extrap` allein lässt sich die historische Kombination nicht rekonstruieren.
- **Abweichende Kontraktauswahl:** Backfill begrenzt auf ±30 % um Spot und höchstens 24 Strikes je Seite/Expiry. Das beeinflusst auch Smilefilter und spätere 10Δ-Abdeckung. [scripts/backfill_skew_massive.py:70](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:70), [scripts/backfill_skew_massive.py:283](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:283)

**3. Gewichtsgrenze: `|w| ≤ 1` bitte ersetzen**

Bei sortierten Laufzeiten gilt:

\[
w=\frac{30-t_1}{t_2-t_1},\qquad V_{30}=(1-w)V_1+wV_2.
\]

`|w| ≤ 1` erlaubt Extrapolation nach unten bis `w = −1`, verbietet aber **jede** Extrapolation nach oben, weil dort `w > 1` gilt.

Besser ist eine symmetrische Begrenzung der relativen Entfernung außerhalb des Intervalls:

\[
h=\max(0,-w,w-1),\qquad h\le H.
\]

| Stützstellen | `w` | `h` |
|---|---:|---:|
| 39 / 67 | −0,321 | 0,321 |
| 18 / 25 | 1,714 | 0,714 |

Alternativ beide Koeffizienten begrenzen: `max(|1−w|, |w|) ≤ G`. Dann bedeutet **G = 1 ausschließlich Interpolation**.

Einen konkreten Grenzwert würde ich erst nach dem Trockenlauf festlegen. Den bisherigen absoluten Abstandsschutz zusätzlich behalten. Ein Mindestabstand allein reicht nicht: Entscheidend ist die Entfernung zum Ziel relativ zum Stützstellenabstand.

Außerdem wirkt `w` auf **totale Varianz**, nicht unmittelbar auf IV. Bei nahezu ausgelöschter Zielvarianz kann die anschließende Quadratwurzel empfindlich bleiben. Endlichkeit, zulässiger IV-Bereich und numerische Stabilität gehören daher ebenfalls in die gemeinsame Prüfung.

**4. Flügelschranke und Earnings**

Eine globale feste Schranke aus den gepoolten `cm`-Quantilen ist **als Diagnose geeignet, als alleiniger Ausschlussgrund noch nicht**:

- `cm` ist kein nachgewiesen sauberer Referenzbestand; deine Messung enthält dort selbst Auffälligkeiten.
- Absolute Vol-Punkte hängen vom Volatilitätsniveau ab.
- Unterschiedliche Ticker, Marktphasen und Events werden vermischt.
- Die angegebenen Grenzen würden XLF mit **−10,7** callZeta bereits ohne Puffer **nicht** erfassen, wenn die Untergrenze bei **−13,2** liegt. Der Vorschlag löst also nicht automatisch beide Anlassfälle.

Empfehlung: statistische Auffälligkeit zunächst separat markieren. Einen Ausschluss aus dem Ranking auf belegte Daten-/Rekonstruktionsfehler oder eine validierte Qualitätsregel stützen. Tickerbezogene, zeitliche und relativ zur ATM-IV skalierte Größen im Trockenlauf vergleichen; keine davon ungeprüft zur harten Regel machen.

**Earnings nicht pauschal ausnehmen und nicht pauschal verwerfen.** Konkave IV-Smiles vor Earnings sind empirisch dokumentiert, insbesondere bei sehr kurzen Laufzeiten; daraus folgt keine beliebige zulässige Größenordnung bei 30 Tagen. [Kachhara et al.](https://arxiv.org/abs/2307.15718)

Hier besteht bereits ein Konflikt im Code: Der erläuternde Kommentar verneint eine harte IV-Konvexitätsinvariante, die spätere Leg-Prüfung bezeichnet sie dennoch als Invariante und verwirft ATM mehr als drei Vol-Punkte über beiden Flügeln. Ein Earnings-Test ausschließlich an der fertigen Zeile reicht deshalb nicht. [shared/black_scholes.py:130](C:/dev/Seasonaledge/shared/black_scholes.py:130), [shared/black_scholes.py:493](C:/dev/Seasonaledge/shared/black_scholes.py:493)

**5. Überarbeiteter Plan**

1. **Messbasis reproduzieren.** Unveränderte JSON-Snapshots mit Hash und Session auswerten. Die vier Fälle anhand Rohpreisen, Spot, Verfällen und ausgewählten Legs nachrechnen. MAD-Auffälligkeit und bestätigten Fehler getrennt berichten.

2. **Gemeinsame CM-Entscheidung bauen.** Kandidatenreihenfolge, Gewichtsprüfung, Interpolation, Ergebnisprüfung und Ersatzgruppen zentralisieren. Bei gescheiterter Gruppe weiterprobieren; erst danach `single` beziehungsweise nicht rankbares Ergebnis. Unterschiede der verfügbaren Rohdaten ausdrücklich ausweisen.

3. **Qualitätsstatus und Herkunft erhalten.** Originalmodus, Regelversion, Gründe, Expiries, DTE, Gewicht und Leg-Werte speichern. `cm_mode="unplausibel"` ist technisch möglich, muss aber den ursprünglichen Modus zusätzlich bewahren. Aktuell gehen selbst die vorhandenen Live-Herkunftsfelder beim History-Schreiben verloren. [scripts/compute_options_skew.py:619](C:/dev/Seasonaledge/scripts/compute_options_skew.py:619), [scripts/compute_options_skew.py:1279](C:/dev/Seasonaledge/scripts/compute_options_skew.py:1279)

4. **Bestand kontrolliert behandeln.** Ohne historische Stützstellen kann das Markierungsskript die neue Gewichtsregel nicht rückwirkend anwenden: Status dann „nicht prüfbar“, gezielte Rekonstruktion separat. Migration idempotent, mit Backup, atomarem Schreiben und Prüfung des Ausgangshashs. Der Supervisor pausiert lediglich von **22:50 bis 00:10 UTC**; eine echte gemeinsame Sperre existiert dort nicht. Alle History-Schreiber müssen ausgeschlossen oder über dieselbe Sperre koordiniert werden. [scripts/backfill_supervisor.sh:36](C:/dev/Seasonaledge/scripts/backfill_supervisor.sh:36), [scripts/backfill_skew_massive.py:869](C:/dev/Seasonaledge/scripts/backfill_skew_massive.py:869)

5. **Frontend und Wiederholungsläufe absichern.** `_isNorm` schließt den neuen Modus bereits aus. Wird die aktuelle Session ausgeschlossen, verschwindet der Ticker wegen der Aktualitätsprüfung gegebenenfalls vollständig; er bekommt nicht einfach einen neuen Rang. Auch `MIN_NORM=20` beachten. Bestehende rankbare Tageszeilen werden durch einen neuen nicht rankbaren Live-Befund derzeit nicht ersetzt; dafür fehlt eine ausdrückliche Aktualisierungsregel. [landing/pages/skew.html:238](C:/dev/Seasonaledge/landing/pages/skew.html:238), [scripts/compute_options_skew.py:1256](C:/dev/Seasonaledge/scripts/compute_options_skew.py:1256)

6. **10Δ ergänzen.** Live berechnet beide 10Δ-Werte bereits in `iv30`; diese mit denselben CM-Stützstellen persistieren. Backfill-Auswahl auf ausreichende Flügelabdeckung prüfen. Fehlende 10Δ-Werte als `null` behandeln, ohne die 25Δ-Rankbarkeit zu verändern. [scripts/compute_options_skew.py:1096](C:/dev/Seasonaledge/scripts/compute_options_skew.py:1096)

7. **Wächter, Mutationen und Wirkungsbericht erweitern.** Originalfälle mit ungerundeten Fixtures; beide Extrapolationsrichtungen und Grenzfälle; nächste Gruppe nach Fehlschlag; Earnings durch die gesamte Leg-Pipeline; identische Entscheidungen bei identischen Eingaben; Wiederholungsläufe und Migration; Ausschluss aktueller Session und Unterschreiten der Mindestzahl. Mutationen müssen insbesondere entfernte Gewichtskontrolle, vorzeitigen Abbruch und versehentliche Rankbarkeit erkennen. Bericht je Ticker: Gründe, Abdeckung, beide Radarachsen, Rank und Percentile sowie verschwundene Ticker.

Den Wechsel des Standardmodus zu Percentile würde ich als separate Nutzerentscheidung belassen. Er mindert die Empfindlichkeit gegenüber Extremwerten, ersetzt aber keine Datenprüfung.

**FREIGABE (Plan): nein**
