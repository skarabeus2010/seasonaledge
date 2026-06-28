# Disclaimer-Vorlagen — YouTube-Kanal „Saisonale Börsenanalyse"

**Stand:** Juni 2026
**Format:** Historische Saisonalitätsdaten · Shorts · Keine expliziten Kauf-/Verkaufsempfehlungen
**Status:** **Kanonische Quelle** für alle Rechts-/Disclaimer-Texte des Kanals. Pipeline + Agenten
(`shorts-skripter`, `wachstum-distributor`) und alle SEO-/Posting-Hinweise an den Owner MÜSSEN sich
hierauf beziehen. Siehe Einbindung in [YOUTUBE_STRATEGY.md](YOUTUBE_STRATEGY.md#compliance--disclaimer-verbindlich).

> **Hinweis:** Diese Texte wurden bereits **anwaltlich erstellt/geprüft** (Stand Juni 2026) — keine
> weitere Prüfung nötig. Bei größeren Format-/Rechtsänderungen erneut prüfen lassen.

---

## Teil 1 — Kanal-Disclaimer (About-Seite)

*Wo einfügen:* YouTube Studio → Kanal anpassen → Beschreibung

### Deutsch

```
━━  RECHTLICHER HINWEIS  ━━

Alle auf diesem Kanal veröffentlichten Inhalte dienen ausschließlich der
allgemeinen Information und der Darstellung historischer Marktdaten.

Die gezeigten saisonalen Muster, Statistiken und Verläufe basieren auf
historischen Kursdaten und stellen weder eine Anlageberatung noch eine
Anlageempfehlung noch eine Aufforderung zum Kauf, Verkauf oder Halten
von Wertpapieren, Kryptowährungen oder sonstigen Finanzinstrumenten dar.

Historische Daten und saisonale Muster sind kein verlässlicher Indikator
für zukünftige Kurs- oder Marktentwicklungen.

Die Inhalte berücksichtigen nicht die individuelle finanzielle Situation,
die Risikobereitschaft oder die Anlageziele einzelner Zuschauer.
Investitionen in Wertpapiere und Kryptowährungen sind mit erheblichen
Risiken verbunden, einschließlich des möglichen Totalverlusts des
eingesetzten Kapitals.

Für individuelle Anlageentscheidungen konsultiere bitte einen unabhängigen,
zugelassenen Finanzberater.

[Falls Affiliate-Links vorhanden: Dieser Kanal enthält Partnerlinks.
Beim Abschluss über diese Links erhalte ich ggf. eine Provision.]
```

### Englisch (optional)

```
━━  LEGAL DISCLAIMER  ━━

All content published on this channel is for general informational
purposes only and presents historical market data and seasonal patterns.

Nothing on this channel constitutes investment advice, an investment
recommendation, or a solicitation to buy, sell, or hold any security,
cryptocurrency, or other financial instrument.

Historical data and seasonal patterns are not a reliable indicator of
future market performance.

Content does not take into account the individual financial situation,
risk tolerance, or investment objectives of any viewer.
Investments involve significant risk, including the possible loss of
the entire amount invested.

Please consult a qualified, independent financial advisor before making
any investment decision.

[If affiliate links apply: This channel may contain affiliate links.
I may receive a commission on transactions made through these links.]
```

---

## Teil 2 — Video-Disclaimer (Beschreibung je Short)

*Wo einfügen:* YouTube Studio → Standardinfo für Videos (einmal hinterlegen = automatisch bei jedem
Short). Zusätzlich manuell oben in die Beschreibung, damit er ohne „mehr anzeigen" sichtbar ist.

### 2a · Kurzform — empfohlen für Shorts (~230 Zeichen)

```
⚠️ Historische Daten — keine Anlageberatung oder -empfehlung.
Saisonale Muster sind kein Indikator für zukünftige Entwicklungen.
Kein Kauf- oder Verkaufssignal. Eigene Recherche erforderlich.
Investitionen bergen Verlustrisiken bis zum Totalverlust.
```

### 2a-EN · Kurzform Englisch

```
⚠️ Historical data — not investment advice or a recommendation.
Seasonal patterns are not an indicator of future performance.
No buy or sell signal. Do your own research.
Investing carries risk of loss up to total loss of capital.
```

### 2b · Standardform

```
━━  RECHTLICHER HINWEIS  ━━

Die in diesem Video dargestellten saisonalen Muster und Statistiken
basieren ausschließlich auf historischen Kursdaten.

Kein Kauf-, Verkaufs- oder Halteempfehlung.
Keine individuelle Anlageberatung.
Historische Daten sind kein verlässlicher Indikator für die Zukunft.
Investitionen sind mit Verlustrisiken verbunden.

Vor Anlageentscheidungen bitte unabhängigen Finanzberater konsultieren.
```

### 2c · Krypto-Zusatz (bei Krypto-Inhalten ergänzen)

```
[Zusatz für Krypto-Inhalte]

Kryptowährungen unterliegen keiner staatlichen Einlagensicherung und
sind hochvolatile, spekulative Anlagen. Vergangene Saisonalitätsmuster
bei Kryptowährungen haben eine besonders geringe Vorhersagekraft für
zukünftige Kursentwicklungen. Dieser Kanal erbringt keine
Krypto-Dienstleistungen im Sinne der MiCAR-Verordnung.
```

---

## Teil 3 — Kurzeinblender im Short (Textoverlay)

Wird vom `compose.py`-Schritt **eingebrannt** (Pflicht, 2-3s, gut lesbar). Standard = „Standard"-Variante.

| Variante    | Text                                                                                      | Dauer    |
|-------------|-------------------------------------------------------------------------------------------|----------|
| Minimal     | Historische Daten · Keine Anlageberatung                                                  | 2 Sek.   |
| Standard    | Historische Daten — kein Kauf-/Verkaufssignal — keine Anlageberatung                     | 3 Sek.   |
| Ausführlich | Nur historische Daten · Keine Anlageberatung · Vergangene Muster ≠ Zukunft · Kein Signal | 4–5 Sek. |
| EN-Standard | Historical data — no buy/sell signal — not investment advice                              | 3 Sek.   |

Zusätzlich trägt der **Chart-Renderer** eine dezente Dauer-Fußzeile („Historische Daten · keine
Anlageberatung") in jedem Frame.

---

## Teil 4 — Impressum-Vorlage (§ 5 DDG)

*Wo einfügen:* Externe Seite (eigene Website / `seasonalpha.ai`), dann in YouTube → Links →
„Impressum" verlinken. YouTube erlaubt kein vollständiges Impressum direkt im Kanal.
(Deckt sich mit dem YMYL-P0 in [SEO_TODO.md](SEO_TODO.md): Impressum/Datenschutz sind ohnehin Pflicht.)

```
IMPRESSUM

Angaben gemäß § 5 DDG (Digitale-Dienste-Gesetz)

Name:            [Vor- und Nachname]
Anschrift:       [Straße und Hausnummer]
                 [PLZ und Ort]
                 Deutschland

E-Mail:          [deine@email.de]

[Falls gewerblich:]
Umsatzsteuer-ID: DE[XXXXXXXXX]
                 (gemäß § 27a UStG)

Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV:
[Vor- und Nachname], [Anschrift wie oben]

Haftungshinweis:
Trotz sorgfältiger inhaltlicher Kontrolle übernehmen wir
keine Haftung für die Inhalte externer Links. Für den
Inhalt der verlinkten Seiten sind ausschließlich deren
Betreiber verantwortlich.
```

> **Gewerbepflicht:** Sobald der Kanal Einnahmen erzielt (Ads, Affiliate, Sponsoring), besteht i.d.R.
> Gewerbepflicht. → Gewerbeanmeldung beim Ordnungsamt + Gewerberegisternummer ins Impressum.

---

## Teil 5 — Checkliste vor Kanalstart (Owner-Aktionen)

- [ ] Kanal-Disclaimer (deutsch) in der Kanalbeschreibung hinterlegt
- [ ] Impressum auf externer Seite erstellt und im Kanal verlinkt
- [ ] Video-Disclaimer (2a Kurzform) als Standard-Videobeschreibung in YouTube Studio gespeichert
- [ ] Kurzeinblender in Video-Vorlage / Bearbeitungstemplate integriert (→ macht `compose.py` automatisch)
- [ ] Kein explizites Kauf-/Verkaufssignal in den Inhalten (→ erzwingt der `shorts-skripter`-Agent)
- [ ] Affiliate-Links als Werbung gekennzeichnet (falls vorhanden)
- [ ] Krypto-Zusatz (2c) bei Krypto-Inhalten aktiviert
- [ ] Datenschutzerklärung vorhanden (bei eigenem Kontaktformular / Newsletter)
- [x] Anwaltlich erstellt/geprüft — **erledigt** (Stand Juni 2026)

---

## Rechtliche Grundlagen

| Norm | Inhalt |
|------|--------|
| Art. 3 MAR | Definition Anlageempfehlung (EU-Marktmissbrauchsverordnung) |
| § 85 WpHG | Anlageempfehlungen, Offenlegungspflichten |
| § 5 DDG | Impressumspflicht für Telemedien |
| § 18 Abs. 2 MStV | Verantwortlicher für Inhalte (Medienstaatsvertrag) |
| MiCAR | EU-Krypto-Verordnung (ab 2024) |
| § 5a UWG | Irreführung durch Unterlassen (Werbetransparenz) |

**Quellen:** BaFin Factsheet Finfluencer (Januar 2026) · BaFin Merkblatt Anlageberatung (Februar 2025)
