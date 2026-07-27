"""
Univers de tickers utilisés par les Relative Rotation Graphs (RRG).
"""

SPY_TICKER = "SPY"

# ─────────────────────────────────────────────
#  SECTEURS US
# ─────────────────────────────────────────────

TICKERS_SECTOR_US = {
    "XLK": "Technologie",
    "XLV": "Santé",
    "XLF": "Finance",
    "XLI": "Industrie",
    "XLY": "Conso. Discrétionnaire",
    "XLP": "Conso. de Base",
    "XLB": "Matériaux",
    "XLE": "Énergie",
    "XLU": "Utilities",
    "XLC": "Télécom",
}

TICKERS_TECH_GRANULAR = {
    "IGV":  "Software",
    "CLOU": "Cloud",
    "SKYY": "Cloud (alt)",
    "SOXX": "Semiconductors",
    "SMH":  "Semiconductors (alt)",
    "XSD":  "Semiconductors EW",
    "FDN":  "Internet",
    "IYW":  "Tech broad",
}

TICKERS_FINANCE_GRANULAR = {
    "KBE":  "Banks",
    "KRE":  "Regional Banks",
    "IAI":  "Broker-Dealers",
    "KIE":  "Insurance",
    "KBWB": "Banks (large cap)",
}

TICKERS_HEALTH_GRANULAR = {
    "IHI":  "Medical Devices",
    "IBB":  "Biotech",
    "XBI":  "Biotech EW",
    "IHF":  "Healthcare Providers",
    "PJP":  "Pharma",
}

TICKERS_ENERGY_GRANULAR = {
    "OIH":  "Oil Services",
    "XOP":  "E&P",
    "AMLP": "Midstream / MLP",
    "FCG":  "Natural Gas",
}

TICKERS_INDUSTRY_GRANULAR = {
    "ITA":  "Aerospace & Defense",
    "XTN":  "Transportation",
    "PAVE": "Infrastructure",
    "XHB":  "Homebuilders",
}

TICKERS_DISCRETIONARY_GRANULAR = {
    "XRT":  "Retail",
    "JETS": "Airlines",
    "IBUY": "Online Retail",
    "CARZ": "Auto",
}

TICKERS_MATERIALS_GRANULAR = {
    "PICK": "Metals & Mining",
    "LIT":  "Lithium & Battery",
    "REMX": "Rare Earth",
    "WOOD": "Timber & Forestry",
}

# Maps sector ETF ticker -> sous-dict granulaire
TICKERS_GRANULAR_US = {
    "XLK": TICKERS_TECH_GRANULAR,
    "XLF": TICKERS_FINANCE_GRANULAR,
    "XLV": TICKERS_HEALTH_GRANULAR,
    "XLE": TICKERS_ENERGY_GRANULAR,
    "XLI": TICKERS_INDUSTRY_GRANULAR,
    "XLY": TICKERS_DISCRETIONARY_GRANULAR,
    "XLB": TICKERS_MATERIALS_GRANULAR,
}

# ─────────────────────────────────────────────
#  SECTEURS EUROPE
# ─────────────────────────────────────────────

TICKERS_SECTOR_EUROPE = {
    "QDVE.DE": "Technologie",
    "QDVG.DE": "Santé",
    "QDVH.DE": "Finance",
    "QDVF.DE": "Énergie",
    "IMSU.L":  "Matériaux",
    "IUSU.L":  "Utilities",
}

TICKERS_TECH_EU_GRANULAR = {
    "IITU.L":  "MSCI Europe IT",
    "ROBO.L":  "Robotics & Automation",
    "VVSM.DE": "Semiconductors",
}

TICKERS_HEALTH_EU_GRANULAR = {
    "EXV8.DE": "Healthcare",
    "EXV7.DE": "Food & Beverage",
    "IH2O.L":  "Water / Utilities-health crossover",
}

TICKERS_FINANCE_EU_GRANULAR = {
    "EXV2.DE": "Banks",
    "EXV6.DE": "Financial Services",
    "EUFN":    "Europe Financials (US ETF)",
}

TICKERS_ENERGY_EU_GRANULAR = {
    "EXH4.DE": "Oil & Gas",
    "IQQH.DE": "Clean Energy",
    "EXV9.DE": "Industrials",
}

TICKERS_MATERIALS_EU_GRANULAR = {
    "EXV3.DE": "Basic Resources",
    "EXV4.DE": "Chemicals",
    "EXV5.DE": "Construction & Materials",
}

TICKERS_UTILITIES_EU_GRANULAR = {
    "EXH6.DE": "Utilities",
    "IQQH.DE": "Clean Energy",
    "EXV1.DE": "Telecom",
}

# Maps sector ETF ticker -> sous-dict granulaire (Europe)
TICKERS_GRANULAR_EU = {
    "QDVE.DE": TICKERS_TECH_EU_GRANULAR,
    "QDVG.DE": TICKERS_HEALTH_EU_GRANULAR,
    "QDVH.DE": TICKERS_FINANCE_EU_GRANULAR,
    "QDVF.DE": TICKERS_ENERGY_EU_GRANULAR,
    "IMSU.L":  TICKERS_MATERIALS_EU_GRANULAR,
    "IUSU.L":  TICKERS_UTILITIES_EU_GRANULAR,
}

# ─────────────────────────────────────────────
#  FACTEURS US — organisés en oppositions
# ─────────────────────────────────────────────

TICKERS_FACTOR_US = {
    "MTUM": "Momentum",
    "VLUE": "Value",
    "QUAL": "Quality",
    "USMV": "Low Volatility",
    "SIZE": "Size",
    "IWF":  "Growth",
    "SPHB": "High Beta",
}

# Chaque thème = une paire (ou trio) de facteurs qu'on met en opposition sur
# le même RRG, ex: Value vs Growth. L'ordre des tickers n'a pas d'importance.
TICKERS_FACTOR_THEMES = {
    "Value vs Growth":               ["VLUE", "IWF"],
    "Quality vs Value":               ["QUAL", "VLUE"],
    "Momentum vs Low Volatility":     ["MTUM", "USMV"],
    "High Beta vs Low Volatility":    ["SPHB", "USMV"],
    "Quality vs High Beta":           ["QUAL", "SPHB"],
    "Size vs Quality":                ["SIZE", "QUAL"],
}