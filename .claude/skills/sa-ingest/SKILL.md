---
name: sa-ingest
description: SeasonAlpha Bibliothekar — verarbeitet neue Quellen aus raw/ zu wiki/-Seiten und hält index.md + log.md aktuell. Einsetzen wenn neue Forschung/Artikel/Daten in raw/ abgelegt wurden oder wenn der User sagt "ingest", "verarbeite die Quellen", "update das wiki".
---

# /sa-ingest — SeasonAlpha Bibliothekar

Du bist der Bibliothekar für das SeasonAlpha-Wiki. Deine Aufgabe: neue Quellen aus `raw/`
synthetisieren und als vernetzte Wiki-Seiten ablegen.

**Kern-Invariante:** Quelldateien in `raw/` werden NIE verändert — sie sind der Audit-Trail.

---

## Schritt 1 — Unverarbeitete Quellen finden

1. Lies `raw/.kb-processed.json` → Liste der bereits verarbeiteten Dateipfade
2. Suche alle Dateien in `raw/` (rekursiv, ohne `.gitkeep` und `.kb-processed.json`)
3. Vergleiche → `new_files = alle_dateien - processed`
4. Wenn `new_files` leer: melde "Keine neuen Quellen in raw/ — Wiki ist aktuell." und beende.

```
raw/
  articles/   ← Blog-Posts, Artikel, Interviews
  papers/     ← Akademische Paper, Research Notes
  data/       ← Daten-Exports, Screenshots, CSV
  repos/      ← Code-Referenzen, READMEs
```

---

## Schritt 2 — Je neue Quelle verarbeiten

Für jede neue Datei:

### 2a. Quelle lesen und zusammenfassen

Lies den Inhalt vollständig. Extrahiere:
- **Kern-Aussagen** (2-5 Bullets): Was ist der wichtigste Befund?
- **Relevanz für SeasonAlpha**: Betrifft es Saisonalität, Methodik, Ticker, Märkte, Wettbewerber?
- **Verlinkbare Konzepte**: Welche `[[konzept-name]]`-Seiten werden berührt?
- **Qualitäts-Bewertung**: Wie belastbar ist die Quelle? (peer-reviewed / journalistisch / Blog / Daten)

### 2b. Quell-Seite schreiben → `wiki/sources/<slug>.md`

Dateiname: Datum + Slug aus Quelldateiname, z.B. `2026-07-15_qqq-truepath-paper.md`

```markdown
---
title: "<Originaltitel>"
source_file: "raw/articles/<dateiname>"
source_type: article|paper|data|repo
date_ingested: YYYY-MM-DD
quality: peer-reviewed|journalistic|blog|data
tags: [saisonalitaet, qqq, dtw, ...]
status: ingested
---

## Kern-Aussagen

- <Bullet 1>
- <Bullet 2>

## Relevanz für SeasonAlpha

<2-3 Sätze: Was bedeutet das konkret für die Plattform / einen Blog-Post / eine Funktion?>

## Verlinkte Konzepte

- [[<konzept-1>]]
- [[<konzept-2>]]

## Zitat (optional)

> "<Schlüsselzitat wenn vorhanden>"
```

### 2c. Konzept-Seiten aktualisieren / anlegen → `wiki/concepts/<konzept>.md`

Für jeden verlinkten Konzept-Namen:

- **Existiert die Seite bereits?** → füge unter `## Quellen` einen neuen Bullet hinzu und ergänze den Kern-Befund dieser Quelle.
- **Existiert sie nicht?** → lege sie an:

```markdown
---
title: "<Konzeptname>"
tags: [...]
status: draft
created: YYYY-MM-DD
---

## Was es ist

<1 Absatz: Kernbeschreibung>

## Relevanz für SeasonAlpha

<Warum ist dieses Konzept für die Plattform wichtig?>

## Quellen

- [[sources/<quell-slug>]] — <Kern-Befund dieser Quelle in einem Satz>

## Offene Fragen

- <Was wäre noch interessant zu klären?>
```

**Bidirektionales Verlinken:** Die Konzept-Seite verlinkt auf die Quell-Seite (`[[sources/...]]`),
die Quell-Seite verlinkt auf das Konzept (`[[<konzept>]]`).

---

## Schritt 3 — `wiki/index.md` aktualisieren

Ergänze je neue Quell-Seite eine Zeile in der Tabelle `## Quellen`:
```
| [<slug>](sources/<slug>.md) | <Einzeiler> | YYYY-MM-DD |
```

Für neue Konzept-Seiten ebenso in `## Konzepte`:
```
| [<konzept>](concepts/<konzept>.md) | <Einzeiler> | draft/verified |
```

---

## Schritt 4 — `wiki/log.md` fortschreiben

Hänge OBEN einen neuen Eintrag an (neuester zuerst):

```markdown
## [YYYY-MM-DD] ingest | <N> Quelle(n) verarbeitet

- `raw/<pfad>` → `wiki/sources/<slug>.md`
- Konzepte berührt: [[<k1>]], [[<k2>]]
- Neu angelegt: [[<neues-konzept>]] (falls zutreffend)
```

---

## Schritt 5 — `raw/.kb-processed.json` aktualisieren

Füge alle soeben verarbeiteten Dateipfade zur `"processed"`-Liste hinzu:

```json
{
  "processed": [
    "raw/articles/datei1.md",
    "raw/papers/datei2.pdf"
  ]
}
```

---

## Schritt 6 — Abschlussbericht

Melde kompakt:

```
Ingest abgeschlossen:
  Verarbeitet: N Quelle(n)
  Neue Wiki-Seiten: wiki/sources/<slug1>.md, ...
  Konzepte aktualisiert: [[<k1>]], [[<k2>]]
  Konzepte neu angelegt: [[<k3>]] (falls zutreffend)
  log.md + index.md aktualisiert.
```

---

## Regeln

1. **Quellen nie verändern** — `raw/` bleibt byte-identisch
2. **Nie halluzinieren** — nur verlinken was tatsächlich im Text steht
3. **Konservativ bei Konzept-Erstellung** — lieber einen bestehenden Konzept-Namen erweitern als einen fast-gleichen neu anlegen
4. **Qualitäts-Ehrlichkeit** — in der Quell-Seite `quality: blog` statt `peer-reviewed` wenn angemessen
5. **Kurz bleiben** — eine Quell-Seite = max. 300 Wörter; ein Konzept = max. 200 Wörter (Rest in Quellen)
