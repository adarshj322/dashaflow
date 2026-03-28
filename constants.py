import swisseph as swe

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE,
}

ZODIAC_SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_LORDS = {
    "Aries": "Mars", "Taurus": "Venus", "Gemini": "Mercury", "Cancer": "Moon",
    "Leo": "Sun", "Virgo": "Mercury", "Libra": "Venus", "Scorpio": "Mars",
    "Sagittarius": "Jupiter", "Capricorn": "Saturn", "Aquarius": "Saturn", "Pisces": "Jupiter"
}

# Nakshatra lord sequence repeats 3 times to cover all 27
NAKSHATRA_LORD_SEQUENCE = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"
]

NAKSHATRAS = [
    {"name": "Ashwini",        "lord": "Ketu"},
    {"name": "Bharani",        "lord": "Venus"},
    {"name": "Krittika",       "lord": "Sun"},
    {"name": "Rohini",         "lord": "Moon"},
    {"name": "Mrigashira",     "lord": "Mars"},
    {"name": "Ardra",          "lord": "Rahu"},
    {"name": "Punarvasu",      "lord": "Jupiter"},
    {"name": "Pushya",         "lord": "Saturn"},
    {"name": "Ashlesha",       "lord": "Mercury"},
    {"name": "Magha",          "lord": "Ketu"},
    {"name": "Purva Phalguni", "lord": "Venus"},
    {"name": "Uttara Phalguni","lord": "Sun"},
    {"name": "Hasta",          "lord": "Moon"},
    {"name": "Chitra",         "lord": "Mars"},
    {"name": "Swati",          "lord": "Rahu"},
    {"name": "Vishakha",       "lord": "Jupiter"},
    {"name": "Anuradha",       "lord": "Saturn"},
    {"name": "Jyeshtha",       "lord": "Mercury"},
    {"name": "Mula",           "lord": "Ketu"},
    {"name": "Purva Ashadha",  "lord": "Venus"},
    {"name": "Uttara Ashadha", "lord": "Sun"},
    {"name": "Shravana",       "lord": "Moon"},
    {"name": "Dhanishta",      "lord": "Mars"},
    {"name": "Shatabhisha",    "lord": "Rahu"},
    {"name": "Purva Bhadrapada","lord": "Jupiter"},
    {"name": "Uttara Bhadrapada","lord": "Saturn"},
    {"name": "Revati",         "lord": "Mercury"},
]

NAK_SPAN = 360.0 / 27.0  # 13.33333... degrees per nakshatra
PADA_SPAN = NAK_SPAN / 4.0  # 3.33333... degrees per pada

# ==========================================
# VIMSHOTTARI DASHA
# ==========================================
VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
}
VIMSHOTTARI_TOTAL = 120.0

DASHA_SEQUENCE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

# ==========================================
# PLANETARY DIGNITY (per BPHS)
# ==========================================

# (sign_name, deep_exaltation_degree)
EXALTATION = {
    "Sun":     ("Aries", 10),
    "Moon":    ("Taurus", 3),
    "Mars":    ("Capricorn", 28),
    "Mercury": ("Virgo", 15),
    "Jupiter": ("Cancer", 5),
    "Venus":   ("Pisces", 27),
    "Saturn":  ("Libra", 20),
    "Rahu":    ("Taurus", 20),
    "Ketu":    ("Scorpio", 20),
}

DEBILITATION = {
    "Sun":     ("Libra", 10),
    "Moon":    ("Scorpio", 3),
    "Mars":    ("Cancer", 28),
    "Mercury": ("Pisces", 15),
    "Jupiter": ("Capricorn", 5),
    "Venus":   ("Virgo", 27),
    "Saturn":  ("Aries", 20),
    "Rahu":    ("Scorpio", 20),
    "Ketu":    ("Taurus", 20),
}

OWN_SIGNS = {
    "Sun":     ["Leo"],
    "Moon":    ["Cancer"],
    "Mars":    ["Aries", "Scorpio"],
    "Mercury": ["Gemini", "Virgo"],
    "Jupiter": ["Sagittarius", "Pisces"],
    "Venus":   ["Taurus", "Libra"],
    "Saturn":  ["Capricorn", "Aquarius"],
    "Rahu":    ["Aquarius"],
    "Ketu":    ["Scorpio"],
}

# (sign, start_degree, end_degree) -- per BPHS
# Mooltrikona ranges per B.V. Raman (Hindu Predictive Astrology).
# Note: Pure BPHS has slightly narrower ranges for Moon(4-20), Mars(0-12),
# Jupiter(0-10), Venus(0-5). Raman's expanded ranges are used here for
# compatibility with VedAstro and most modern Vedic software.
MOOLTRIKONA = {
    "Sun":     ("Leo", 0, 20),
    "Moon":    ("Taurus", 4, 30),
    "Mars":    ("Aries", 0, 18),
    "Mercury": ("Virgo", 16, 20),
    "Jupiter": ("Sagittarius", 0, 13),
    "Venus":   ("Libra", 0, 10),
    "Saturn":  ("Aquarius", 0, 20),
}

# ==========================================
# PLANETARY RELATIONSHIPS (BPHS natural/permanent)
# ==========================================
NATURAL_FRIENDS = {
    "Sun":     ["Moon", "Mars", "Jupiter"],
    "Moon":    ["Sun", "Mercury"],
    "Mars":    ["Sun", "Moon", "Jupiter"],
    "Mercury": ["Sun", "Venus"],
    "Jupiter": ["Sun", "Moon", "Mars"],
    "Venus":   ["Mercury", "Saturn"],
    "Saturn":  ["Mercury", "Venus"],
    "Rahu":    ["Mercury", "Venus", "Saturn"],
    "Ketu":    ["Mars", "Jupiter"],
}

NATURAL_ENEMIES = {
    "Sun":     ["Venus", "Saturn"],
    "Moon":    [],
    "Mars":    ["Mercury"],
    "Mercury": ["Moon"],
    "Jupiter": ["Mercury", "Venus"],
    "Venus":   ["Sun", "Moon"],
    "Saturn":  ["Sun", "Moon", "Mars"],
    "Rahu":    ["Sun", "Moon", "Mars"],
    "Ketu":    ["Mercury", "Venus"],
}

# Planets not in friends or enemies are neutral
NATURAL_NEUTRALS = {
    "Sun":     ["Mercury"],
    "Moon":    ["Mars", "Jupiter", "Venus", "Saturn"],
    "Mars":    ["Venus", "Saturn"],
    "Mercury": ["Mars", "Jupiter", "Saturn"],
    "Jupiter": ["Saturn"],
    "Venus":   ["Mars", "Jupiter"],
    "Saturn":  ["Jupiter"],
    "Rahu":    ["Jupiter"],
    "Ketu":    ["Sun", "Moon", "Saturn"],
}

# ==========================================
# COMBUSTION ORBS (degrees from Sun)
# ==========================================
COMBUSTION_ORBS = {
    "Moon": 12,
    "Mars": 17,
    "Mercury": {"direct": 14, "retrograde": 12},
    "Jupiter": 11,
    "Venus": {"direct": 10, "retrograde": 8},
    "Saturn": 15,
}

# ==========================================
# PANCHANG NAMES
# ==========================================
TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya",
]

VARA_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
VARA_LORDS = ["Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun"]

PANCHANG_YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda",
    "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
    "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
    "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma",
    "Indra", "Vaidhriti",
]

KARANA_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Garija",
    "Vanija", "Vishti", "Shakuni", "Chatushpada", "Nagava", "Kimstughna"
]

# ==========================================
# DIGBALA (directional strength)
# Houses where planets gain Digbala (1-indexed)
# ==========================================
DIGBALA_HOUSES = {
    "Jupiter": 1,
    "Mercury": 1,
    "Sun": 10,
    "Mars": 10,
    "Saturn": 7,
    "Moon": 4,
    "Venus": 4,
}
