import os

GEMINI_API_KEY = ""

SECTOR_UNIVERSES = {
    "digital_infrastructure": ["EQIX","DLR","AMT","CCI","SBAC","IRM","QTS","CONE","UNIT","LUMN","CSCO","JNPR","NTAP","PSTG","SMAR"],
    "software":               ["ADBE","CRM","NOW","WDAY","VEEV","DDOG","MDB","SNOW","ZS","OKTA","HUBS","BILL","GTLB","DOMO","APPF"],
    "healthcare":             ["ISRG","IDXX","HOLX","TECH","MMSI","ABIOMED","NUVA","OFIX","ATRC","NVCR"],
    "industrials":            ["HON","GE","MMM","EMR","ROK","CARR","TT","IR","FWRD","XPO"],
    "financial_services":     ["LPLA","RJF","SEIC","VRTS","APAM","WEX","EVTC","RPAY","FOUR","PAYO"],
    "energy":                 ["VTLE","CHRD","SM","CIVI","SOC","RRC","MTDR","CTRA","GPOR","ESTE"],
    "consumer_discretionary": ["RVLV","BOOT","PLNT","WING","MODG","DOCN","TXRH","SHAK","PLAY","SBH"],
    "consumer_staples":       ["POST","COTY","CENT","FRPT","PFGC","CHEF","COKE","NOMD","HIMS","ELAN"],
    "communication_services": ["ZETA","GENI","MGNI","LSXMA","IHRT","YELP","TDC","BMBL","MTCH","ANGI"],
    "materials":              ["AZEK","TREX","UFPI","SLVM","KRO","LAUR","PGTI","APOG","JELD","AMWD"],
    "utilities":              ["NWE","SPWR","CLNE","PNM","GPLE","AVA","MGEE","NWPX","OTTR","ELLO"],
    "real_estate":            ["ROIC","IIPR","STAG","COLD","SAFE","ELME","NXRT","GMRE","ILPT","PLYM"],
}

SCORING_WEIGHTS = {
    "valuation":     0.25,
    "profitability": 0.25,
    "leverage":      0.20,
    "growth":        0.15,
    "scale":         0.15,
}

TARGET_MARKET_CAP_MIN_B = 0.5
TARGET_MARKET_CAP_MAX_B = 30.0
TOP_N_TARGETS     = 5
OUTPUT_DIR        = "output"
TEARSHEET_PREFIX  = "tearsheet"
SUMMARY_FILENAME  = "ma_target_summary.xlsx"
