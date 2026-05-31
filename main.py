from fastapi import FastAPI, HTTPException, status
from schemas import TourismRequest, TourismRequest
from services.openai_service import generate_tourism_guide
from services.wordpress_service import send_to_wordpress

app = FastAPI(title="GapGPT Tourism API", description="سرویس هوشمند تولید محتوای گردشگری")

@app.post("/generate-guide")
async def generate_guide(request: TourismRequest):
    # ۱. تولید اولیه با گروک
    grok_response = await generate_tourism_guide(
        request.place_name, request.location, request.about_char_limit
    )
    
    # ۲. ادغام (Merge) داده‌های سفارشی کلاینت
    if request.extra_fields:
        # نکته: اگر فیلدها تودرتو (Nested) هستند، باید از deep_merge استفاده کنی
        # اینجا یک ادغام ساده در سطح اول انجام دادیم
        grok_response.update(request.extra_fields)
    
    # ۳. ارسال به وردپرس
    try:
        wp_result = await send_to_wordpress(grok_response)
        return {"status": "success", "wp_response": wp_result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn
    # برای اجرای کد: uvicorn main:app --reload
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
