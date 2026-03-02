EU_COUNTRY_CODES = [
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", 
    "HU", "IE", "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", 
    "SI", "ES", "SE"
]
NOT_EU_COUNTRY_CODES = ['LI', 'TR', 'MK', 'NO', 'CH', 'GB']

def get_our_countries():
    lst = EU_COUNTRY_CODES.copy()
    lst.extend(NOT_EU_COUNTRY_CODES)
    return lst

# import pycountry
# EU_COUNTRY_NAMES_BY_CODE = {
#     code: pycountry.countries.get(alpha_2=code).name 
#     for code in EU_COUNTRY_CODES
# }
