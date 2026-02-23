"""
Mahabote (မဟာဘုတ်) Astrology Engine

Implements the traditional Myanmar Mahabote astrology system:
- 7 Houses derived from Myanmar Era year
- 8-day weekday system (Wednesday split at noon)
- Planet assignments and personality profiles
- 6-month Do/Don't forecast generation

All interpretations are provided in Myanmar language.
"""

import math
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional
from myanmar_calendar import gregorian_to_myanmar, get_myanmar_year, get_weekday_index, MyanmarDate


# ─── 8-Day Weekday System ────────────────────────────────────────────────────
# Mahabote uses 8 days: Wednesday is split into morning (Mercury) and afternoon (Rahu)

EIGHT_DAY_WEEK = {
    # weekday_index (from myanmar_calendar): {name_mm, name_en, planet_mm, planet_en, animal_mm, direction_mm}
    # myanmar_calendar weekday: 0=Sat, 1=Sun, 2=Mon, 3=Tue, 4=Wed, 5=Thu, 6=Fri
    0: {"name_mm": "စနေ", "name_en": "Saturday", "planet_mm": "စနေဂြိုဟ်", "planet_en": "Saturn",
        "animal_mm": "နဂါး", "animal_en": "Dragon/Naga", "direction_mm": "အနောက်တောင်"},
    1: {"name_mm": "တနင်္ဂနွေ", "name_en": "Sunday", "planet_mm": "နေဂြိုဟ်", "planet_en": "Sun",
        "animal_mm": "ဂဠုန်", "animal_en": "Garuda", "direction_mm": "အရှေ့မြောက်"},
    2: {"name_mm": "တနင်္လာ", "name_en": "Monday", "planet_mm": "လဂြိုဟ်", "planet_en": "Moon",
        "animal_mm": "ကျား", "animal_en": "Tiger", "direction_mm": "အရှေ့"},
    3: {"name_mm": "အင်္ဂါ", "name_en": "Tuesday", "planet_mm": "အင်္ဂါဂြိုဟ်", "planet_en": "Mars",
        "animal_mm": "ခြင်္သေ့", "animal_en": "Lion", "direction_mm": "အရှေ့တောင်"},
    4: {"name_mm": "ဗုဒ္ဓဟူး", "name_en": "Wednesday", "planet_mm": "ဗုဒ္ဓဂြိုဟ်", "planet_en": "Mercury",
        "animal_mm": "ဆင်(အစွယ်ရှိ)", "animal_en": "Tusked Elephant", "direction_mm": "တောင်"},
    5: {"name_mm": "ကြာသပတေး", "name_en": "Thursday", "planet_mm": "ကြာသပတေးဂြိုဟ်", "planet_en": "Jupiter",
        "animal_mm": "ကြွက်", "animal_en": "Rat", "direction_mm": "အနောက်"},
    6: {"name_mm": "သောကြာ", "name_en": "Friday", "planet_mm": "သောကြာဂြိုဟ်", "planet_en": "Venus",
        "animal_mm": "ပူးဂဗ်", "animal_en": "Guinea Pig", "direction_mm": "မြောက်"},
    # Rahu = Wednesday afternoon
    7: {"name_mm": "ရာဟု", "name_en": "Rahu (Wed PM)", "planet_mm": "ရာဟုဂြိုဟ်", "planet_en": "Rahu",
        "animal_mm": "ဆင်(အစွယ်မဲ့)", "animal_en": "Tuskless Elephant", "direction_mm": "အနောက်မြောက်"},
}


# ─── 7 Houses of Mahabote ────────────────────────────────────────────────────
# House index = Myanmar Era year % 7

HOUSES = {
    0: {
        "name_mm": "အသေအိမ်",
        "name_en": "House of Impermanence",
        "planet_mm": "စနေ",
        "planet_en": "Saturn",
        "nature": "liability",
        "personality_mm": (
            "အသေအိမ်ဖွား ပုဂ္ဂိုလ်များသည် လွတ်လပ်မှုကို နှစ်သက်ပြီး စိတ်ဓာတ်တွင် "
            "မတည်ငြိမ်မှုများ ရှိတတ်ပါသည်။ ကျန်းမာရေးနှင့် ချမ်းသာကြွယ်ဝမှု "
            "အတက်အကျ ရှိတတ်ပြီး ဘဝနောက်ပိုင်းတွင် ဆရာအတတ်ပညာဖြင့် "
            "အောင်မြင်တတ်ပါသည်။ စိတ်ရှည်သည်းခံမှုနှင့် တည်ငြိမ်မှုကို "
            "လေ့ကျင့်ရန် လိုအပ်ပါသည်။"
        ),
        "personality_en": (
            "People born in the House of Impermanence value independence and may experience "
            "nervous tension. Health and wealth tend to fluctuate. Success often comes later "
            "in life, especially in teaching and mentoring roles."
        ),
        "strengths_mm": ["စိတ်ဓာတ်ကြံ့ခိုင်မှု", "အလုပ်ကြိုးစားမှု", "ဆရာအတတ်ပညာ"],
        "weaknesses_mm": ["စိတ်မတည်ငြိမ်မှု", "ငွေကြေးအတက်အကျ", "စိတ်ပူပန်မှု"],
    },
    1: {
        "name_mm": "အထွန်းအိမ်",
        "name_en": "House of Extremity",
        "planet_mm": "နေ",
        "planet_en": "Sun",
        "nature": "liability",
        "personality_mm": (
            "အထွန်းအိမ်ဖွား ပုဂ္ဂိုလ်များသည် အစွန်းရောက်တတ်ပြီး ငယ်ရွယ်စဉ် "
            "ကျန်းမာရေး သို့မဟုတ် မတော်တဆမှုများ ကြုံတွေ့ရတတ်ပါသည်။ "
            "ဤအချိန်ကို ကျော်လွှားနိုင်ပါက ကြီးကျယ်သော အောင်မြင်မှုကို "
            "ရရှိတတ်ပါသည်။ \"ရှိလျှင် အလွန်ရှိ၊ မရှိလျှင် လုံးဝမရှိ\" "
            "ဟူသော သဘောသဘာဝ ရှိပါသည်။"
        ),
        "personality_en": (
            "House of Extremity natives experience life in extremes — 'all or nothing.' "
            "Early life may bring serious accidents or illness, but surviving these challenges "
            "often leads to remarkable success."
        ),
        "strengths_mm": ["ရဲရင့်မှု", "ခေါင်းဆောင်နိုင်စွမ်း", "ပရဟိတစိတ်"],
        "weaknesses_mm": ["အစွန်းရောက်တတ်မှု", "ကျန်းမာရေးအန္တရာယ်", "စိတ်တိုမှု"],
    },
    2: {
        "name_mm": "သိုက်အိမ်",
        "name_en": "House of Fame",
        "planet_mm": "လ",
        "planet_en": "Moon",
        "nature": "asset",
        "personality_mm": (
            "သိုက်အိမ်ဖွား ပုဂ္ဂိုလ်များသည် ကိုယ်ပိုင်လုံ့လဝီရိယဖြင့် "
            "အောင်မြင်တတ်သူများ ဖြစ်ပါသည်။ ပညာတတ်၊ ရဲရင့်ပြီး "
            "စိတ်ကူးစိတ်သန်း ကြွယ်ဝသူများ ဖြစ်တတ်ပါသည်။ "
            "နာမည်ကျော်ကြားမှုနှင့် ဂုဏ်သတင်းကို ရရှိတတ်ပြီး "
            "လူအများ လေးစားမှု ခံရတတ်ပါသည်။"
        ),
        "personality_en": (
            "House of Fame natives are self-made and educated, known for courage, ambition, "
            "and wisdom. They tend to earn fame and respect through their own efforts."
        ),
        "strengths_mm": ["ကိုယ်ပိုင်အားထုတ်မှု", "ဉာဏ်ပညာ", "ကျော်ကြားမှု"],
        "weaknesses_mm": ["အလွန်အကျွံ ကြိုးစားမှု", "အနားယူမှု နည်းခြင်း"],
    },
    3: {
        "name_mm": "ရာဇအိမ်",
        "name_en": "House of Wealth",
        "planet_mm": "အင်္ဂါ",
        "planet_en": "Mars",
        "nature": "asset",
        "personality_mm": (
            "ရာဇအိမ်ဖွား ပုဂ္ဂိုလ်များသည် ရိုသေလေးစားမှု ရှိပြီး "
            "ဘာသာရေး သို့မဟုတ် ဝိညာဉ်ရေး စိတ်ဝင်စားသူများ ဖြစ်တတ်ပါသည်။ "
            "ရက်ရောလောင်းလှဲမှုနှင့် ရည်မှန်းချက်မြင့်မားမှု ရှိပြီး "
            "ချမ်းသာကြွယ်ဝမှုကို ဆွဲဆောင်နိုင်စွမ်း ရှိပါသည်။"
        ),
        "personality_en": (
            "House of Wealth natives are respectful, spiritual, generous, and possess high goals. "
            "They have a natural ability to attract wealth and happiness."
        ),
        "strengths_mm": ["ရက်ရောမှု", "ဘာသာရေးစိတ်", "ချမ်းသာမှု"],
        "weaknesses_mm": ["အလွန်အကျွံ သုံးစွဲမှု", "ယုံကြည်လွယ်မှု"],
    },
    4: {
        "name_mm": "ပုတိအိမ်",
        "name_en": "House of Kingly Position",
        "planet_mm": "ဗုဒ္ဓ",
        "planet_en": "Mercury",
        "nature": "asset",
        "personality_mm": (
            "ပုတိအိမ်ဖွား ပုဂ္ဂိုလ်များသည် ဉာဏ်ကောင်းပြီး "
            "ထက်မြက်သူများ ဖြစ်ပါသည်။ ခေါင်းဆောင်ရာထူးနေရာ "
            "ရရှိတတ်ပြီး စီးပွားရေး သို့မဟုတ် အဖွဲ့အစည်းတွင် "
            "ဘုရင်သဖွယ် နေထိုင်တတ်ပါသည်။ ရည်မှန်းချက်ကို "
            "အပြည့်အဝ မပြည့်စုံနိုင်ဟု ခံစားရတတ်ပါသည်။"
        ),
        "personality_en": (
            "House of Kingly Position natives are intelligent and astute, often attaining "
            "high positions in business or institutions. They live 'like a king' in influence."
        ),
        "strengths_mm": ["ဉာဏ်ထက်မြက်မှု", "ခေါင်းဆောင်နိုင်စွမ်း", "အရာအမြင့်"],
        "weaknesses_mm": ["ပြည့်စုံမှု မခံစားရခြင်း", "စိတ်ဖိစီးမှု"],
    },
    5: {
        "name_mm": "အဓိပတိအိမ်",
        "name_en": "House of Sickly/Change",
        "planet_mm": "ကြာသပတေး",
        "planet_en": "Jupiter",
        "nature": "liability",
        "personality_mm": (
            "အဓိပတိအိမ်ဖွား ပုဂ္ဂိုလ်များသည် ကျန်းမာရေး စိန်ခေါ်မှုများ "
            "ကြုံတွေ့ရတတ်ပြီး ကိုယ်ခန္ဓာ၊ စိတ်ပိုင်း သို့မဟုတ် "
            "စိတ်ခံစားချက်ပိုင်း ဒုက္ခများ ရှိတတ်ပါသည်။ "
            "အပြောင်းအလဲများမှု ဘဝဟန်ချက် ညီအောင် ထိန်းညှိရန် "
            "လိုအပ်ပြီး ကျန်းမာရေးကို ဂရုစိုက်ရန် အရေးကြီးပါသည်။"
        ),
        "personality_en": (
            "The most challenging house. Natives may face persistent physical, emotional, "
            "or mental distress. Self-care and resilience are essential."
        ),
        "strengths_mm": ["ခံနိုင်ရည်ရှိမှု", "အပြောင်းအလဲကို လက်ခံနိုင်မှု"],
        "weaknesses_mm": ["ကျန်းမာရေးပြဿနာ", "စိတ်ဖိစီးမှု", "မတည်ငြိမ်မှု"],
    },
    6: {
        "name_mm": "သုခအိမ်",
        "name_en": "House of Leader",
        "planet_mm": "သောကြာ",
        "planet_en": "Venus",
        "nature": "asset",
        "personality_mm": (
            "သုခအိမ်ဖွား ပုဂ္ဂိုလ်များသည် စကားပြောကောင်းပြီး "
            "ဆက်ဆံရေးပြေပြစ်သူများ ဖြစ်ပါသည်။ အစိုးရ သို့မဟုတ် "
            "စီးပွားရေး လုပ်ငန်းတွင် ခေါင်းဆောင်ဖြစ်တတ်ပြီး "
            "လူမှုဆက်ဆံရေးတွင် ထူးချွန်ပါသည်။ "
            "ပတ်ဝန်းကျင် လူများ၏ ချစ်ခင်မှုကို ရရှိတတ်ပါသည်။"
        ),
        "personality_en": (
            "House of Leader natives are articulate, charismatic, and potential leaders "
            "in government or commerce. They excel in social relationships."
        ),
        "strengths_mm": ["ခေါင်းဆောင်မှု", "ဆက်ဆံရေးကောင်းမှု", "စကားပြောကောင်းမှု"],
        "weaknesses_mm": ["အာရုံအလွန်ပြန့်မှု", "ဆုံးဖြတ်ချက်နှေးမှု"],
    },
}


# ─── 6-Month Forecast Rules ──────────────────────────────────────────────────
# Each house has specific Do/Don't guidance and seasonal modifiers

FORECAST_RULES = {
    0: {  # House of Impermanence (Saturn)
        "do_mm": [
            "တရားထိုင်ခြင်းနှင့် စိတ်ငြိမ်သက်မှု ရှာဖွေပါ",
            "ငွေကြေးစုဆောင်းပြီး ချွေတာပါ",
            "ပညာသင်ကြားပေးခြင်း လုပ်ပါ",
            "ကျန်းမာရေး စစ်ဆေးမှု ခံယူပါ",
            "ရေရှည် ရင်းနှီးမြှုပ်နှံမှု ပြုလုပ်ပါ",
            "မိသားစု ဆက်ဆံရေး ခိုင်မြဲအောင် ထိန်းသိမ်းပါ",
        ],
        "dont_mm": [
            "ရေတိုလောင်းကစားမှု ရှောင်ကြဉ်ပါ",
            "အလွန်အကျွံ သုံးစွဲခြင်း မပြုပါနှင့်",
            "စနေနေ့တွင် ခရီးအဝေးမသွားပါနှင့်",
            "စိတ်လိုက်မာန်ပါ ဆုံးဖြတ်ချက်များ မချပါနှင့်",
            "ငွေချေးခြင်း ရှောင်ကြဉ်ပါ",
            "အငြင်းအခုံ ရှောင်ကြဉ်ပါ",
        ],
    },
    1: {  # House of Extremity (Sun)
        "do_mm": [
            "ခေါင်းဆောင်မှု စွမ်းရည်ကို ဖော်ထုတ်ပါ",
            "ပရဟိတ လှူဒါန်းပါ",
            "ကိုယ်ကာယ ကျန်းမာရေး ဂရုစိုက်ပါ",
            "အသစ်အဆန်း စွန့်စားလုပ်ကိုင်ပါ",
            "ယုံကြည်မှုရှိစွာ ဆုံးဖြတ်ပါ",
            "အားကစား လေ့ကျင့်ပါ",
        ],
        "dont_mm": [
            "တနင်္ဂနွေနေ့တွင် အရှေ့ဘက် ခရီးမသွားပါနှင့်",
            "အစွန်းရောက်သော ဆုံးဖြတ်ချက်များ ရှောင်ကြဉ်ပါ",
            "မာနကြီးခြင်း ရှောင်ကြဉ်ပါ",
            "ကျန်းမာရေး လျစ်လျူရှု မပြုပါနှင့်",
            "ရန်သူများ မပွားပါနှင့်",
            "အန္တရာယ်ရှိသော အားကစား ရှောင်ကြဉ်ပါ",
        ],
    },
    2: {  # House of Fame (Moon)
        "do_mm": [
            "ဖန်တီးရေး လုပ်ငန်းများ လုပ်ပါ",
            "ရေနှင့် ဆက်စပ်သော စီးပွားရေး စဉ်းစားပါ",
            "ပညာရေးတွင် ရင်းနှီးမြှုပ်နှံပါ",
            "နာမည်ကောင်း ရအောင် ကြိုးစားပါ",
            "သုတေသန လုပ်ငန်းများ ဆောင်ရွက်ပါ",
            "ကိုယ်ပိုင် အရည်အချင်းများ ဖွံ့ဖြိုးအောင် လုပ်ပါ",
        ],
        "dont_mm": [
            "အမျိုးသမီးများနှင့် ပဋိပက္ခ ရှောင်ကြဉ်ပါ",
            "ညအချိန် ခရီးသွားခြင်း သတိထားပါ",
            "ဂုဏ်သတင်းကို ထိခိုက်စေမည့်အရာ ရှောင်ကြဉ်ပါ",
            "ရေနှင့်ဆက်စပ်သော အန္တရာယ် သတိထားပါ",
            "လူမုန်းတီးဖွယ် အပြုအမူ ရှောင်ကြဉ်ပါ",
            "မိမိကိုယ်ကို အလွန်အကျွံ ချီးမြှင့်ခြင်း ရှောင်ကြဉ်ပါ",
        ],
    },
    3: {  # House of Wealth (Mars)
        "do_mm": [
            "ရဲရင့်စွာ ဆုံးဖြတ်ပါ",
            "ကိုယ်ကာယ လေ့ကျင့်ခန်း လုပ်ပါ",
            "ဘာသာရေး ကုသိုလ် ပြုပါ",
            "ရင်းနှီးမြှုပ်နှံမှု လုပ်ကိုင်ပါ",
            "အိမ်ခြံမြေ ကိစ္စများ ဆောင်ရွက်ပါ",
            "ခေါင်းဆောင်ဖြစ်ရန် ကြိုးစားပါ",
        ],
        "dont_mm": [
            "အင်္ဂါနေ့တွင် ထက်ရှသော လက်နက် ကိုင်တွယ်ခြင်း ရှောင်ကြဉ်ပါ",
            "ဒေါသထွက်ခြင်း ရှောင်ကြဉ်ပါ",
            "စစ်ခင်းခြင်းနှင့် ပဋိပက္ခ ရှောင်ကြဉ်ပါ",
            "မီးဘေး သတိထားပါ",
            "အလွန်အကျွံ စွန့်စားခြင်း ရှောင်ကြဉ်ပါ",
            "ရန်လိုမှု ထိန်းချုပ်ပါ",
        ],
    },
    4: {  # House of Kingly Position (Mercury)
        "do_mm": [
            "ကုန်သွယ်ရေးနှင့် စာချုပ်ကိစ္စ ဆောင်ရွက်ပါ",
            "ပညာသင်ကြားမှု ဆက်လက်လုပ်ပါ",
            "ဆက်သွယ်ရေး ကွန်ရက် ချဲ့ထွင်ပါ",
            "ရေးသားခြင်းနှင့် ပညာရေး ရင်းနှီးမြှုပ်နှံပါ",
            "နည်းပညာ လုပ်ငန်းများ စတင်ပါ",
            "စီးပွားရေး စီမံကိန်းသစ်များ ရေးဆွဲပါ",
        ],
        "dont_mm": [
            "လိမ်ညာခြင်း သို့မဟုတ် ကြမ်းတမ်းသော စကား ရှောင်ကြဉ်ပါ",
            "ဗုဒ္ဓဟူးနေ့တွင် အရေးကြီး စာချုပ်များ မချုပ်ပါနှင့်",
            "ယုံကြည်မှုကို ချိုးဖောက်ခြင်း ရှောင်ကြဉ်ပါ",
            "အချက်အလက်မဲ့ ကတိကဝတ်များ မပေးပါနှင့်",
            "နှစ်မျက်နှာ ပြုမူခြင်း ရှောင်ကြဉ်ပါ",
            "မမှန်သော သတင်းများ မဖြန့်ပါနှင့်",
        ],
    },
    5: {  # House of Sickly/Change (Jupiter)
        "do_mm": [
            "တရားဥပဒေ ကိစ္စများ ဆောင်ရွက်ပါ",
            "ပညာရေးတွင် ရင်းနှီးမြှုပ်နှံပါ",
            "ကျန်းမာရေး ဂရုစိုက်ပါ",
            "ဘာသာရေး အလှူအတန်း ပြုပါ",
            "စိတ်ပိုင်းဆိုင်ရာ ကုစားမှု ခံယူပါ",
            "သဘာဝ ပတ်ဝန်းကျင်တွင် အနားယူပါ",
        ],
        "dont_mm": [
            "အကြီးအကဲများကို မထီမဲ့မြင် မပြုပါနှင့်",
            "ကြာသပတေးနေ့တွင် ခွဲစိတ်မှု ရှောင်ကြဉ်ပါ",
            "ကျန်းမာရေး ဈေးခိုင်းခြင်း ရှောင်ကြဉ်ပါ",
            "စိတ်ဖိစီးမှု များသော လုပ်ငန်းများ ရှောင်ကြဉ်ပါ",
            "မကောင်းသော အလေ့အထများ ရှောင်ကြဉ်ပါ",
            "ညအချိန် အပြင်ထွက်ခြင်း ရှောင်ကြဉ်ပါ",
        ],
    },
    6: {  # House of Leader (Venus)
        "do_mm": [
            "လူမှုဆက်ဆံရေး တိုးချဲ့ပါ",
            "အလှအပ လုပ်ငန်းများ စတင်ပါ",
            "အနုပညာနှင့် ဖန်တီးရေး လုပ်ငန်း ဆောင်ရွက်ပါ",
            "အိမ်ထောင်ရေး ကိစ္စများ ဂရုစိုက်ပါ",
            "ပွဲလမ်းသဘင်များ စီစဉ်ပါ",
            "လှူဒါန်းခြင်းနှင့် ပရဟိတ လုပ်ငန်းများ ဆောင်ရွက်ပါ",
        ],
        "dont_mm": [
            "သောကြာနေ့တွင် ငွေချေးခြင်း ရှောင်ကြဉ်ပါ",
            "အလွန်အကျွံ အသုံးစွဲခြင်း ရှောင်ကြဉ်ပါ",
            "အချစ်ရေးတွင် အလျင်စလို မဖြစ်ပါနှင့်",
            "အရက်နှင့် မူးယစ်ဆေးဝါး ရှောင်ကြဉ်ပါ",
            "စကားများပြောခြင်း ထိန်းချုပ်ပါ",
            "ပျော်ပွဲရွှင်ပွဲ အလွန်အကျွံ ရှောင်ကြဉ်ပါ",
        ],
    },
}

# Monthly seasonal modifiers for forecast richness
MONTH_MODIFIERS_MM = [
    "ဤလတွင် စိတ်အားထက်သန်မှု ပိုမိုရရှိမည်",      # Month 1
    "ဤလတွင် ငွေကြေးကံ ပွင့်လန်းမည်",               # Month 2
    "ဤလတွင် ဆက်ဆံရေး ပိုမိုခိုင်မြဲမည်",            # Month 3
    "ဤလတွင် အလုပ်အကိုင် အခွင့်အလမ်း ရရှိမည်",     # Month 4
    "ဤလတွင် ကျန်းမာရေး အထူးဂရုစိုက်ရန် လိုအပ်မည်", # Month 5
    "ဤလတွင် ပညာရေးနှင့် သုတေသန ကံကောင်းမည်",       # Month 6
]


# ─── Main Engine Class ────────────────────────────────────────────────────────
@dataclass
class MahaboteReading:
    """Complete Mahabote astrology reading for a person."""
    name: str
    birth_date: datetime
    is_wednesday_pm: bool
    myanmar_date: MyanmarDate
    myanmar_year: int
    house_index: int
    house: dict
    birth_day: dict
    forecast_rules: dict
    current_age: int = 0
    current_myanmar_year: int = 0
    current_year_house: dict = field(default_factory=dict)

    @property
    def house_remainder(self) -> int:
        return self.house_index


class MahaboteEngine:
    """Mahabote Astrology calculation engine."""

    def calculate(
        self,
        name: str,
        birth_year: int,
        birth_month: int,
        birth_day: int,
        is_wednesday_pm: bool = False,
    ) -> MahaboteReading:
        """
        Compute a full Mahabote reading for a person.
        
        Args:
            name: Person's name
            birth_year: Gregorian birth year
            birth_month: Gregorian birth month
            birth_day: Gregorian birth day
            is_wednesday_pm: True if born on Wednesday after 12:00 PM
        """
        # Get Myanmar calendar data
        mm_date = gregorian_to_myanmar(birth_year, birth_month, birth_day)
        my_year = mm_date.myanmar_year

        # House = Myanmar year % 7
        house_index = my_year % 7
        house = HOUSES[house_index]

        # 8-day weekday
        wd = mm_date.weekday  # 0=Sat, 1=Sun, 2=Mon, 3=Tue, 4=Wed, 5=Thu, 6=Fri
        if wd == 4 and is_wednesday_pm:
            birth_day_info = EIGHT_DAY_WEEK[7]  # Rahu
        else:
            birth_day_info = EIGHT_DAY_WEEK[wd]

        # Forecast rules
        rules = FORECAST_RULES[house_index]

        now = datetime.now()
        current_mm_date = gregorian_to_myanmar(now.year, now.month, now.day)
        current_myanmar_year = current_mm_date.myanmar_year
        current_age = current_myanmar_year - my_year + 1
        
        current_year_house_index = current_age % 7
        current_year_house = HOUSES[current_year_house_index]

        return MahaboteReading(
            name=name,
            birth_date=datetime(birth_year, birth_month, birth_day),
            is_wednesday_pm=is_wednesday_pm,
            myanmar_date=mm_date,
            myanmar_year=my_year,
            house_index=house_index,
            house=house,
            birth_day=birth_day_info,
            forecast_rules=rules,
            current_age=current_age,
            current_myanmar_year=current_myanmar_year,
            current_year_house=current_year_house,
        )

    def generate_6month_forecast(self, reading: MahaboteReading) -> list:
        """
        Generate a 6-month forecast with Do/Don't guidance.
        Returns a list of monthly forecast dicts.
        """
        forecasts = []
        now = datetime.now()

        for i in range(6):
            target_date = now + timedelta(days=i * 30)
            month_name = self._get_myanmar_month_name(target_date)
            year_str = str(target_date.year)

            # Rotate through Do/Don't items for variety
            do_idx = i % len(reading.forecast_rules["do_mm"])
            dont_idx = i % len(reading.forecast_rules["dont_mm"])

            forecasts.append({
                "month_mm": month_name,
                "year": year_str,
                "month_en": target_date.strftime("%B %Y"),
                "do_mm": reading.forecast_rules["do_mm"][do_idx],
                "dont_mm": reading.forecast_rules["dont_mm"][dont_idx],
                "modifier_mm": MONTH_MODIFIERS_MM[i],
            })

        return forecasts

    def get_greeting_message(self) -> str:
        """Bot greeting in Myanmar."""
        return (
            "🔮 မင်္ဂလာပါ! **Su Mon Myint Oo မဟာဘုတ် ဗေဒင်(Tarot)** မှ ကြိုဆိုပါတယ်။\n\n"
            "သင့်ရဲ့ မွေးနေ့ ဗေဒင် ဟောစာတမ်း ပြုစုပေးပါမယ်။\n"
            "ကျေးဇူးပြု၍ သင့်ရဲ့ **အမည်** ကို ရိုက်ထည့်ပေးပါ။ 🙏"
        )

    def get_dob_prompt(self, name: str) -> str:
        """Ask for date of birth in Myanmar."""
        return (
            f"ကျေးဇူးတင်ပါတယ် **{name}** ရှင့်!\n\n"
            "သင့်ရဲ့ **မွေးနေ့ရက်စွဲ** ကို ပေးပါ။\n"
            "ဥပမာ - `1990-05-15` (နှစ်-လ-ရက်) ပုံစံဖြင့် ရိုက်ထည့်ပေးပါ။ 📅"
        )

    def get_wednesday_prompt(self) -> str:
        """Ask about Wednesday birth time."""
        return (
            "သင် **ဗုဒ္ဓဟူးနေ့** ဖွားဖြစ်ပါတယ်!\n\n"
            "မဟာဘုတ် ဗေဒင်တွင် ဗုဒ္ဓဟူးနေ့ကို နှစ်ပိုင်း ခွဲပါတယ်:\n"
            "• **နံနက်** (မွန်းတည့်မတိုင်မီ) = ဗုဒ္ဓဂြိုဟ်\n"
            "• **ညနေ** (မွန်းတည့်ပြီးနောက်) = ရာဟုဂြိုဟ်\n\n"
            "သင် **နံနက်** ဖွားလား၊ **ညနေ** ဖွားလား?\n"
            "(`နံနက်` သို့မဟုတ် `ညနေ` ဟု ရိုက်ထည့်ပေးပါ) ⏰"
        )

    def format_reading(self, reading: MahaboteReading) -> str:
        """Format a full Mahabote reading as Myanmar text."""
        house = reading.house
        bd = reading.birth_day
        md = reading.myanmar_date

        lines = [
            f"🌟 **{reading.name}** ၏ မဟာဘုတ် ဗေဒင် ဟောစာတမ်း 🌟",
            "",
            "═══════════════════════════════════════",
            f"📅 **မွေးနေ့**: {reading.birth_date.strftime('%Y-%m-%d')}",
            f"🗓️ **မြန်မာရက်စွဲ**: {md.display}",
            f"📆 **မြန်မာသက္ကရာဇ်**: {reading.myanmar_year} ခုနှစ်",
            f"🎂 **လက်ရှိအသက်**: {reading.current_age} နှစ် (မြန်မာသက္ကရာဇ် {reading.current_myanmar_year} အရ)",
            f"🔮 **ယခုနှစ်ကံကြမ္မာ (သက်ရောက်အိမ်)**: {reading.current_year_house['name_mm']} ({reading.current_year_house['name_en']})",
            f"🌙 **လ အလင်း**: {md.moon_phase_name}",
            "",
            "═══════════════════════════════════════",
            f"🏠 **မဟာဘုတ်အိမ်**: {house['name_mm']} ({house['name_en']})",
            f"🪐 **အိမ်ရှင်ဂြိုဟ်**: {house['planet_mm']} ({house['planet_en']})",
            f"🔢 **ကြွင်းကိန်း**: {reading.house_remainder}",
            f"📊 **သဘာဝ**: {'ကောင်းသောအိမ်' if house['nature'] == 'asset' else 'စိန်ခေါ်သောအိမ်'}",
            "",
            "═══════════════════════════════════════",
            f"☀️ **မွေးနေ့**: {bd['name_mm']} ({bd['name_en']})",
            f"🪐 **မွေးနေ့ဂြိုဟ်**: {bd['planet_mm']} ({bd['planet_en']})",
            f"🐾 **ရာသီတိရစ္ဆာန်**: {bd['animal_mm']} ({bd['animal_en']})",
            f"🧭 **ကံကောင်းသော ဦးတည်ရာ**: {bd['direction_mm']}",
            "",
            "═══════════════════════════════════════",
            "**🧬 ကိုယ်ရည်ကိုယ်သွေး ဖတ်ခြင်း:**",
            "",
            house['personality_mm'],
            "",
            "**💪 အားသာချက်များ:**",
        ]
        for s in house.get("strengths_mm", []):
            lines.append(f"  ✅ {s}")

        lines.append("")
        lines.append("═══════════════════════════════════════")

        return "\n".join(lines)

    def format_forecast(self, reading: MahaboteReading) -> str:
        """Format the 6-month forecast as Myanmar text."""
        forecasts = self.generate_6month_forecast(reading)

        lines = [
            f"📅 **{reading.name}** ၏ ၆ လ ဟောစာတမ်း",
            f"🎂 **လက်ရှိအသက်**: {reading.current_age} နှစ် (မြန်မာသက္ကရာဇ် {reading.current_myanmar_year} အရ)",
            f"🔮 **ယခုနှစ်ကံကြမ္မာ (သက်ရောက်အိမ်)**: {reading.current_year_house['name_mm']} ({reading.current_year_house['name_en']})",
            f"🏠 မူလအိမ်: {reading.house['name_mm']} ({reading.house['name_en']})",
            "",
            "═══════════════════════════════════════",
        ]

        for f in forecasts:
            lines.extend([
                "",
                f"🗓️ **{f['month_en']}**",
                f"💫 {f['modifier_mm']}",
                f"  ✅ လုပ်သင့်သည်: {f['do_mm']}",
                f"  ❌ ရှောင်ကြဉ်ရန်: {f['dont_mm']}",
            ])

        lines.extend([
            "",
            "═══════════════════════════════════════",
        ])

        return "\n".join(lines)


    @staticmethod
    def _get_myanmar_month_name(dt: datetime) -> str:
        """Approximate Myanmar month name from Gregorian date."""
        names = [
            "ပြာသိုလ", "တပို့တွဲလ", "တပေါင်းလ", "တန်ခူးလ",
            "ကဆုန်လ", "နယုန်လ", "ဝါဆိုလ", "ဝါခေါင်လ",
            "တော်သလင်းလ", "သီတင်းကျွတ်လ", "တန်ဆောင်မုန်းလ", "နတ်တော်လ",
        ]
        # Rough mapping: Gregorian month → Myanmar month (offset by ~3)
        idx = (dt.month + 2) % 12
        return names[idx]


# ─── Self-Test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = MahaboteEngine()

    # Test with a known date
    reading = engine.calculate("တက်ဇော်", 1990, 5, 15)
    print(engine.format_reading(reading))
    print()
    print(engine.format_forecast(reading))
