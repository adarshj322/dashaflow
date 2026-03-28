from constants import ZODIAC_SIGNS, SIGN_LORDS, NATURAL_FRIENDS, NATURAL_ENEMIES
from nakshatra import get_nakshatra
import math

# --- Data Tables ---
# 0-26 indexed Nakshatras
YONI_ANIMALS = [
    "Horse", "Elephant", "Sheep", "Serpent", "Serpent", "Dog", "Cat", "Sheep", "Cat", # 0-8
    "Rat", "Rat", "Cow", "Buffalo", "Tiger", "Buffalo", "Tiger", "Deer", "Deer", # 9-17
    "Dog", "Monkey", "Mongoose", "Monkey", "Lion", "Horse", "Lion", "Cow", "Elephant" # 18-26
]

YONI_ENEMIES = {
    "Horse": "Buffalo", "Buffalo": "Horse",
    "Elephant": "Lion", "Lion": "Elephant",
    "Sheep": "Monkey", "Monkey": "Sheep",
    "Serpent": "Mongoose", "Mongoose": "Serpent",
    "Dog": "Deer", "Deer": "Dog",
    "Cat": "Rat", "Rat": "Cat",
    "Cow": "Tiger", "Tiger": "Cow"
}

GANA = [
    "Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", "Deva", "Deva", "Rakshasa",
    "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Deva", "Rakshasa", "Deva", "Rakshasa",
    "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva"
]

NADI = [
    "Adi", "Madhya", "Antya", "Antya", "Madhya", "Adi", "Adi", "Madhya", "Antya",
    "Antya", "Madhya", "Adi", "Adi", "Madhya", "Antya", "Antya", "Madhya", "Adi",
    "Adi", "Madhya", "Antya", "Antya", "Madhya", "Adi", "Adi", "Madhya", "Antya"
]

VARNA = {
    "Cancer": 1, "Scorpio": 1, "Pisces": 1, # Brahmin
    "Aries": 2, "Leo": 2, "Sagittarius": 2, # Kshatriya
    "Taurus": 3, "Virgo": 3, "Capricorn": 3, # Vaishya
    "Gemini": 4, "Libra": 4, "Aquarius": 4 # Shudra
}

# 1. Varna (1 point)
def calc_varna(m_sign, f_sign):
    m_varna = VARNA[m_sign]
    f_varna = VARNA[f_sign]
    return 1.0 if m_varna <= f_varna else 0.0

# 2. Vashya (2 points) — Full BPHS classification
# Sign categories: Chatushpada (quadruped), Manava (human), Jalachara (water),
# Vanachara (wild/forest), Keet (insect/reptile)
VASHYA_TYPE = {
    "Aries": "Chatushpada", "Taurus": "Chatushpada",
    "Leo": "Vanachara", "Sagittarius": "Chatushpada",  # 2nd half is Manava
    "Capricorn": "Chatushpada",  # 1st half is Chatushpada
    "Gemini": "Manava", "Virgo": "Manava", "Libra": "Manava",
    "Aquarius": "Manava",  # 1st half is Manava
    "Cancer": "Jalachara", "Pisces": "Jalachara",
    "Scorpio": "Keet",
}

# Vashya compatibility scoring matrix
VASHYA_MATRIX = {
    ("Chatushpada", "Chatushpada"): 2.0,
    ("Manava", "Manava"): 2.0,
    ("Jalachara", "Jalachara"): 2.0,
    ("Vanachara", "Vanachara"): 2.0,
    ("Keet", "Keet"): 2.0,
    ("Chatushpada", "Manava"): 0.5,
    ("Manava", "Chatushpada"): 0.5,
    ("Manava", "Jalachara"): 1.0,
    ("Jalachara", "Manava"): 1.0,
    ("Chatushpada", "Jalachara"): 0.5,
    ("Jalachara", "Chatushpada"): 0.5,
    ("Vanachara", "Chatushpada"): 0.0,  # Wild eats quadruped
    ("Chatushpada", "Vanachara"): 0.0,
    ("Keet", "Chatushpada"): 0.0,
    ("Chatushpada", "Keet"): 0.0,
    ("Vanachara", "Manava"): 0.5,
    ("Manava", "Vanachara"): 0.5,
    ("Keet", "Manava"): 0.5,
    ("Manava", "Keet"): 0.5,
    ("Vanachara", "Jalachara"): 0.5,
    ("Jalachara", "Vanachara"): 0.5,
    ("Keet", "Jalachara"): 1.0,
    ("Jalachara", "Keet"): 1.0,
    ("Vanachara", "Keet"): 1.0,
    ("Keet", "Vanachara"): 1.0,
}

def calc_vashya(m_sign, f_sign):
    if m_sign == f_sign:
        return 2.0
    m_type = VASHYA_TYPE.get(m_sign, "Manava")
    f_type = VASHYA_TYPE.get(f_sign, "Manava")
    return VASHYA_MATRIX.get((m_type, f_type), 1.0)

# 3. Tara (3 points)
def calc_tara(m_nak_idx, f_nak_idx):
    m_to_f = (f_nak_idx - m_nak_idx) % 9
    f_to_m = (m_nak_idx - f_nak_idx) % 9
    pts = 0.0
    if m_to_f not in (2, 4, 6): pts += 1.5
    if f_to_m not in (2, 4, 6): pts += 1.5
    return pts

# 4. Yoni (4 points)
def calc_yoni(m_nak_idx, f_nak_idx):
    m_yoni = YONI_ANIMALS[m_nak_idx]
    f_yoni = YONI_ANIMALS[f_nak_idx]
    if m_yoni == f_yoni:
        return 4.0
    if YONI_ENEMIES.get(m_yoni) == f_yoni:
        return 0.0
    return 2.0 # Neutral

# 5. Graha Maitri (5 points)
def check_friendship(p1, p2):
    if p1 == p2:
        return 1.0 # Same lord
    if p2 in NATURAL_FRIENDS.get(p1, []):
        return 1.0
    if p2 in NATURAL_ENEMIES.get(p1, []):
        return 0.0
    return 0.5 # Neutral

def calc_graha_maitri(m_sign, f_sign):
    m_lord = SIGN_LORDS[m_sign]
    f_lord = SIGN_LORDS[f_sign]
    m_to_f = check_friendship(m_lord, f_lord)
    f_to_m = check_friendship(f_lord, m_lord)
    
    total = m_to_f + f_to_m
    if total == 2.0: return 5.0
    if total == 1.5: return 4.0
    if total == 1.0: return 3.0
    if total == 0.5: return 1.0
    return 0.0

# 6. Gana (6 points)
def calc_gana(m_nak_idx, f_nak_idx):
    m_gana = GANA[m_nak_idx]
    f_gana = GANA[f_nak_idx]
    if m_gana == f_gana: return 6.0
    if m_gana == "Deva" and f_gana == "Manushya": return 6.0
    if m_gana == "Manushya" and f_gana == "Deva": return 5.0
    if m_gana == "Rakshasa" and f_gana == "Manushya": return 0.0
    if f_gana == "Rakshasa" and m_gana == "Manushya": return 0.0
    if m_gana == "Rakshasa" and f_gana == "Deva": return 1.0
    if f_gana == "Rakshasa" and m_gana == "Deva": return 0.0
    return 0.0

# 7. Bhakoot (7 points)
def calc_bhakoot(m_sign, f_sign):
    m_idx = ZODIAC_SIGNS.index(m_sign)
    f_idx = ZODIAC_SIGNS.index(f_sign)
    diff = (f_idx - m_idx) % 12 + 1
    if diff in (1, 7, 3, 11, 4, 10):
        return 7.0
    return 0.0

# 8. Nadi (8 points)
def calc_nadi(m_nak_idx, f_nak_idx):
    m_nadi = NADI[m_nak_idx]
    f_nadi = NADI[f_nak_idx]
    if m_nadi != f_nadi:
        return 8.0
    return 0.0 # Nadi Dosha

def calculate_ashtakoot(male_moon_lon: float, female_moon_lon: float):
    """
    Calculates the 36-point Ashtakoot compatibility matching.
    """
    m_nak = get_nakshatra(male_moon_lon)
    f_nak = get_nakshatra(female_moon_lon)
    m_nak_idx = m_nak["index"]
    f_nak_idx = f_nak["index"]
    
    m_sign_idx = int((male_moon_lon % 360) / 30)
    f_sign_idx = int((female_moon_lon % 360) / 30)
    m_sign = ZODIAC_SIGNS[m_sign_idx]
    f_sign = ZODIAC_SIGNS[f_sign_idx]

    scores = {
        "Varna": calc_varna(m_sign, f_sign),
        "Vashya": calc_vashya(m_sign, f_sign),
        "Tara": calc_tara(m_nak_idx, f_nak_idx),
        "Yoni": calc_yoni(m_nak_idx, f_nak_idx),
        "GrahaMaitri": calc_graha_maitri(m_sign, f_sign),
        "Gana": calc_gana(m_nak_idx, f_nak_idx),
        "Bhakoot": calc_bhakoot(m_sign, f_sign),
        "Nadi": calc_nadi(m_nak_idx, f_nak_idx),
    }
    
    total_score = sum(scores.values())
    
    return {
        "male_details": {
            "moon_sign": m_sign,
            "nakshatra": m_nak["name"],
            "gana": GANA[m_nak_idx],
            "nadi": NADI[m_nak_idx],
            "yoni": YONI_ANIMALS[m_nak_idx]
        },
        "female_details": {
            "moon_sign": f_sign,
            "nakshatra": f_nak["name"],
            "gana": GANA[f_nak_idx],
            "nadi": NADI[f_nak_idx],
            "yoni": YONI_ANIMALS[f_nak_idx]
        },
        "scores": scores,
        "total_score": total_score,
        "max_score": 36.0,
        "is_match_approved": total_score >= 18.0 and scores["Nadi"] > 0
    }
