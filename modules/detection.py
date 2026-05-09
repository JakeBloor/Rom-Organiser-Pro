import re
from config import SYSTEM_MAP

DISC_REGEX = re.compile(r"(disc|disk|cd)[\s_-]*(\d+)", re.I)

ARCADE_KEYWORDS = [
    "arcade",
    "fbneo",
    "mame"
]


def clean_name(name):
    name = DISC_REGEX.sub("", name)
    name = re.sub(r"\(.*?\)|\[.*?\]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()



def get_disc_number(name):
    m = DISC_REGEX.search(name)
    return int(m.group(2)) if m else None



def detect_arcade(path):
    p = str(path).lower()

    for keyword in ARCADE_KEYWORDS:
        if keyword in p:
            return "fbneo"

    return None



def detect_system(file_path):
    arcade = detect_arcade(file_path)

    if arcade:
        return arcade

    return SYSTEM_MAP.get(file_path.suffix.lower())