from openai import OpenAI
from httpx import Timeout


# ایجاد یک نمونه از کلاینت با کلید API خود
client = OpenAI(base_url='https://api.gapgpt.app/v1', api_key='sk-Q3CyQKPJUeyQBseDAmUQelUMmu13PkEvNfnG0yeMKJpW996I')

response = client.chat.completions.create(
    model="gpt-4o",
    timeout=Timeout(120.0, connect=10.0),
    messages=[
        {"role": "user", "content": "سلام!"}
    ]
)

print(response.choices[0].message.content)