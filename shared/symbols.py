# shared/symbols.py
# Zentrale Ticker-Datenbank für SeasonAlpha.
#
# Felder pro Symbol:
#   name       : Anzeigename (Deutsch)
#   kategorie  : Gruppe für Filterung/Dropdown
#   währung    : "USD" | "EUR" | "GBP" | "JPY" | ...
#   exchange   : Börse (informativ)
#   beschreibung: Kurzbeschreibung (optional, für Tooltips)
#
# Neue Symbole einfach unten in die passende Gruppe eintragen.
# Import-Beispiel:
#   from shared.symbols import SYMBOLS, get_symbols_by_category, KATEGORIEN

# ── Symboldatenbank ────────────────────────────────────────────────────────────

SYMBOLS = {

    # ── US-INDIZES ─────────────────────────────────────────────────────────────
    "^GSPC": {
        "name":         "S&P 500",
        "kategorie":    "US-Index",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "S&P 500 Index — 500 größte US-Unternehmen",
    },
    "^DJI": {
        "name":         "Dow Jones",
        "kategorie":    "US-Index",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Dow Jones Industrial Average — 30 Blue Chips",
    },
    "^IXIC": {
        "name":         "Nasdaq Composite",
        "kategorie":    "US-Index",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Nasdaq Composite — alle Nasdaq-gelisteten Aktien",
    },
    "^NDX": {
        "name":         "Nasdaq 100",
        "kategorie":    "US-Index",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Nasdaq 100 — Top 100 Nicht-Finanzwerte",
    },
    "^RUT": {
        "name":         "Russell 2000",
        "kategorie":    "US-Index",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Russell 2000 — 2000 Small-Cap US-Aktien",
    },
    "^VIX": {
        "name":         "VIX Volatilitätsindex",
        "kategorie":    "US-Index",
        "währung":      "USD",
        "exchange":     "CBOE",
        "beschreibung": "CBOE Volatility Index — Angst-Barometer",
    },

    # ── US-ETFs ────────────────────────────────────────────────────────────────
    "SPY": {
        "name":         "SPDR S&P 500 ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Größter S&P 500 ETF — sehr hohe Liquidität",
    },
    "QQQ": {
        "name":         "Invesco Nasdaq 100 ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Nasdaq 100 ETF — Tech-lastig",
    },
    "IWM": {
        "name":         "iShares Russell 2000 ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Small-Cap US-Aktien ETF",
    },
    "DIA": {
        "name":         "SPDR Dow Jones ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Dow Jones Industrial Average ETF",
    },
    "TLT": {
        "name":         "iShares 20+ Year Treasury ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Langläufer US-Staatsanleihen ETF",
    },
    "GLD": {
        "name":         "SPDR Gold ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Gold ETF — physisch hinterlegt",
    },
    "SLV": {
        "name":         "iShares Silver ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Silber ETF",
    },
    "USO": {
        "name":         "United States Oil ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "Rohöl ETF (WTI)",
    },
    "XLF": {
        "name":         "Financial Select Sector ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "US-Finanzsektor ETF",
    },
    "XLK": {
        "name":         "Technology Select Sector ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "US-Technologiesektor ETF",
    },
    "XLE": {
        "name":         "Energy Select Sector ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "US-Energiesektor ETF",
    },
    "XLV": {
        "name":         "Health Care Select Sector ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "US-Gesundheitssektor ETF",
    },
    "XLU": {
        "name":         "Utilities Select Sector ETF",
        "kategorie":    "US-ETF",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "US-Versorgungssektor ETF",
    },

    # ── US-EINZELAKTIEN ────────────────────────────────────────────────────────
    "AAPL": {
        "name":         "Apple",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Apple Inc. — Consumer Electronics & Software",
    },
    "MSFT": {
        "name":         "Microsoft",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Microsoft Corp. — Software & Cloud",
    },
    "NVDA": {
        "name":         "Nvidia",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Nvidia Corp. — GPUs & KI-Chips",
    },
    "AMZN": {
        "name":         "Amazon",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Amazon.com — E-Commerce & Cloud (AWS)",
    },
    "GOOGL": {
        "name":         "Alphabet (Google)",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Alphabet Inc. — Suchmaschine & Werbung",
    },
    "META": {
        "name":         "Meta Platforms",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Meta Platforms — Facebook, Instagram, WhatsApp",
    },
    "TSLA": {
        "name":         "Tesla",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NASDAQ",
        "beschreibung": "Tesla Inc. — Elektrofahrzeuge & Energie",
    },
    "JPM": {
        "name":         "JPMorgan Chase",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "JPMorgan Chase — größte US-Bank",
    },
    "XOM": {
        "name":         "ExxonMobil",
        "kategorie":    "US-Aktie",
        "währung":      "USD",
        "exchange":     "NYSE",
        "beschreibung": "ExxonMobil Corp. — Öl & Gas",
    },

    # ── EUROPÄISCHE INDIZES ────────────────────────────────────────────────────
    "^GDAXI": {
        "name":         "DAX 40",
        "kategorie":    "EU-Index",
        "währung":      "EUR",
        "exchange":     "XETRA",
        "beschreibung": "Deutscher Leitindex — 40 größte deutsche Unternehmen",
    },
    "^MDAXI": {
        "name":         "MDAX",
        "kategorie":    "EU-Index",
        "währung":      "EUR",
        "exchange":     "XETRA",
        "beschreibung": "Mid-Cap Deutschen Aktien — 50 Unternehmen",
    },
    "^STOXX50E": {
        "name":         "Euro Stoxx 50",
        "kategorie":    "EU-Index",
        "währung":      "EUR",
        "exchange":     "Euronext",
        "beschreibung": "50 größte Eurozone-Unternehmen",
    },
    "^FTSE": {
        "name":         "FTSE 100",
        "kategorie":    "EU-Index",
        "währung":      "GBP",
        "exchange":     "LSE",
        "beschreibung": "Britischer Leitindex — 100 größte UK-Unternehmen",
    },
    "^FCHI": {
        "name":         "CAC 40",
        "kategorie":    "EU-Index",
        "währung":      "EUR",
        "exchange":     "Euronext Paris",
        "beschreibung": "Französischer Leitindex — 40 Unternehmen",
    },
    "^SSMI": {
        "name":         "SMI (Schweiz)",
        "kategorie":    "EU-Index",
        "währung":      "CHF",
        "exchange":     "SIX",
        "beschreibung": "Swiss Market Index — 20 größte Schweizer Unternehmen",
    },

    # ── ASIATISCHE INDIZES ─────────────────────────────────────────────────────
    "^N225": {
        "name":         "Nikkei 225",
        "kategorie":    "Asien-Index",
        "währung":      "JPY",
        "exchange":     "TSE",
        "beschreibung": "Japanischer Leitindex — 225 Unternehmen",
    },
    "^HSI": {
        "name":         "Hang Seng",
        "kategorie":    "Asien-Index",
        "währung":      "HKD",
        "exchange":     "HKEX",
        "beschreibung": "Hongkonger Leitindex",
    },
    "^KS11": {
        "name":         "KOSPI (Korea)",
        "kategorie":    "Asien-Index",
        "währung":      "KRW",
        "exchange":     "KRX",
        "beschreibung": "Koreanischer Aktienindex",
    },

    # ── ROHSTOFFE / FUTURES ────────────────────────────────────────────────────
    "GC=F": {
        "name":         "Gold Futures",
        "kategorie":    "Rohstoff",
        "währung":      "USD",
        "exchange":     "COMEX",
        "beschreibung": "Gold Front-Month Futures ($/oz)",
    },
    "SI=F": {
        "name":         "Silber Futures",
        "kategorie":    "Rohstoff",
        "währung":      "USD",
        "exchange":     "COMEX",
        "beschreibung": "Silber Front-Month Futures ($/oz)",
    },
    "CL=F": {
        "name":         "WTI Rohöl Futures",
        "kategorie":    "Rohstoff",
        "währung":      "USD",
        "exchange":     "NYMEX",
        "beschreibung": "West Texas Intermediate Crude Oil ($/barrel)",
    },
    "BZ=F": {
        "name":         "Brent Rohöl Futures",
        "kategorie":    "Rohstoff",
        "währung":      "USD",
        "exchange":     "ICE",
        "beschreibung": "Brent Crude Oil ($/barrel)",
    },
    "NG=F": {
        "name":         "Natural Gas Futures",
        "kategorie":    "Rohstoff",
        "währung":      "USD",
        "exchange":     "NYMEX",
        "beschreibung": "Natural Gas Front-Month Futures",
    },
    "ZC=F": {
        "name":         "Corn Futures (Mais)",
        "kategorie":    "Rohstoff",
        "währung":      "USD",
        "exchange":     "CBOT",
        "beschreibung": "Corn (Mais) Front-Month Futures (cents/bushel)",
    },
    "ZW=F": {
        "name":         "Wheat Futures (Weizen)",
        "kategorie":    "Rohstoff",
        "währung":      "USD",
        "exchange":     "CBOT",
        "beschreibung": "Wheat (Weizen) Front-Month Futures",
    },
    "ES=F": {
        "name":         "E-Mini S&P 500 Futures",
        "kategorie":    "Futures",
        "währung":      "USD",
        "exchange":     "CME",
        "beschreibung": "E-Mini S&P 500 Front-Month Futures",
    },
    "NQ=F": {
        "name":         "E-Mini Nasdaq 100 Futures",
        "kategorie":    "Futures",
        "währung":      "USD",
        "exchange":     "CME",
        "beschreibung": "E-Mini Nasdaq 100 Front-Month Futures",
    },

    # ── EU-EINZELAKTIEN ────────────────────────────────────────────────────────
    "SAP": {"name": "SAP", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "XETRA", "beschreibung": "SAP SE — Enterprise Software"},
    "SIE.DE": {"name": "Siemens", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "XETRA", "beschreibung": "Siemens AG — Industrie & Technologie"},
    "ALV.DE": {"name": "Allianz", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "XETRA", "beschreibung": "Allianz SE — Versicherung"},
    "BAS.DE": {"name": "BASF", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "XETRA", "beschreibung": "BASF SE — Chemie"},
    "BMW.DE": {"name": "BMW", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "XETRA", "beschreibung": "BMW AG — Automobil"},
    "MBG.DE": {"name": "Mercedes-Benz", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "XETRA", "beschreibung": "Mercedes-Benz Group — Automobil"},
    "DTE.DE": {"name": "Deutsche Telekom", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "XETRA", "beschreibung": "Deutsche Telekom AG"},
    "ADS.DE": {"name": "Adidas", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "XETRA", "beschreibung": "Adidas AG — Sportartikel"},
    "ASML": {"name": "ASML", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext", "beschreibung": "ASML Holding — Halbleiter-Lithografie"},
    "MC.PA": {"name": "LVMH", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "LVMH — Luxusgüter"},

    # ── EU-AKTIEN (Top 75 Marktkapitalisierung) ────────────────────────────────
    "RO.SW": {"name": "Roche", "kategorie": "EU-Aktie", "währung": "CHF", "exchange": "SIX", "beschreibung": "Roche Holding — Pharma & Diagnostik"},
    "AZN": {"name": "AstraZeneca", "kategorie": "EU-Aktie", "währung": "GBP", "exchange": "LSE", "beschreibung": "AstraZeneca — Pharma"},
    "NVS": {"name": "Novartis", "kategorie": "EU-Aktie", "währung": "CHF", "exchange": "SIX", "beschreibung": "Novartis AG — Pharma"},
    "HSBC": {"name": "HSBC", "kategorie": "EU-Aktie", "währung": "GBP", "exchange": "LSE", "beschreibung": "HSBC Holdings — Großbank"},
    "SHEL": {"name": "Shell", "kategorie": "EU-Aktie", "währung": "GBP", "exchange": "LSE", "beschreibung": "Shell plc — Öl & Gas"},
    "NESN.SW": {"name": "Nestlé", "kategorie": "EU-Aktie", "währung": "CHF", "exchange": "SIX", "beschreibung": "Nestlé SA — Lebensmittel"},
    "LIN": {"name": "Linde", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "XETRA", "beschreibung": "Linde plc — Industriegase"},
    "OR.PA": {"name": "L'Oréal", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "L'Oréal SA — Kosmetik"},
    "PRX.AS": {"name": "Prosus", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Amsterdam", "beschreibung": "Prosus NV — Tech-Investment"},
    "RMS.PA": {"name": "Hermès", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "Hermès International — Luxusgüter"},
    "TTE": {"name": "TotalEnergies", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "TotalEnergies SE — Energie"},
    "ITX.MC": {"name": "Inditex", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "BME Madrid", "beschreibung": "Inditex SA — Textil (Zara)"},
    "SAN": {"name": "Banco Santander", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "BME Madrid", "beschreibung": "Banco Santander — Großbank"},
    "NVO": {"name": "Novo Nordisk", "kategorie": "EU-Aktie", "währung": "DKK", "exchange": "Kopenhagen", "beschreibung": "Novo Nordisk — Pharma (Diabetes)"},
    "ARM": {"name": "Arm Holdings", "kategorie": "EU-Aktie", "währung": "GBP", "exchange": "NASDAQ", "beschreibung": "Arm Holdings — Chip-Design"},
    "IBE.MC": {"name": "Iberdrola", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "BME Madrid", "beschreibung": "Iberdrola SA — Energieversorger"},
    "SU.PA": {"name": "Schneider Electric", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "Schneider Electric — Elektrotechnik"},
    "AIR.PA": {"name": "Airbus", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "Airbus SE — Luft- & Raumfahrt"},
    "RIO": {"name": "Rio Tinto", "kategorie": "EU-Aktie", "währung": "GBP", "exchange": "LSE", "beschreibung": "Rio Tinto — Bergbau"},
    "ENR.F": {"name": "Siemens Energy", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "XETRA", "beschreibung": "Siemens Energy AG — Energietechnik"},
    "ABBN.SW": {"name": "ABB", "kategorie": "EU-Aktie", "währung": "CHF", "exchange": "SIX", "beschreibung": "ABB Ltd — Elektrotechnik & Automation"},
    "ETN": {"name": "Eaton", "kategorie": "EU-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "Eaton Corp — Elektro & Industrie (IR-Sitz)"},
    "SAF.PA": {"name": "Safran", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "Safran SA — Luft- & Raumfahrt"},
    "BUD": {"name": "AB InBev", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Brüssel", "beschreibung": "Anheuser-Busch InBev — Bier"},
    "RR.L": {"name": "Rolls-Royce", "kategorie": "EU-Aktie", "währung": "GBP", "exchange": "LSE", "beschreibung": "Rolls-Royce Holdings — Triebwerke"},
    "CB": {"name": "Chubb", "kategorie": "EU-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "Chubb Ltd — Versicherung (CH-Sitz)"},
    "BTI": {"name": "British American Tobacco", "kategorie": "EU-Aktie", "währung": "GBP", "exchange": "LSE", "beschreibung": "BAT — Tabak"},
    "UL": {"name": "Unilever", "kategorie": "EU-Aktie", "währung": "GBP", "exchange": "LSE", "beschreibung": "Unilever plc — Konsumgüter"},
    "BBVA": {"name": "BBVA", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "BME Madrid", "beschreibung": "Banco Bilbao Vizcaya Argentaria"},
    "UBS": {"name": "UBS", "kategorie": "EU-Aktie", "währung": "CHF", "exchange": "SIX", "beschreibung": "UBS Group AG — Großbank"},
    "BP": {"name": "BP", "kategorie": "EU-Aktie", "währung": "GBP", "exchange": "LSE", "beschreibung": "BP plc — Öl & Gas"},
    "AI.PA": {"name": "Air Liquide", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "Air Liquide SA — Industriegase"},
    "ACN": {"name": "Accenture", "kategorie": "EU-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "Accenture plc — IT-Beratung (IR-Sitz)"},
    "INVE-B.ST": {"name": "Investor AB", "kategorie": "EU-Aktie", "währung": "SEK", "exchange": "Stockholm", "beschreibung": "Investor AB — Beteiligungsgesellschaft"},
    "SNY": {"name": "Sanofi", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "Sanofi SA — Pharma"},
    "ENEL.MI": {"name": "Enel", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Borsa Italiana", "beschreibung": "Enel SpA — Energieversorger"},
    "UCG.MI": {"name": "UniCredit", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Borsa Italiana", "beschreibung": "UniCredit SpA — Großbank"},
    "GSK": {"name": "GSK", "kategorie": "EU-Aktie", "währung": "GBP", "exchange": "LSE", "beschreibung": "GSK plc — Pharma & Consumer Health"},
    "MDT": {"name": "Medtronic", "kategorie": "EU-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "Medtronic plc — Medizintechnik (IR-Sitz)"},
    "ISP.MI": {"name": "Intesa Sanpaolo", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Borsa Italiana", "beschreibung": "Intesa Sanpaolo — Großbank"},
    "BNP.PA": {"name": "BNP Paribas", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "BNP Paribas — Großbank"},
    "ZURN.SW": {"name": "Zurich Insurance", "kategorie": "EU-Aktie", "währung": "CHF", "exchange": "SIX", "beschreibung": "Zurich Insurance Group — Versicherung"},
    "CFR.SW": {"name": "Richemont", "kategorie": "EU-Aktie", "währung": "CHF", "exchange": "SIX", "beschreibung": "Compagnie Financière Richemont — Luxusgüter"},
    "EQNR": {"name": "Equinor", "kategorie": "EU-Aktie", "währung": "NOK", "exchange": "Oslo", "beschreibung": "Equinor ASA — Energie"},
    "EL.PA": {"name": "EssilorLuxottica", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "EssilorLuxottica — Optik & Brillen"},
    "SPOT": {"name": "Spotify", "kategorie": "EU-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "Spotify Technology — Musik-Streaming (LU-Sitz)"},
    "CS.PA": {"name": "AXA", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "AXA SA — Versicherung"},
    "TT": {"name": "Trane Technologies", "kategorie": "EU-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "Trane Technologies — Klimatechnik (IR-Sitz)"},
    "CDI.PA": {"name": "Dior", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "Christian Dior SE — Luxusgüter"},
    "STX": {"name": "Seagate", "kategorie": "EU-Aktie", "währung": "USD", "exchange": "NASDAQ", "beschreibung": "Seagate Technology — Datenspeicher (IR-Sitz)"},
    "GLCNF": {"name": "Glencore", "kategorie": "EU-Aktie", "währung": "USD", "exchange": "OTC", "beschreibung": "Glencore plc — Rohstoffhandel"},
    "BA.L": {"name": "BAE Systems", "kategorie": "EU-Aktie", "währung": "GBP", "exchange": "LSE", "beschreibung": "BAE Systems — Rüstung & Verteidigung"},
    "CABK.MC": {"name": "CaixaBank", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "BME Madrid", "beschreibung": "CaixaBank SA — Bank"},
    "DG.PA": {"name": "Vinci", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "Vinci SA — Bau & Konzessionen"},
    "ATCO-B.ST": {"name": "Atlas Copco", "kategorie": "EU-Aktie", "währung": "SEK", "exchange": "Stockholm", "beschreibung": "Atlas Copco — Industriekompressoren"},
    "NGG": {"name": "National Grid", "kategorie": "EU-Aktie", "währung": "GBP", "exchange": "LSE", "beschreibung": "National Grid plc — Energienetze"},
    "RHM.F": {"name": "Rheinmetall", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "XETRA", "beschreibung": "Rheinmetall AG — Rüstung & Automobil"},
    "ENGI.PA": {"name": "ENGIE", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "ENGIE SA — Energieversorger"},
    "JCI": {"name": "Johnson Controls", "kategorie": "EU-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "Johnson Controls — Gebäudetechnik (IR-Sitz)"},
    "E": {"name": "ENI", "kategorie": "EU-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "ENI SpA — Öl & Gas (ADR)"},
    "MUV2.DE": {"name": "Munich Re", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "XETRA", "beschreibung": "Münchener Rückversicherung"},
    "ING": {"name": "ING", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Amsterdam", "beschreibung": "ING Group — Bank"},
    "LYG": {"name": "Lloyds Banking", "kategorie": "EU-Aktie", "währung": "GBP", "exchange": "LSE", "beschreibung": "Lloyds Banking Group — Großbank (ADR)"},
    "BCS": {"name": "Barclays", "kategorie": "EU-Aktie", "währung": "GBP", "exchange": "LSE", "beschreibung": "Barclays plc — Großbank (ADR)"},
    "CRH": {"name": "CRH", "kategorie": "EU-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "CRH plc — Baustoffe (IR-Sitz)"},
    "AON": {"name": "Aon", "kategorie": "EU-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "Aon plc — Versicherungsmakler (IR-Sitz)"},
    "VOLV-A.ST": {"name": "Volvo", "kategorie": "EU-Aktie", "währung": "SEK", "exchange": "Stockholm", "beschreibung": "Volvo Group — LKW & Baumaschinen"},
    "HO.PA": {"name": "Thales", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Euronext Paris", "beschreibung": "Thales SA — Verteidigung & Elektronik"},
    "G.MI": {"name": "Generali", "kategorie": "EU-Aktie", "währung": "EUR", "exchange": "Borsa Italiana", "beschreibung": "Assicurazioni Generali — Versicherung"},

    # ── WEITERE US-AKTIEN ────────────────────────────────────────────────────────
    "BRK-B": {"name": "Berkshire Hathaway B", "kategorie": "US-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "Berkshire Hathaway — Warren Buffett"},
    "V": {"name": "Visa", "kategorie": "US-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "Visa Inc. — Zahlungsnetzwerk"},
    "JNJ": {"name": "Johnson & Johnson", "kategorie": "US-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "J&J — Pharma & Consumer Health"},
    "WMT": {"name": "Walmart", "kategorie": "US-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "Walmart Inc. — Einzelhandel"},
    "PG": {"name": "Procter & Gamble", "kategorie": "US-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "P&G — Konsumgüter"},
    "UNH": {"name": "UnitedHealth", "kategorie": "US-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "UnitedHealth Group — Krankenversicherung"},
    "HD": {"name": "Home Depot", "kategorie": "US-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "Home Depot — Baumarkt-Kette"},
    "MA": {"name": "Mastercard", "kategorie": "US-Aktie", "währung": "USD", "exchange": "NYSE", "beschreibung": "Mastercard Inc. — Zahlungsnetzwerk"},

    # ── SEKTOR-ETFs (weitere) ────────────────────────────────────────────────────
    "XLI": {"name": "Industrials Select Sector ETF", "kategorie": "US-ETF", "währung": "USD", "exchange": "NYSE", "beschreibung": "US-Industriesektor ETF"},
    "XLC": {"name": "Communication Services ETF", "kategorie": "US-ETF", "währung": "USD", "exchange": "NYSE", "beschreibung": "US-Kommunikationssektor ETF"},
    "XLB": {"name": "Materials Select Sector ETF", "kategorie": "US-ETF", "währung": "USD", "exchange": "NYSE", "beschreibung": "US-Grundstoffsektor ETF"},
    "XLP": {"name": "Consumer Staples Select ETF", "kategorie": "US-ETF", "währung": "USD", "exchange": "NYSE", "beschreibung": "US-Basiskonsumgüter ETF"},
    "XLY": {"name": "Consumer Discretionary ETF", "kategorie": "US-ETF", "währung": "USD", "exchange": "NYSE", "beschreibung": "US-Zyklische Konsumgüter ETF"},

    # ── ANLEIHEN / FIXED INCOME ──────────────────────────────────────────────────
    "SHY": {"name": "iShares 1-3Y Treasury ETF", "kategorie": "Anleihen", "währung": "USD", "exchange": "NYSE", "beschreibung": "Kurzläufer US-Staatsanleihen"},
    "IEF": {"name": "iShares 7-10Y Treasury ETF", "kategorie": "Anleihen", "währung": "USD", "exchange": "NYSE", "beschreibung": "Mittelfristige US-Staatsanleihen"},
    "HYG": {"name": "iShares High Yield Corp Bond", "kategorie": "Anleihen", "währung": "USD", "exchange": "NYSE", "beschreibung": "US High-Yield Unternehmensanleihen"},

    # ── EMERGING MARKETS ─────────────────────────────────────────────────────────
    "EEM": {"name": "iShares MSCI EM ETF", "kategorie": "Emerging Markets", "währung": "USD", "exchange": "NYSE", "beschreibung": "Schwellenländer ETF"},
    "FXI": {"name": "iShares China Large-Cap ETF", "kategorie": "Emerging Markets", "währung": "USD", "exchange": "NYSE", "beschreibung": "China Large-Cap ETF"},
    "EWZ": {"name": "iShares MSCI Brazil ETF", "kategorie": "Emerging Markets", "währung": "USD", "exchange": "NYSE", "beschreibung": "Brasilien ETF"},

    # ── WEITERE INDIZES ──────────────────────────────────────────────────────────
    "^SDAXI": {"name": "SDAX", "kategorie": "EU-Index", "währung": "EUR", "exchange": "XETRA", "beschreibung": "Small-Cap Deutsche Aktien"},
    "^TECDAX": {"name": "TecDAX", "kategorie": "EU-Index", "währung": "EUR", "exchange": "XETRA", "beschreibung": "Deutsche Technologie-Aktien"},
    "^IBEX": {"name": "IBEX 35", "kategorie": "EU-Index", "währung": "EUR", "exchange": "BME", "beschreibung": "Spanischer Leitindex"},

    # ── WEITERE ROHSTOFFE ────────────────────────────────────────────────────────
    "HG=F": {"name": "Copper Futures (Kupfer)", "kategorie": "Rohstoff", "währung": "USD", "exchange": "COMEX", "beschreibung": "Kupfer Futures ($/lb)"},
    "PL=F": {"name": "Platinum Futures (Platin)", "kategorie": "Rohstoff", "währung": "USD", "exchange": "NYMEX", "beschreibung": "Platin Futures ($/oz)"},
    "ZS=F": {"name": "Soybean Futures (Sojabohnen)", "kategorie": "Rohstoff", "währung": "USD", "exchange": "CBOT", "beschreibung": "Sojabohnen Futures"},

    # ── KRYPTOWÄHRUNGEN ────────────────────────────────────────────────────────
    "BTC-USD": {
        "name":         "Bitcoin (USD)",
        "kategorie":    "Krypto",
        "währung":      "USD",
        "exchange":     "Crypto",
        "beschreibung": "Bitcoin / US-Dollar",
    },
    "ETH-USD": {
        "name":         "Ethereum (USD)",
        "kategorie":    "Krypto",
        "währung":      "USD",
        "exchange":     "Crypto",
        "beschreibung": "Ethereum / US-Dollar",
    },
    "SOL-USD": {
        "name":         "Solana (USD)",
        "kategorie":    "Krypto",
        "währung":      "USD",
        "exchange":     "Crypto",
        "beschreibung": "Solana / US-Dollar",
    },

    "XRP-USD": {"name": "XRP (Ripple)", "kategorie": "Krypto", "währung": "USD", "exchange": "Crypto", "beschreibung": "XRP / US-Dollar"},
    "ADA-USD": {"name": "Cardano", "kategorie": "Krypto", "währung": "USD", "exchange": "Crypto", "beschreibung": "Cardano / US-Dollar"},
    "DOGE-USD": {"name": "Dogecoin", "kategorie": "Krypto", "währung": "USD", "exchange": "Crypto", "beschreibung": "Dogecoin / US-Dollar"},

    # ── FX / DEVISEN ───────────────────────────────────────────────────────────
    "EURUSD=X": {
        "name":         "EUR/USD",
        "kategorie":    "FX",
        "währung":      "USD",
        "exchange":     "Forex",
        "beschreibung": "Euro / US-Dollar Wechselkurs",
    },
    "GBPUSD=X": {
        "name":         "GBP/USD",
        "kategorie":    "FX",
        "währung":      "USD",
        "exchange":     "Forex",
        "beschreibung": "Britisches Pfund / US-Dollar",
    },
    "USDJPY=X": {
        "name":         "USD/JPY",
        "kategorie":    "FX",
        "währung":      "JPY",
        "exchange":     "Forex",
        "beschreibung": "US-Dollar / Japanischer Yen",
    },
    "USDCHF=X": {
        "name":         "USD/CHF",
        "kategorie":    "FX",
        "währung":      "CHF",
        "exchange":     "Forex",
        "beschreibung": "US-Dollar / Schweizer Franken",
    },
    "AUDUSD=X": {"name": "AUD/USD", "kategorie": "FX", "währung": "USD", "exchange": "Forex", "beschreibung": "Australischer Dollar / US-Dollar"},
    "NZDUSD=X": {"name": "NZD/USD", "kategorie": "FX", "währung": "USD", "exchange": "Forex", "beschreibung": "Neuseeland Dollar / US-Dollar"},
    "USDCAD=X": {"name": "USD/CAD", "kategorie": "FX", "währung": "CAD", "exchange": "Forex", "beschreibung": "US-Dollar / Kanadischer Dollar"},
}


# ── Konstanten ─────────────────────────────────────────────────────────────────

# Alle verfügbaren Kategorien (geordnet für Dropdowns)
KATEGORIEN = [
    "US-Index",
    "US-ETF",
    "US-Aktie",
    "EU-Index",
    "EU-Aktie",
    "Asien-Index",
    "Rohstoff",
    "Futures",
    "Anleihen",
    "Emerging Markets",
    "Krypto",
    "FX",
]

# Standard-Ticker
DEFAULT_SYMBOL = "SPY"


# ── Hilfsfunktionen ────────────────────────────────────────────────────────────

def get_symbols_by_category(kategorie: str) -> dict:
    """Gibt alle Symbole einer Kategorie zurück."""
    return {k: v for k, v in SYMBOLS.items() if v["kategorie"] == kategorie}


def get_all_tickers() -> list[str]:
    """Gibt alle Ticker-Symbole als sortierte Liste zurück."""
    return sorted(SYMBOLS.keys())


def get_display_name(ticker: str) -> str:
    """Gibt den Anzeigenamen für einen Ticker zurück.
    Fallback: Ticker selbst wenn nicht in SYMBOLS."""
    return SYMBOLS.get(ticker, {}).get("name", ticker)


def get_dropdown_label(ticker: str) -> str:
    """Gibt einen kombinierten Label für Streamlit-Dropdowns zurück.
    Format: 'SPY — SPDR S&P 500 ETF'"""
    name = get_display_name(ticker)
    return f"{ticker} — {name}"


def get_symbols_grouped() -> dict[str, dict]:
    """Gibt alle Symbole gruppiert nach Kategorie zurück.
    Nützlich für gruppierte Streamlit-Selectboxen."""
    grouped = {kat: {} for kat in KATEGORIEN}
    for ticker, info in SYMBOLS.items():
        kat = info["kategorie"]
        if kat in grouped:
            grouped[kat][ticker] = info
    # Leere Kategorien entfernen
    return {k: v for k, v in grouped.items() if v}


def search_symbols(query: str) -> dict:
    """Sucht Symbole nach Ticker oder Name (case-insensitive).
    Nützlich für eine Suchbox."""
    q = query.lower().strip()
    return {
        k: v for k, v in SYMBOLS.items()
        if q in k.lower() or q in v["name"].lower()
        or q in v.get("beschreibung", "").lower()
    }
