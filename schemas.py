from pydantic import BaseModel
from typing import Optional, Dict, Any, List



class TourismRequest(BaseModel):
    place_name: str
    location: str
    about_char_limit: int = 200
    extra_fields: Optional[Dict[str, Any]] = None
    exclude_fields: Optional[List[str]] = None

class TourismResponse(BaseModel):
    status: str
    data: Any # اینجا می‌تونی مدل دقیق JSON خودت رو بسازی