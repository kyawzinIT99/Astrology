"""
Myanmar Calendar Engine — Pure Python implementation.

Ported from the Cool Emerald / Yan Naing Aye algorithm:
  https://cool-emerald.blogspot.com/2013/06/algorithm-program-and-calculation-of.html
  https://github.com/yan9a/mmcal

This module converts Gregorian dates to Myanmar calendar dates,
including Myanmar year, month, day, moon phase, and weekday.
All calculations use Julian Day Numbers internally.
"""

import math
from dataclasses import dataclass
from typing import Optional

# ─── Constants ────────────────────────────────────────────────────────────────
SY = 1577917828 / 4320000      # Solar year = 365.2587565 days
LM = 1577917828 / 53433336     # Lunar month = 29.53058795 days
MO = 1954168.050623            # Beginning of 0 ME (Julian Day)
SG = 2361222                   # Gregorian calendar start (English: 1752/Sep/14)

# ─── Era Definitions ─────────────────────────────────────────────────────────
ERAS = [
    # Era 1.1: Makaranta system 1 (ME 0 – 797)
    {
        "eid": 1.1, "begin": -999, "end": 797,
        "WO": -1.1, "NM": -1,
        "fme": [[205,1],[246,1],[471,1],[572,-1],[651,1],[653,2],[656,1],[672,1],[729,1],[767,-1]],
        "wte": []
    },
    # Era 1.2: Makaranta system 2 (ME 798 – 1099)
    {
        "eid": 1.2, "begin": 798, "end": 1099,
        "WO": -1.1, "NM": -1,
        "fme": [[813,-1],[849,-1],[851,-1],[854,-1],[927,-1],[933,-1],[936,-1],
                [938,-1],[949,-1],[952,-1],[963,-1],[968,-1],[1039,-1]],
        "wte": []
    },
    # Era 1.3: Thandeikta (ME 1100 – 1216)
    {
        "eid": 1.3, "begin": 1100, "end": 1216,
        "WO": -0.85, "NM": -1,
        "fme": [[1120,1],[1126,-1],[1150,1],[1172,-1],[1207,1]],
        "wte": [[1201,1],[1202,0]]
    },
    # Era 2: British colony (ME 1217 – 1311)
    {
        "eid": 2, "begin": 1217, "end": 1311,
        "WO": -1, "NM": 4,
        "fme": [[1234,1],[1261,-1]],
        "wte": [[1263,1],[1264,0]]
    },
    # Era 3: After Independence (ME 1312+)
    {
        "eid": 3, "begin": 1312, "end": 9999,
        "WO": -0.5, "NM": 8,
        "fme": [[1377,1]],
        "wte": [[1344,1],[1345,0]]
    },
]

# ─── Myanmar month/weekday names ─────────────────────────────────────────────
MYANMAR_MONTHS = {
    0: "ပထမ ဝါဆို",   # First Waso
    1: "တန်ခူး",       # Tagu
    2: "ကဆုန်",        # Kason
    3: "နယုန်",        # Nayon
    4: "ဝါဆို",        # (2nd) Waso
    5: "ဝါခေါင်",      # Wagaung
    6: "တော်သလင်း",    # Tawthalin
    7: "သီတင်းကျွတ်",  # Thadingyut
    8: "တန်ဆောင်မုန်း", # Tazaungmon
    9: "နတ်တော်",       # Nadaw
    10: "ပြာသို",       # Pyatho
    11: "တပို့တွဲ",     # Tabodwe
    12: "တပေါင်း",      # Tabaung
}

MOON_PHASES = {
    0: "လဆန်း",     # Waxing
    1: "လပြည့်",     # Full Moon
    2: "လဆုတ်",     # Waning
    3: "လကွယ်",     # New Moon
}

WEEKDAYS_MM = ["စနေ", "တနင်္ဂနွေ", "တနင်္လာ", "အင်္ဂါ", "ဗုဒ္ဓဟူး", "ကြာသပတေး", "သောကြာ"]
# wd: 0=Sat, 1=Sun, 2=Mon, 3=Tue, 4=Wed, 5=Thu, 6=Fri

WEEKDAYS_EN = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


# ─── Data Classes ─────────────────────────────────────────────────────────────
@dataclass
class MyanmarDate:
    """Represents a full Myanmar calendar date."""
    myanmar_year: int          # Myanmar Era year
    year_type: int             # 0=common, 1=little watat, 2=big watat
    year_length: int           # 354, 384, or 385 days
    month: int                 # 0=1st Waso, 1=Tagu .. 12=Tabaung
    month_type: int            # 1=hnaung, 0=oo
    month_length: int          # 29 or 30 days
    month_day: int             # 1-30
    fortnight_day: int         # 1-15
    moon_phase: int            # 0=waxing, 1=full, 2=waning, 3=new
    weekday: int               # 0=sat, 1=sun .. 6=fri

    @property
    def month_name(self) -> str:
        return MYANMAR_MONTHS.get(self.month, "")

    @property
    def moon_phase_name(self) -> str:
        return MOON_PHASES.get(self.moon_phase, "")

    @property
    def weekday_name(self) -> str:
        return WEEKDAYS_MM[self.weekday]

    @property
    def weekday_en(self) -> str:
        return WEEKDAYS_EN[self.weekday]

    @property
    def display(self) -> str:
        """Full Myanmar date string."""
        return (
            f"မြန်မာသက္ကရာဇ် {self.myanmar_year} ခုနှစ်၊ "
            f"{self.month_name}လ {self.moon_phase_name} "
            f"{self.fortnight_day} ရက်၊ {self.weekday_name}နေ့"
        )


# ─── Helper Functions ─────────────────────────────────────────────────────────
def _bsearch(key: int, arr: list) -> int:
    """Binary search in a sorted 2D list by first element. Returns index or -1."""
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid][0] == key:
            return mid
        elif arr[mid][0] < key:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


# ─── Gregorian ↔ Julian Day Number ────────────────────────────────────────────
def w2j(y: int, m: int, d: int, ct: int = 0) -> int:
    """
    Western (Gregorian/Julian) date to Julian Day Number.
    ct: 0=English (default), 1=Gregorian, 2=Julian
    """
    a = math.floor((14 - m) / 12)
    y = y + 4800 - a
    m = m + (12 * a) - 3
    jd = d + math.floor((153 * m + 2) / 5) + (365 * y) + math.floor(y / 4)
    if ct == 1:
        jd = jd - math.floor(y / 100) + math.floor(y / 400) - 32045
    elif ct == 2:
        jd = jd - 32083
    else:
        jd = jd - math.floor(y / 100) + math.floor(y / 400) - 32045
        if jd < SG:
            jd = d + math.floor((153 * m + 2) / 5) + (365 * y) + math.floor(y / 4) - 32083
            if jd > SG:
                jd = SG
    return jd


def j2w(jd: float) -> dict:
    """
    Julian Day Number to Western date.
    Returns dict with y, m, d, h, n, s.
    """
    j = math.floor(jd + 0.5)
    jf = jd + 0.5 - j

    if jd < SG:
        b = j + 1524
        c = math.floor((b - 122.1) / 365.25)
        f = math.floor(365.25 * c)
        e = math.floor((b - f) / 30.6001)
        m = (e - 13) if e > 13 else (e - 1)
        d = b - f - math.floor(30.6001 * e)
        y = (c - 4715) if m < 3 else (c - 4716)
    else:
        j -= 1721119
        y = math.floor((4 * j - 1) / 146097)
        j = 4 * j - 1 - 146097 * y
        d = math.floor(j / 4)
        j = math.floor((4 * d + 3) / 1461)
        d = 4 * d + 3 - 1461 * j
        d = math.floor((d + 4) / 4)
        m = math.floor((5 * d - 3) / 153)
        d = 5 * d - 3 - 153 * m
        d = math.floor((d + 5) / 5)
        y = 100 * y + j
        if m < 10:
            m += 3
        else:
            m -= 9
            y += 1

    jf *= 24
    h = math.floor(jf)
    jf = (jf - h) * 60
    n = math.floor(jf)
    s = (jf - n) * 60

    return {"y": y, "m": m, "d": d, "h": h, "n": n, "s": s}


# ─── Myanmar Year Checks ─────────────────────────────────────────────────────
def chk_watat(my: int) -> dict:
    """
    Check intercalary month (watat) for a Myanmar year.
    Returns: {fm: full moon day of 2nd Waso (JDN), watat: 0 or 1}
    """
    # Select the correct era
    era = ERAS[0]
    for i in range(len(ERAS) - 1, 0, -1):
        if my >= ERAS[i]["begin"]:
            era = ERAS[i]
            break

    NM = era["NM"]
    WO = era["WO"]
    TA = (SY / 12 - LM) * (12 - NM)   # threshold to adjust
    ed = (SY * (my + 3739)) % LM        # excess day

    if ed < TA:
        ed += LM  # adjust excess days

    fm = round(SY * my + MO - ed + 4.5 * LM + WO)  # full moon day of 2nd Waso

    TW = 0
    watat = 0

    if era["eid"] >= 2:
        # 2nd era or later: find watat based on excess days
        TW = LM - (SY / 12 - LM) * NM
        if ed >= TW:
            watat = 1
    else:
        # 1st era: watat by 19-year metonic cycle
        watat = (my * 7 + 2) % 19
        if watat < 0:
            watat += 19
        watat = math.floor(watat / 12)

    # Correct watat exceptions
    idx = _bsearch(my, era["wte"])
    if idx >= 0:
        watat = era["wte"][idx][1]

    # Correct full moon day exceptions
    if watat:
        idx = _bsearch(my, era["fme"])
        if idx >= 0:
            fm += era["fme"][idx][1]

    return {"fm": fm, "watat": watat}


def chk_my(my: int) -> dict:
    """
    Full Myanmar year check.
    Returns: {myt: year type (0=common, 1=little watat, 2=big watat),
              tg1: first day of Tagu (JDN), fm: full moon day (JDN), werr: watat error}
    """
    yd = 0
    fm = 0
    werr = 0

    y2 = chk_watat(my)
    myt = y2["watat"]

    # Find nearest watat year before this year
    while True:
        yd += 1
        y1 = chk_watat(my - yd)
        if y1["watat"] != 0 or yd >= 3:
            break

    if myt:
        nd = (y2["fm"] - y1["fm"]) % 354
        myt = math.floor(nd / 31) + 1
        fm = y2["fm"]
        if nd != 30 and nd != 31:
            werr = 1
    else:
        fm = y1["fm"] + 354 * yd

    tg1 = y1["fm"] + 354 * yd - 102

    return {"myt": myt, "tg1": tg1, "fm": fm, "werr": werr}


# ─── Julian Day Number → Myanmar Date ─────────────────────────────────────────
def j2m(jd: float) -> MyanmarDate:
    """
    Convert Julian Day Number to Myanmar Date.
    """
    jdn = round(jd)
    my = math.floor((jdn - 0.5 - MO) / SY)  # Myanmar year
    yo = chk_my(my)
    dd = jdn - yo["tg1"] + 1  # day count

    b = math.floor(yo["myt"] / 2)
    c = math.floor(1 / (yo["myt"] + 1))  # big wa and common yr
    myl = 354 + (1 - c) * 30 + b          # year length
    mmt = math.floor((dd - 1) / myl)      # month type: Hnaung=1 or Oo=0
    dd -= mmt * myl

    a = math.floor((dd + 423) / 512)
    mm = math.floor((dd - b * a + c * a * 30 + 29.26) / 29.544)  # month
    e = math.floor((mm + 12) / 16)
    f = math.floor((mm + 11) / 16)
    md = dd - math.floor(29.544 * mm - 29.26) - b * e + c * f * 30  # day
    mm += f * 3 - e * 4
    mml = 30 - mm % 2  # month length
    if mm == 3:
        mml += b  # Nayon in big watat

    mp = math.floor((md + 1) / 16) + math.floor(md / 16) + math.floor(md / mml)
    fd = md - 15 * math.floor(md / 16)
    wd = (jdn + 2) % 7  # weekday: 0=Sat

    return MyanmarDate(
        myanmar_year=my,
        year_type=yo["myt"],
        year_length=myl,
        month=mm,
        month_type=mmt,
        month_length=mml,
        month_day=md,
        fortnight_day=fd,
        moon_phase=mp,
        weekday=wd,
    )


# ─── High-Level Convenience ──────────────────────────────────────────────────
def gregorian_to_myanmar(year: int, month: int, day: int) -> MyanmarDate:
    """
    Convert a Gregorian date to a Myanmar date.
    """
    jdn = w2j(year, month, day, ct=1)  # Use Gregorian calendar
    return j2m(jdn)


def get_myanmar_year(year: int, month: int, day: int) -> int:
    """Get the Myanmar Era year for a Gregorian date."""
    jdn = w2j(year, month, day, ct=1)
    return math.floor((jdn - 0.5 - MO) / SY)


def get_weekday_index(year: int, month: int, day: int) -> int:
    """
    Get the weekday index for a Gregorian date.
    Returns: 0=Sat, 1=Sun, 2=Mon, 3=Tue, 4=Wed, 5=Thu, 6=Fri
    """
    jdn = w2j(year, month, day, ct=1)
    return (jdn + 2) % 7


# ─── Self-Test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test: 2000-01-01 should have JDN = 2451545
    jdn = w2j(2000, 1, 1, ct=1)
    print(f"2000-01-01 JDN: {jdn} (expected: 2451545) {'✓' if jdn == 2451545 else '✗'}")

    # Test: 2012-05-23 → Myanmar 1374 Nayon waxing 3
    md = gregorian_to_myanmar(2012, 5, 23)
    print(f"2012-05-23 → {md.display}")
    print(f"  Year: {md.myanmar_year} (expected: 1374) {'✓' if md.myanmar_year == 1374 else '✗'}")
    print(f"  Month: {md.month} (expected: 3=Nayon) {'✓' if md.month == 3 else '✗'}")
    print(f"  Moon: {md.moon_phase} (expected: 0=waxing) {'✓' if md.moon_phase == 0 else '✗'}")
    print(f"  Day: {md.fortnight_day} (expected: 3) {'✓' if md.fortnight_day == 3 else '✗'}")

    # Test: Today
    from datetime import datetime
    now = datetime.now()
    today = gregorian_to_myanmar(now.year, now.month, now.day)
    print(f"\nToday ({now.strftime('%Y-%m-%d')}): {today.display}")
