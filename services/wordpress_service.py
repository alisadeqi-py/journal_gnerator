import httpx
from typing import Dict, Any

async def send_to_wordpress(data: Dict[str, Any]):
    
    # print('dataa', data)
    url = "https://safarjoore.com/wp-json/v1/create-draft-post"
    token = "sk_live_8QvN2xLp7RtY4mKa1ZcD9hJu5BwE3FsX6PnA0VrT"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status() # اگر خطا داد، متوجه بشیم
        return response.json()
