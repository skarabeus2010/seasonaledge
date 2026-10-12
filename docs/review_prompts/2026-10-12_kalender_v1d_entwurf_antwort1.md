# Antwort Codex — V1d Entwurf v1 (2026-10-12)

Zu: [Entwurf v1](2026-10-12_kalender_v1d_entwurf.md)

**Urteil**
Grundsätzlich tragfähig, aber noch keine Freigabe als Bauvorlage. Read-only gegen Code und Verträge geprüft; nichts geändert. B2.2–B2.4 bleiben ausdrücklich V4-Abnahme.

**Befunde (P1/P2)**

- **P2 – Halbtag unbekannt ≠ voller Tag:** §7 verliert `halbtag_status`. Laut [boersenereignisse.py:503](/C:/dev/SeasonalEdge/shared/boersenereignisse.py:503) sind sämtliche anderen Börsen und NYSE außerhalb 2013–2028 ungeprüft. Fehlendes Ereignis darf dort keine bestätigte Vollsitzung ergeben. Status und Sitzungsbedeutung mitgeben; `schlusszeit` auf geschlossenen/ungeprüften Tagen ausdrücklich definieren.
- **P2 – Zeitpunktvertrag fehlt:** §§5–6 legen zulässige Typen, Zeitzonenpflicht und Fehlerfälle nicht fest. Naive Python-Datetimes und JS-Zeittexte ohne Offset können vom Rechnerstandort abhängen und B1.5 verletzen. Einen absoluten Zeitpunkt verlangen, einmal erfassen, normalisiert zurückgeben; CRYPTO ebenfalls ausdrücklich nach UTC umrechnen.
- **P2 – Rand-/Eingabevertrag unvollständig:** Inklusivität beider Intervallenden, `von > bis`, echte Boolean-Pflicht, ganzzahliges `n` und Suchabbruch am unteren Rand fehlen. Python-`is_trading_day` selbst begrenzt den Rechenbereich nicht ([exchange_holidays.py:313](/C:/dev/SeasonalEdge/shared/exchange_holidays.py:313)); alle neuen Helfer müssen 1885–2100 selbst absichern. Ungültige Positionen sind Fehler, nur eine gültige, nicht vorhandene Position ergibt `None/null`.
- **P2 – Prüfung kann gemeinsame Fehler übersehen:** Das Zwillingsraster ersetzt keine unabhängige Referenz für Sitzungslisten und große Offsets. 2000–2030 prüft außerdem keine tatsächlichen Rechenränder. Die zwei Laufzeitzonen müssen benannt sein; DST-, ungültige Eingabe-, fehlende Zone- und Halbtag-Abdeckungsfälle fehlen.
- **P2 – Doku widerspricht dem Scope:** [KALENDER_UMSTELLUNG.md](/C:/dev/SeasonalEdge/docs/KALENDER_UMSTELLUNG.md) kündigt eine gemeinsame Änderung der Betriebshelfer „in V1d“ an; §38 schließt sie aus. Die konservative Betriebskonvention kann bleiben, der verbindliche Plan muss das ausdrücklich übernehmen.

**Antworten 1–3**

1. Das Funktionsset reicht: Monatsfolge plus Position entsteht aus `sitzungen` und `nummern`; Weekly kann den Zieltag und seine Nachfolger enumerieren. Kein weiterer Pflichthelfer nötig. B5.4/B5.7 benötigen später eigene Verbraucherprüfungen.
2. `zieltermin` gehört als reine, explizite Auswahlregel in den Kern. Beide Arten passen zu B5; Handelsschluss darf die heutige Datumswahl nicht heimlich ändern.
3. Ja: vorhandene IANA-Zonen wiederverwenden, CRYPTO/FOREX ausdrücklich UTC, fehlende Zone als Fehler. Die Zonen einmal aus Python ins Bundle erzeugen; keine zweite JS-Tabelle. Die regulären Schlusszeiten dadurch nicht als historisch belegte Sitzungszeiten ausgeben.

**Auflagen**

- Die genannten Eingabe-, Ergebnis-, Abdeckungs- und Randverträge vor Implementierung festschreiben; bestehende JS-Funktionen als delegierende Kompatibilitätshüllen erhalten.
- Unabhängige Sollfolgen samt Positionsreferenz ergänzen; beide Rechenränder, TSE 27.04.2019→07.05.2019, NYSE-Halbtag und ungeprüfte Halbtag-Abdeckung prüfen.
- Mutationstests nur isoliert, atomar, mit gültigem Anker und frischem Bytecodepfad; Fehlerklassen prüfen. Absturz oder abgefangene Ausnahme zählt nicht als gefangen.
- Generatorprüfung und Sitzungswächter ins Gate aufnehmen; Verbraucher und Betriebshelfer bleiben bis zu ihrer ausdrücklich benannten Phase unverändert.
