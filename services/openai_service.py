import os
import json
from openai import AsyncOpenAI
from prompt_builder import build_prompt
from dotenv import load_dotenv
import json
import re

load_dotenv()

client = AsyncOpenAI(
    api_key="sk-Uhn7TyqRieHJTpPuQ0zSJKL8Wh69pZLDuTwFlIkMPE3iRufF",
    base_url='https://api.gapgpt.app/v1',
)



async def generate_tourism_guide(place_name: str, location: str, about_char_limit: int):
    prompt = build_prompt(place_name, location, about_char_limit)

    response = await client.chat.completions.create(
        model="grok-4.3",
        messages=[
            {"role": "system", "content": "Return only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content

    cleaned = re.sub(r"```json|```", "", content).strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "error": "Invalid JSON returned by model",
            "raw_content": content
        }
