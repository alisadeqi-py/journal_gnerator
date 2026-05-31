from pydantic import BaseModel
from typing import Optional, Dict, Any



class TourismRequest(BaseModel):
    place_name: str
    location: str
    about_char_limit: int = 200
    # این فیلد برای overrides استفاده میشه
    extra_fields: Optional[Dict[str, Any]] = None

class TourismResponse(BaseModel):
    status: str
    data: Any # اینجا می‌تونی مدل دقیق JSON خودت رو بسازی