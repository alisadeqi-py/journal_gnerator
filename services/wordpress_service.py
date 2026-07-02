import httpx
from typing import Dict, Any

WORDPRESS_URL = "https://safarjoore.com/wp-json/v1/create-draft-post"
WORDPRESS_TOKEN = "sk_live_8QvN2xLp7RtY4mKa1ZcD9hJu5BwE3FsX6PnA0VrT"


async def send_to_wordpress(data: Dict[str, Any]) -> Dict[str, Any]:

    headers = {
        "Authorization": f"Bearer {WORDPRESS_TOKEN}",
        "Content-Type": "application/json"
    }
    print("post data", data)
    async with httpx.AsyncClient(
        trust_env=False,
        timeout=120.0
    ) as client:

        response = await client.post(
            WORDPRESS_URL,
            json=data,
            headers=headers
        )

        response.raise_for_status()
        return response.json()
