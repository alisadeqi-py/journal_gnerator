import os
import json
import logging
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv
from httpx import Timeout

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

client = AsyncOpenAI(
    api_key= "sk-RQ0yQp86iI2n8jhJ8WPaEmnuKlhcVwKqP6WvRVeE0RWSgLax",
    base_url='https://api.gapgpt.app/v1',
)

def build_prompt(
    place_name: str,
    location: str,
    about_char_limit: int = 180
) -> str:

    prompt_template = f"""
You are an expert Persian travel guide writer and a precise JSON generator.
Generate a COMPLETE Persian travel guide for:
- Place Name: "{place_name}"
- Location: "{location}"

### STRICT RULES:
1. Output ONLY valid JSON. No markdown, no comments (// or /* */), no explanations, no trailing commas.
2. ALL descriptive text values must be in Persian (Farsi).
3. If a specific data point is unknown, use null for strings/numbers and false for booleans. NEVER hallucinate.
4. Boolean fields: set true ONLY if the feature genuinely exists at this place.
5. For HTML fields (about_post-int, reason_naming, etc.), wrap text in <p> tags.
6. The "access_hours" array must have exactly 7 entries, one per day of the week (شنبه through جمعه).

### OUTPUT JSON STRUCTURE:
{{
  "post_title": "نام مکان یا مجموعه",
  "acf_fields": {{
    "visit_duration": "X ساعت زمان لازم",
    "visit_count": "سالانه X بازدید",
    "temporarily_closed": false,
    "24access": false,
    "access_hours": [
      {{"day": "شنبه",    "closed": false, "from": "08:00", "to": "20:00"}},
      {{"day": "یک‌شنبه", "closed": false, "from": "08:00", "to": "20:00"}},
      {{"day": "دوشنبه",  "closed": false, "from": "08:00", "to": "20:00"}},
      {{"day": "سه‌شنبه", "closed": false, "from": "08:00", "to": "20:00"}},
      {{"day": "چهارشنبه","closed": false, "from": "08:00", "to": "20:00"}},
      {{"day": "پنج‌شنبه","closed": false, "from": "08:00", "to": "20:00"}},
      {{"day": "جمعه",    "closed": false, "from": "08:00", "to": "20:00"}}
    ],
    "kind_price": false,
    "entrance_fee": "هزینه ورودی یا: بازدید از این جاذبه رایگان است",
    "variable_fee": [
      {{"ttl": "عنوان هزینه", "fee": "مبلغ"}}
    ],
    "data": {{
      "season-best-view": [
        {{"select_seasen": "spring|summer|autumn|winter", "description": "توضیحات"}}
      ],
      "week-best-view": [
        {{"select_day": "saturday|sundey|mondey|tuseday|wendsday|thursday|friday", "description": "توضیحات"}}
      ],
      "day-best-view": [
        {{"select_time": "day|night", "description": "توضیحات"}}
      ]
    }},
    "phone_numbers": [
      {{"phone": "۰XX-XXXXXXXX"}}
    ],
    "about_post-int": "<p>درباره مکان به فارسی - حداکثر {about_char_limit} کاراکتر</p>",
    "reason_naming": "<p>علت نام‌گذاری به فارسی</p>",
    "cam-conditions": "<p>شرایط کمپ به فارسی</p>",
    "picnic-conditions": "<p>شرایط پیکنیک به فارسی</p>",
    "post-rules": "<p>قوانین مکان به فارسی</p>",
    "suitable-data": {{
      "suitable-family": false,
      "suitable-baby": false,
      "suitable-baby_desc": "توضیح",
      "suitable-ms": false,
      "suitable-ms_desc": "توضیح",
      "suitable-mr": false,
      "suitable-mr_desc": "توضیح",
      "suitable-f": false,
      "suitable-f_desc": "توضیح",
      "suitable-disabled-people": false,
      "suitable-disabled-people_desc": "توضیح",
      "suitable-tourists": false,
      "suitable-tourists_desc": "توضیح",
      "suitable-tourists_desc_price": null
    }},
    "access_routes": [
      {{
        "from": "شهر مبدا",
        "by_car": "توضیح مسیر با ماشین",
        "by_train": "توضیح مسیر با قطار",
        "by_bus": "توضیح مسیر با اتوبوس",
        "by_airplan": "توضیح مسیر با هواپیما"
      }}
    ],
    "important_places": [
      {{"place": "نام مکان", "desc": "توضیح مکان"}}
    ],
    "difficulty_road": "<p>سختی راه به فارسی</p>",
    "parking_space": "<p>توضیح پارکینگ به فارسی</p>",
    "time-reading": 5,
    "post_adress": "آدرس کامل به فارسی",
    "location_way": "<p>راه دسترسی به فارسی</p>",
    "essential_tips": "<p>نکات ضروری به فارسی</p>",
    "posts_faq": [
      {{"question": "سوال؟", "answer": "<p>جواب</p>"}}
    ]
  }},
  "categories": {{
    "iran-tour": false, "alborz": false, "chalus-road": false, "karaj": false,
    "kurds": false, "tehran": false, "guilan": false, "talesh": false,
    "lisar": false, "mazandaran": false, "amol": false, "chalus": false,
    "ramsar": false, "kelardasht": false, "marzanabad-mazandaran": false,
    "namak-abroud": false, "the-light": false, "nowshahr": false,
    "hormozgan": false, "kish": false, "tourism": false,
    "tourism-magazine": false, "study-travel-guide": false,
    "camping-guide": false, "travel": false, "travel-application": false,
    "travel-plan": false, "travel-guide": false, "visa": false, "food": false
  }},
  "essential_items": {{
    "drinking-water": false, "raincoats-and-waterproof-clothing": false,
    "passport": false, "power-bank": false, "travel-blanket": false,
    "cash": false, "chador": false, "generic-drugs": false,
    "mobile-charger": false, "glasses": false, "identification-card": false,
    "walking-shoes": false, "mountaineering-shoes": false, "first-aid": false,
    "backpack": false, "sleeping-bag": false, "seasonal-clothing": false,
    "map-or-gps": false, "a-light-meal": false
  }},
  "facilities": {{
    "mobile-antenna": false, "alachiq": false, "accommodation-facilities": false,
    "snack-buffet": false, "parking": false, "internet-access": false,
    "help": false, "toilet": false, "wheelchair": false,
    "guarding": false, "need-to-know": false, "wifi": false
  }},
  "should_do": {{
    "bathing": false, "hydrotherapy": false, "spa": false, "off-road": false,
    "escape-room": false, "horseback-riding": false, "swimming-pool": false,
    "skycycle": false, "submarine-scooter": false, "water-skiing": false,
    "snow-skiing": false, "ice-skating": false, "snorkeling": false,
    "kite-flying": false, "bodybuilding-club": false, "billiards-club": false,
    "shooting-club": false, "bungee-jumping": false, "banana-ride": false,
    "bowling": false, "big-ball": false, "paracel": false, "water-park": false,
    "paddle-board": false, "free-jump": false, "suspension-bridge": false,
    "roller-skating-rink": false, "cycling-track": false,
    "motor-racing-track": false, "paintball": false, "trampoline": false,
    "cable-car": false, "telesigh": false, "jet-ski": false, "jet-flyer": false,
    "four-wheel-drive": false, "sunbathing": false, "turkish-bath": false,
    "souvenir-shopping": false, "seeing-animals": false, "restaurant": false,
    "rafting": false, "badminton-court": false, "basketball-court": false,
    "tennis-court": false, "football-pitch": false, "volleyball-court": false,
    "zipline": false, "theater": false, "music-hall": false, "sledding": false,
    "sauna": false, "cinema": false, "multidimensional-cinema": false,
    "shuttle-ride": false, "swimming-with-dolphins": false,
    "amusement-park": false, "indoor-park": false, "diving": false,
    "gift-shop": false, "foot-court": false, "bubble-football": false,
    "boating": false, "karting": false, "cafe": false, "canoeing": false,
    "kayaking": false, "kiteboarding": false, "sailing": false,
    "art-gallery": false, "gamenet": false, "childrens-toys": false,
    "sports-equipment": false, "fishing": false, "walking-path": false,
    "bike-path": false, "unesco-world-heritage-site": false,
    "ping-pong-table": false, "chess-table": false, "dolphin-show": false,
    "hovercraft": false, "virtual-reality": false, "beach-volleyball": false,
    "vic-birding": false
  }},
  "special_features": {{
    "gentlemen": false, "ladies": false, "walking": false, "picnic": false,
    "tourist": false, "youth": false, "cycling": false, "day-trip": false,
    "pilgrimage": false, "nocturnal": false, "nature-tour": false,
    "photo": false, "camping": false, "children": false,
    "the-disabled": false, "sports": false
  }},
  "where_go": {{
    "zoo": false, "park": false, "history": false, "water-acs": false,
    "a-flight": false, "souvenir": false, "shopping": false, "culture": false,
    "rural-tourism": false, "beaches": false, "amusement": false,
    "circulation": false
  }},
  "occasions": {{
    "nowruz": false, "arbaeen-ceremony": false, "tasua-ceremony": false,
    "chaharshanbe-suri-ceremony": false, "chinese-new-year-ceremony": false,
    "yalda-night-ceremony": false, "martyrdom-ceremony-of-imam-reza": false,
    "ashura-ceremony": false, "eid-al-fitr-ceremony": false,
    "eid-al-adha-ceremony": false, "nowruz-eid-ceremony": false,
    "christmas-ceremony": false, "ramadan-ceremony": false,
    "safar-ceremony": false, "muharram-ceremony": false,
    "mid-shaban-ceremony": false, "halloween-ceremony": false
  }},
  "difficult_road": {{
    "south": false, "east": false, "the-north": false, "the-west": false
  }},
  "important_places": {{
    "bus-station": false, "taxi-stand": false, "railway-station": false,
    "metro-station": false, "bus-terminal": false, "gas-station": false,
    "gas-pump": false, "airport": false, "international-airport": false
  }}
}}
"""
    return prompt_template.strip()



async def generate_tourism_article(place_name, location):
    prompt = build_prompt(place_name, location)
    try:
        print('sending request')
        response = await client.chat.completions.create(
            model="grok-4.3",
            timeout=Timeout(180.0, connect=30.0),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            # stream=True
        )
        print("response", response)
        content = response.choices[0].message.content
        return {"status": "success", "data": json.loads(content)}

    except json.JSONDecodeError as e:
        logger.error(f"خطای پارس JSON برای {place_name}: {e}")
        return {"status": "error", "type": "JSON_DECODE_ERROR", "message": str(e), "raw_content": content}

    except Exception as e:
        # اینجا تمام جزئیات خطا رو می‌گیریم
        error_msg = f"خطای غیرمنتظره برای {place_name}: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "type": "API_ERROR", "message": str(e)}
async def test_connection():
    try:
        models = await client.models.list()
        print("✅ اتصال برقرار شد! مدل‌های موجود:", [m.id for m in models.data])
    except Exception as e:
        print("❌ اتصال برقرار نشد! خطا:", e)

# توی main قبل از generate، اینو صدا بزن


async def main():
    await test_connection()
    place = "عمارت عالی‌قاپو"
    city = "اصفهان"
    
    print(f"🚀 در حال تولید مقاله برای: {place} در {city} ...")
    
    # فراخوانی تابع تولید مقاله
    result = await generate_tourism_article(place, city)

    if result["status"] == "success":
        print("✅ موفقیت:", result["data"])
    else:
        print(f"❌ error type: {result['type']}")
        print(f"📌 message: {result['message']}")
        if "raw_content" in result:
            print(f"📝 متن خامِ مشکل‌دار: {result['raw_content']}")

if __name__ == "__main__":
    asyncio.run(main())
