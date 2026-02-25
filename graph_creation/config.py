import pycountry

# 27 EU member state ISO Alpha-2 codes and Great Britain
EU_COUNTRY_CODES = [
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", 
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", 
    "SI", "ES", "SE", "GB"
]
EU_COUNTRY_NAMES_BY_CODE = {
    code: pycountry.countries.get(alpha_2=code).name 
    for code in EU_COUNTRY_CODES
}


