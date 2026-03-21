"""
programmatic_seo_builder.py — SEO Landingpage Generator
=========================================================
Generiert automatisch SEO-optimierte HTML-Landingpages
fuer jeden Finanztitel aus einer Datenliste.

Ausfuehren:  py seo/programmatic_seo_builder.py
Ergebnis:    seo/output/ Ordner mit einer HTML-Datei pro Titel

Schritt-fuer-Schritt Erklaerung:
1. Wir definieren eine Liste von Finanztiteln (Ticker, Name, bester Monat etc.)
2. Wir laden ein HTML-Template (seo_template.html) mit Platzhaltern {{ ... }}
3. Fuer jeden Titel fuellen wir die Platzhalter mit den echten Daten
4. Wir speichern das Ergebnis als eigene HTML-Datei (z.B. apple-saisonalitaet.html)

Abhaengigkeit: pip install Jinja2
"""

# ── Schritt 1: Bibliotheken importieren ──────────────────────────────────────

# os: Fuer Dateipfade und Ordner erstellen
import os

# datetime: Fuer das aktuelle Datum (wird im Template angezeigt)
from datetime import datetime

# Jinja2: Die Template-Engine. Sie ersetzt {{ platzhalter }} durch echte Werte.
# Environment = laedt Templates aus einem Ordner
# FileSystemLoader = sagt Jinja2 WO die Templates liegen
from jinja2 import Environment, FileSystemLoader


# ── Schritt 2: Datenquelle definieren ────────────────────────────────────────
# Jeder Eintrag ist ein "Dictionary" (dict) = eine Sammlung von
# Schluessel-Wert-Paaren. Spaeter koennte das aus einer CSV oder DB kommen.

TITEL_DATEN = [
    {
        "ticker":       "AAPL",
        "name":         "Apple",
        "slug":         "apple-saisonalitaet",      # URL-freundlicher Name (keine Umlaute/Leerzeichen)
        "typ":          "Aktie",                     # Aktie, ETF, Index, Krypto, Rohstoff
        "bester_monat": "Oktober",
        "win_rate":     "72",                        # In Prozent
        "avg_return":   "+3.2%",                     # Durchschnittsrendite im besten Monat
        "jahre":        "20",                        # Wie viele Jahre analysiert
    },
    {
        "ticker":       "^GDAXI",
        "name":         "DAX",
        "slug":         "dax-saisonalitaet",
        "typ":          "Index",
        "bester_monat": "November",
        "win_rate":     "68",
        "avg_return":   "+2.8%",
        "jahre":        "30",
    },
    {
        "ticker":       "BMW.DE",
        "name":         "BMW",
        "slug":         "bmw-saisonalitaet",
        "typ":          "Aktie",
        "bester_monat": "April",
        "win_rate":     "65",
        "avg_return":   "+2.1%",
        "jahre":        "20",
    },
    {
        "ticker":       "BTC-USD",
        "name":         "Bitcoin",
        "slug":         "bitcoin-saisonalitaet",
        "typ":          "Kryptowaehrung",
        "bester_monat": "November",
        "win_rate":     "75",
        "avg_return":   "+18.5%",
        "jahre":        "12",
    },
    {
        "ticker":       "TSLA",
        "name":         "Tesla",
        "slug":         "tesla-saisonalitaet",
        "typ":          "Aktie",
        "bester_monat": "Januar",
        "win_rate":     "70",
        "avg_return":   "+8.3%",
        "jahre":        "12",
    },
    {
        "ticker":       "GC=F",
        "name":         "Gold",
        "slug":         "gold-saisonalitaet",
        "typ":          "Rohstoff",
        "bester_monat": "September",
        "win_rate":     "67",
        "avg_return":   "+2.4%",
        "jahre":        "30",
    },
    {
        "ticker":       "CL=F",
        "name":         "Oel (WTI)",
        "slug":         "oel-saisonalitaet",
        "typ":          "Rohstoff",
        "bester_monat": "Februar",
        "win_rate":     "62",
        "avg_return":   "+3.1%",
        "jahre":        "25",
    },
    {
        "ticker":       "QQQ",
        "name":         "Nasdaq 100 ETF",
        "slug":         "nasdaq-100-saisonalitaet",
        "typ":          "ETF",
        "bester_monat": "November",
        "win_rate":     "73",
        "avg_return":   "+4.1%",
        "jahre":        "25",
    },
    {
        "ticker":       "DIA",
        "name":         "Dow Jones ETF",
        "slug":         "dow-jones-saisonalitaet",
        "typ":          "ETF",
        "bester_monat": "Dezember",
        "win_rate":     "70",
        "avg_return":   "+2.3%",
        "jahre":        "25",
    },
    {
        "ticker":       "SAP.DE",
        "name":         "SAP",
        "slug":         "sap-saisonalitaet",
        "typ":          "Aktie",
        "bester_monat": "Oktober",
        "win_rate":     "66",
        "avg_return":   "+3.0%",
        "jahre":        "20",
    },
]


# ── Schritt 3: Jinja2 Template-Engine einrichten ────────────────────────────

def build_seo_pages():
    """
    Hauptfunktion: Laedt das Template, fuellt es fuer jeden Titel
    mit Daten und speichert das Ergebnis als HTML-Datei.
    """

    # Wo liegt dieses Skript? Davon ausgehend finden wir das Template.
    # __file__ = der Dateipfad dieses Skripts
    # os.path.dirname = der Ordner in dem es liegt
    skript_ordner = os.path.dirname(os.path.abspath(__file__))

    # Jinja2 Environment erstellen:
    # FileSystemLoader sagt Jinja2: "Suche Templates im Ordner 'skript_ordner'"
    env = Environment(
        loader=FileSystemLoader(skript_ordner),
        autoescape=True,  # Schuetzt vor XSS (boesartiger Code in Daten)
    )

    # Template laden: Die Datei seo_template.html mit den {{ platzhaltern }}
    template = env.get_template("seo_template.html")

    # Ausgabe-Ordner erstellen (falls er nicht existiert)
    output_ordner = os.path.join(skript_ordner, "output")
    os.makedirs(output_ordner, exist_ok=True)

    # Aktuelles Datum fuer die Seiten (z.B. "20.03.2026")
    heute = datetime.now().strftime("%d.%m.%Y")

    # Anzahl KI-Features (fuer den SEO-Text)
    ki_count = 15

    # ── Schritt 4: Fuer jeden Titel eine HTML-Seite generieren ──────────

    print(f"\n{'='*60}")
    print(f"  SeasonalEdge — Programmatic SEO Builder")
    print(f"  {len(TITEL_DATEN)} Seiten werden generiert...")
    print(f"{'='*60}\n")

    for i, titel in enumerate(TITEL_DATEN, 1):
        # Template mit den Daten dieses Titels fuellen.
        # Jinja2 ersetzt {{ name }} durch titel["name"], {{ ticker }} durch titel["ticker"] etc.
        html_output = template.render(
            **titel,                # Entpackt alle Schluessel-Wert-Paare als Template-Variablen
            datum=heute,            # Zusaetzliche Variable: aktuelles Datum
            ki_count=ki_count,      # Anzahl KI-Modelle
        )

        # Dateiname: z.B. "apple-saisonalitaet.html"
        dateiname = f'{titel["slug"]}.html'
        dateipfad = os.path.join(output_ordner, dateiname)

        # HTML-Datei speichern
        with open(dateipfad, "w", encoding="utf-8") as f:
            f.write(html_output)

        # Fortschritt anzeigen
        print(f"  [{i}/{len(TITEL_DATEN)}] {titel['name']:20s} -> {dateiname}")

    print(f"\n{'='*60}")
    print(f"  Fertig! {len(TITEL_DATEN)} Seiten in: {output_ordner}")
    print(f"{'='*60}\n")


# ── Schritt 5: Skript ausfuehren ────────────────────────────────────────────
# Dieser Block wird nur ausgefuehrt wenn das Skript direkt gestartet wird
# (nicht wenn es von einem anderen Skript importiert wird).

if __name__ == "__main__":
    build_seo_pages()
