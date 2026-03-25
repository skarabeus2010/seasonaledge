# shared/assets.py
# ============================================================
# ASSET-WÖRTERBUCH — SeasonAlpha v8.3
# ============================================================
# Single Source of Truth für:
#   - Ticker-Mapping: Klarname / Keyword  →  Yahoo Finance Symbol
#   - Kategorie-Filter in der Sidebar
#   - Anzeigenamen in Charts und Tabellen
#
# PFLEGE: Neues Asset hier eintragen → alle Pages profitieren sofort.
#
# FELDER pro Eintrag:
#   ticker   — exaktes Yahoo Finance Symbol         (Pflicht)
#   name     — Anzeigename in UI und Charts         (Pflicht)
#   category — Kategorie für Filter-Dropdown        (Pflicht)
#   keywords — Suchbegriffe, Komma-getrennt,
#              Groß-/Kleinschreibung egal           (Pflicht)
# ============================================================

ASSETS = [

    # ── INDIZES ───────────────────────────────────────────────────────────────
    # Dein Original + weitere Welt-Indizes ergänzt
    {"ticker": "^GDAXI",    "name": "DAX 40",               "category": "Index",       "keywords": "DAX, Deutschland, German, Bluechips, Frankfurt, Leitindex, DAX40"},
    {"ticker": "^DJI",      "name": "Dow Jones Industrial", "category": "Index",       "keywords": "Dow, DJIA, Dow Jones, US, Wall Street, Industrial"},
    {"ticker": "^GSPC",     "name": "S&P 500",              "category": "Index",       "keywords": "SP500, S&P, SNP, US, Large Cap, Standard Poor"},
    {"ticker": "^NDX",      "name": "Nasdaq 100",           "category": "Index",       "keywords": "Nasdaq, NDX, Tech, US, QQQ, Technologie"},
    {"ticker": "^STOXX50E", "name": "Euro Stoxx 50",        "category": "Index",       "keywords": "Stoxx, Euro Stoxx, Europa, Europe, EuroStoxx"},
    {"ticker": "^FTSE",     "name": "FTSE 100",             "category": "Index",       "keywords": "FTSE, UK, England, London, British, Großbritannien"},
    {"ticker": "^N225",     "name": "Nikkei 225",           "category": "Index",       "keywords": "Nikkei, Japan, Tokio, Tokyo"},
    {"ticker": "^VIX",      "name": "VIX Volatilitätsindex","category": "Index",       "keywords": "VIX, Volatilität, Volatility, Angst, Fear, CBOE"},
    {"ticker": "^RUT",      "name": "Russell 2000",         "category": "Index",       "keywords": "Russell, Small Cap, US, RUT"},
    {"ticker": "^MDAXI",    "name": "MDAX",                 "category": "Index",       "keywords": "MDAX, Deutschland, MidCap, Mittelstand"},
    {"ticker": "^TECDAX",   "name": "TecDAX",               "category": "Index",       "keywords": "TecDAX, Tech, Technologie, Deutschland"},

    # ── ROHSTOFFE ─────────────────────────────────────────────────────────────
    # Gold ist dein Original — Rest ergänzt
    {"ticker": "GC=F",      "name": "Gold",                 "category": "Rohstoff",    "keywords": "Gold, Edelmetall, Safe Haven, XAU, GC"},
    {"ticker": "SI=F",      "name": "Silber",               "category": "Rohstoff",    "keywords": "Silber, Silver, Edelmetall, XAG"},
    {"ticker": "CL=F",      "name": "Rohöl WTI",           "category": "Rohstoff",    "keywords": "Öl, Oil, Rohöl, WTI, Crude, CL"},
    {"ticker": "BZ=F",      "name": "Rohöl Brent",         "category": "Rohstoff",    "keywords": "Brent, Öl, Oil, Rohöl, Crude"},
    {"ticker": "NG=F",      "name": "Erdgas",               "category": "Rohstoff",    "keywords": "Erdgas, Gas, Natural Gas, NG"},
    {"ticker": "HG=F",      "name": "Kupfer",               "category": "Rohstoff",    "keywords": "Kupfer, Copper, Metall, Industrie"},
    {"ticker": "ZW=F",      "name": "Weizen",               "category": "Rohstoff",    "keywords": "Weizen, Wheat, Getreide, Agrar"},

    # ── FOREX ─────────────────────────────────────────────────────────────────
    # EUR/USD dein Original — Rest ergänzt
    {"ticker": "EURUSD=X",  "name": "Euro / US-Dollar",     "category": "Forex",       "keywords": "EUR, USD, Euro, Dollar, Devisen, Währung, EURUSD"},
    {"ticker": "GBPUSD=X",  "name": "GBP / USD",            "category": "Forex",       "keywords": "Pfund, Pound, GBP, Dollar, Devisen, Sterling"},
    {"ticker": "USDJPY=X",  "name": "USD / JPY",            "category": "Forex",       "keywords": "Yen, Dollar, Japan, Devisen, USDJPY"},
    {"ticker": "USDCHF=X",  "name": "USD / CHF",            "category": "Forex",       "keywords": "Franken, Schweiz, CHF, Dollar, Devisen"},
    {"ticker": "EURGBP=X",  "name": "EUR / GBP",            "category": "Forex",       "keywords": "Euro, Pfund, Devisen, EURGBP"},

    # ── KRYPTO ────────────────────────────────────────────────────────────────
    # Bitcoin dein Original — Rest ergänzt
    {"ticker": "BTC-USD",   "name": "Bitcoin",              "category": "Krypto",      "keywords": "Bitcoin, BTC, Coin, Crypto, Krypto, Digitales Gold"},
    {"ticker": "ETH-USD",   "name": "Ethereum",             "category": "Krypto",      "keywords": "Ethereum, ETH, Crypto, Krypto, Smart Contracts"},
    {"ticker": "SOL-USD",   "name": "Solana",               "category": "Krypto",      "keywords": "Solana, SOL, Crypto, Krypto"},
    {"ticker": "XRP-USD",   "name": "Ripple (XRP)",         "category": "Krypto",      "keywords": "Ripple, XRP, Crypto, Krypto"},

    # ── ETFs ──────────────────────────────────────────────────────────────────
    # Neu ergänzt — häufigste ETFs für saisonale Analysen
    {"ticker": "SPY",       "name": "SPDR S&P 500 ETF",     "category": "ETF",         "keywords": "SPY, SP500, ETF, S&P, SPDR"},
    {"ticker": "QQQ",       "name": "Invesco Nasdaq 100 ETF","category": "ETF",         "keywords": "QQQ, Nasdaq, ETF, Tech, Invesco"},
    {"ticker": "TLT",       "name": "iShares 20+ Yr Treasury","category": "ETF",        "keywords": "TLT, Anleihen, Bonds, Treasury, US, Zinsen"},
    {"ticker": "GLD",       "name": "SPDR Gold ETF",         "category": "ETF",         "keywords": "GLD, Gold, ETF, SPDR, Edelmetall"},
    {"ticker": "IWM",       "name": "iShares Russell 2000",  "category": "ETF",         "keywords": "IWM, Russell, Small Cap, ETF"},

    # ── AKTIEN US ─────────────────────────────────────────────────────────────
    # Apple dein Original — Top-Namen ergänzt die User eintippen würden
    {"ticker": "AAPL",      "name": "Apple Inc.",            "category": "Aktie (US)",  "keywords": "Apple, Tech, iPhone, US, Smartphone"},
    {"ticker": "MSFT",      "name": "Microsoft Corp.",       "category": "Aktie (US)",  "keywords": "Microsoft, Windows, Cloud, Azure, Tech, US"},
    {"ticker": "NVDA",      "name": "NVIDIA Corp.",          "category": "Aktie (US)",  "keywords": "Nvidia, KI, AI, Chips, Halbleiter, GPU, US"},
    {"ticker": "AMZN",      "name": "Amazon.com Inc.",       "category": "Aktie (US)",  "keywords": "Amazon, E-Commerce, Cloud, AWS, US"},
    {"ticker": "GOOGL",     "name": "Alphabet (Google)",     "category": "Aktie (US)",  "keywords": "Google, Alphabet, Search, Cloud, Tech, US"},
    {"ticker": "META",      "name": "Meta Platforms",        "category": "Aktie (US)",  "keywords": "Meta, Facebook, Instagram, WhatsApp, Social Media, US"},
    {"ticker": "TSLA",      "name": "Tesla Inc.",            "category": "Aktie (US)",  "keywords": "Tesla, Elektro, EV, Musk, Auto, US"},
    {"ticker": "JPM",       "name": "JPMorgan Chase",        "category": "Aktie (US)",  "keywords": "JPMorgan, Bank, Finanzen, US"},
    {"ticker": "XOM",       "name": "ExxonMobil Corp.",      "category": "Aktie (US)",  "keywords": "Exxon, Öl, Energy, US"},
    {"ticker": "V",         "name": "Visa Inc.",             "category": "Aktie (US)",  "keywords": "Visa, Zahlung, Payment, Fintech, US"},

    # ── DAX 40 UNTERNEHMEN (dein Original, vollständig unverändert) ───────────
    {"ticker": "ADS.DE",   "name": "Adidas AG",                  "category": "Aktie (DAX)", "keywords": "DAX, Konsum, Sport, Bekleidung, Schuhe"},
    {"ticker": "AIR.DE",   "name": "Airbus SE",                  "category": "Aktie (DAX)", "keywords": "DAX, Luftfahrt, Rüstung, Flugzeuge, Industrie"},
    {"ticker": "ALV.DE",   "name": "Allianz SE",                 "category": "Aktie (DAX)", "keywords": "DAX, Versicherung, Finanzen, München"},
    {"ticker": "BAS.DE",   "name": "BASF SE",                    "category": "Aktie (DAX)", "keywords": "DAX, Chemie, Industrie, Ludwigshafen"},
    {"ticker": "BAYN.DE",  "name": "Bayer AG",                   "category": "Aktie (DAX)", "keywords": "DAX, Pharma, Agrar, Chemie, Gesundheit"},
    {"ticker": "BEI.DE",   "name": "Beiersdorf AG",              "category": "Aktie (DAX)", "keywords": "DAX, Konsum, Nivea, Pflege, Kosmetik"},
    {"ticker": "BMW.DE",   "name": "BMW AG",                     "category": "Aktie (DAX)", "keywords": "DAX, Auto, Mobilität, München, KFZ"},
    {"ticker": "BNR.DE",   "name": "Brenntag SE",                "category": "Aktie (DAX)", "keywords": "DAX, Chemie, Logistik, Handel"},
    {"ticker": "CBK.DE",   "name": "Commerzbank AG",             "category": "Aktie (DAX)", "keywords": "DAX, Bank, Finanzen, Frankfurt"},
    {"ticker": "CON.DE",   "name": "Continental AG",             "category": "Aktie (DAX)", "keywords": "DAX, Auto, Reifen, Zulieferer, Hannover"},
    {"ticker": "1COV.DE",  "name": "Covestro AG",                "category": "Aktie (DAX)", "keywords": "DAX, Chemie, Kunststoffe, Werkstoffe"},
    {"ticker": "DTG.DE",   "name": "Daimler Truck Holding AG",   "category": "Aktie (DAX)", "keywords": "DAX, Auto, LKW, Nutzfahrzeuge, Transport"},
    {"ticker": "DBK.DE",   "name": "Deutsche Bank AG",           "category": "Aktie (DAX)", "keywords": "DAX, Bank, Finanzen, Frankfurt"},
    {"ticker": "DB1.DE",   "name": "Deutsche Börse AG",          "category": "Aktie (DAX)", "keywords": "DAX, Finanzen, Börse, Frankfurt"},
    {"ticker": "DHL.DE",   "name": "DHL Group",                  "category": "Aktie (DAX)", "keywords": "DAX, Logistik, Post, Transport, Paket"},
    {"ticker": "DTE.DE",   "name": "Deutsche Telekom AG",        "category": "Aktie (DAX)", "keywords": "DAX, Telekommunikation, Tech, Bonn, Internet"},
    {"ticker": "EOAN.DE",  "name": "E.ON SE",                    "category": "Aktie (DAX)", "keywords": "DAX, Energie, Versorger, Strom, Essen"},
    {"ticker": "FRE.DE",   "name": "Fresenius SE",               "category": "Aktie (DAX)", "keywords": "DAX, Gesundheit, Pharma, Klinik, Medizin"},
    {"ticker": "HNR1.DE",  "name": "Hannover Rück SE",           "category": "Aktie (DAX)", "keywords": "DAX, Versicherung, Finanzen, Rückversicherung"},
    {"ticker": "HEI.DE",   "name": "Heidelberg Materials AG",    "category": "Aktie (DAX)", "keywords": "DAX, Bau, Zement, Baustoffe, Industrie"},
    {"ticker": "HEN3.DE",  "name": "Henkel AG",                  "category": "Aktie (DAX)", "keywords": "DAX, Konsum, Klebstoffe, Persil, Chemie"},
    {"ticker": "IFX.DE",   "name": "Infineon Technologies AG",   "category": "Aktie (DAX)", "keywords": "DAX, Tech, Halbleiter, Chips, München"},
    {"ticker": "MBG.DE",   "name": "Mercedes-Benz Group AG",     "category": "Aktie (DAX)", "keywords": "DAX, Auto, Premium, Stuttgart, KFZ"},
    {"ticker": "MRK.DE",   "name": "Merck KGaA",                 "category": "Aktie (DAX)", "keywords": "DAX, Pharma, Chemie, Tech, Gesundheit"},
    {"ticker": "MTX.DE",   "name": "MTU Aero Engines AG",        "category": "Aktie (DAX)", "keywords": "DAX, Luftfahrt, Triebwerke, Industrie, Rüstung"},
    {"ticker": "MUV2.DE",  "name": "Münchener Rückversicherung", "category": "Aktie (DAX)", "keywords": "DAX, Versicherung, Finanzen, Munich Re, München"},
    {"ticker": "P911.DE",  "name": "Porsche AG",                 "category": "Aktie (DAX)", "keywords": "DAX, Auto, Sportwagen, Mobilität, Stuttgart"},
    {"ticker": "PAH3.DE",  "name": "Porsche Automobil Holding",  "category": "Aktie (DAX)", "keywords": "DAX, Auto, Holding, Investment, VW"},
    {"ticker": "QIA.DE",   "name": "Qiagen N.V.",                "category": "Aktie (DAX)", "keywords": "DAX, Gesundheit, Biotech, Diagnostik, Labor"},
    {"ticker": "RHM.DE",   "name": "Rheinmetall AG",             "category": "Aktie (DAX)", "keywords": "DAX, Rüstung, Industrie, Automotive, Verteidigung"},
    {"ticker": "RWE.DE",   "name": "RWE AG",                     "category": "Aktie (DAX)", "keywords": "DAX, Energie, Versorger, Erneuerbare, Strom"},
    {"ticker": "SAP.DE",   "name": "SAP SE",                     "category": "Aktie (DAX)", "keywords": "DAX, Tech, Software, Walldorf, Cloud"},
    {"ticker": "SRT3.DE",  "name": "Sartorius AG",               "category": "Aktie (DAX)", "keywords": "DAX, Gesundheit, Labor, Pharma, Biotech"},
    {"ticker": "ENR.DE",   "name": "Siemens Energy AG",          "category": "Aktie (DAX)", "keywords": "DAX, Energie, Industrie, Turbinen, Wind"},
    {"ticker": "SHL.DE",   "name": "Siemens Healthineers AG",    "category": "Aktie (DAX)", "keywords": "DAX, Gesundheit, Medizintechnik, Erlangen"},
    {"ticker": "SIE.DE",   "name": "Siemens AG",                 "category": "Aktie (DAX)", "keywords": "DAX, Industrie, Tech, München, Automatisierung"},
    {"ticker": "SY1.DE",   "name": "Symrise AG",                 "category": "Aktie (DAX)", "keywords": "DAX, Chemie, Duftstoffe, Aroma, Geschmack"},
    {"ticker": "VOW3.DE",  "name": "Volkswagen AG",              "category": "Aktie (DAX)", "keywords": "DAX, Auto, Mobilität, VW, Wolfsburg"},
    {"ticker": "VNA.DE",   "name": "Vonovia SE",                 "category": "Aktie (DAX)", "keywords": "DAX, Immobilien, Wohnen, Miete, Bochum"},
    {"ticker": "ZAL.DE",   "name": "Zalando SE",                 "category": "Aktie (DAX)", "keywords": "DAX, E-Commerce, Mode, Tech, Berlin"},
]

# ── Schnell-Lookup: Ticker (uppercase) → asset-dict ──────────────────────────
# Intern verwendet von ticker_search.py und yahoo_downloader.py.
TICKER_MAP: dict = {a["ticker"].upper(): a for a in ASSETS}

# ── Sortierte Kategorie-Liste für Filter-Dropdown ─────────────────────────────
CATEGORIES: list[str] = sorted(set(a["category"] for a in ASSETS))
