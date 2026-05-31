import os
import json
from openai import AsyncOpenAI
from prompt_builder import build_prompt
from dotenv import load_dotenv

load_dotenv()

client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url='https://api.gapgpt.app/v1',
)

async def generate_tourism_guide(place_name: str, location: str, about_char_limit: int):
    # ۱. ساخت پرامپت
    prompt = build_prompt(place_name, location, about_char_limit)
    print('build prompt', prompt)
    # ۲. فراخوانی API
    response = await client.chat.completions.create(
        model="grok-4.3",
        messages=[
            {"role": "user", "content": prompt}  # اینجا باید اون پرامپت بزرگ رو بفرستی
        ],
        temperature=0.2, # برای کارهای دقیق، تمپرچر پایین بهتره
    )
    # ۳. پارس کردن خروجی
    content = response.choices[0].message.content
    return json.loads(content)
