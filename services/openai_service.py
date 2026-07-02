import os
import json
from openai import AsyncOpenAI
from prompt_builder import build_prompt
from dotenv import load_dotenv
import json
import re
import httpx

load_dotenv()


transport = httpx.AsyncHTTPTransport(verify=True)


client = AsyncOpenAI(
    api_key="sk-ZhCO3v19wfulZYsnLjyurOPUqHuLgtAaERZdimcjnidjBFm1",
    base_url='https://api.gapgpt.app/v1',
    http_client=httpx.AsyncClient(
        transport=transport,
        # این پارامتر حیاتیه: کلاً بررسی متغیرهای محیطی رو غیرفعال می‌کنه
        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        trust_env=False 
    )
)



async def generate_tourism_guide(place_name: str, location: str, about_char_limit: int, access_routes_cities: list = None):
    prompt = build_prompt(place_name, location, about_char_limit, access_routes_cities)

    response = await client.chat.completions.create(
        model="grok-4.3",
        messages=[
            {"role": "system", "content": "Return only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        timeout=120,
    )

    content = response.choices[0].message.content

    cleaned = re.sub(r"```json|```", "", content).strip()
    # print("returned json", json.loads(cleaned))
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "error": "Invalid JSON returned by model",
            "raw_content": content
        }
