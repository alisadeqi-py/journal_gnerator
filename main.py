import base64
import io
import os
import asyncio
import httpx
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from asgiref.wsgi import WsgiToAsgi
from openai import OpenAI
from PIL import Image
from services.openai_service import generate_tourism_guide
from services.wordpress_service import send_to_wordpress

app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB
asgi_app = WsgiToAsgi(app)

API_TOKEN = os.getenv("API_TOKEN", "GAPGPT_SECRET_TOKEN_2026_ALI")

_vision_client = OpenAI(
    api_key=os.environ.get("GAPGPT_API_KEY", "sk-ZhCO3v19wfulZYsnLjyurOPUqHuLgtAaERZdimcjnidjBFm1"),
    base_url=os.environ.get("GAPGPT_BASE_URL", "https://api.gapgpt.app/v1"),
    http_client=httpx.Client(trust_env=False),
)
_VISION_MODEL = os.environ.get("GAPGPT_MODEL", "gpt-5.3-chat-latest")
_VISION_ALLOWED = {"png", "jpg", "jpeg", "webp", "gif"}
_VISION_SYSTEM = (
    "You are an SEO expert. Given an image, write exactly one line of SEO-friendly "
    "alt text / description for it: concise, descriptive, keyword-rich, no more than "
    "15 words, no quotes, no trailing period, plain text only."
)

def _allowed_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in _VISION_ALLOWED

def _describe_image(image_bytes, mime_type):
    data_url = f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode()}"
    response = _vision_client.chat.completions.create(
        model=_VISION_MODEL,
        messages=[
            {"role": "system", "content": _VISION_SYSTEM},
            {"role": "user", "content": [
                {"type": "text", "text": "Describe this image for SEO in one line. IN FARSI."},
                {"type": "image_url", "image_url": {"url": data_url}},
            ]},
        ],
    )
    return response.choices[0].message.content.strip()

def check_auth(req):
    auth_header = req.headers.get("Authorization")
    print("auth header", auth_header)
    return auth_header == f"Bearer {API_TOKEN}"

def remove_fields(data, fields):
    if isinstance(data, dict):
        for field in fields:
            data.pop(field, None)
        for value in data.values():
            remove_fields(value, fields)
    elif isinstance(data, list):
        for item in data:
            remove_fields(item, fields)

@app.route("/generate-guide", methods=["POST", "OPTIONS"])
async def generate_guide():

    if not check_auth(request):
        return jsonify({
            "status": "error",
            "message": "Unauthorized"
        }), 401

    # try:
    data = request.get_json()

    place_name = data.get("place_name")
    location = data.get("location")
    about_lines_limit = data.get("about_char_limit", 500)
    extra_fields = data.get("extra_fields", {})
    exclude_fields = data.get("exclude_fields", [])
    writer_id = data.get("writerID")
    access_routes_cities = data.get("access_routes_cities", [])
    print("writer_id", writer_id)
    print("access_routes_cities", access_routes_cities)

    grok_response = await generate_tourism_guide(place_name, location, about_lines_limit, access_routes_cities)

    if writer_id is not None:
        grok_response["author"] = writer_id

    if extra_fields:
        grok_response.update(extra_fields)

    if exclude_fields:
        remove_fields(grok_response, exclude_fields)

    asyncio.ensure_future(send_to_wordpress(grok_response))

    return jsonify({
        "status": "success",
        "writerID": writer_id,
        "message": "journal created"
    })

    # except Exception as e:
    #     return jsonify({
    #         "status": "error",
    #         "message": str(e)
    #     }), 500


@app.route("/resize-image", methods=["POST", "OPTIONS"])
def resize_image():

    if not check_auth(request):
        return jsonify({
            "status": "error",
            "message": "Unauthorized"
        }), 401

    if "image" not in request.files:
        return jsonify({
            "status": "error",
            "message": "No image uploaded"
        }), 400

    try:
        image_file = request.files["image"]
        filename = image_file.filename

        width = request.form.get("width")
        height = request.form.get("height")

        if not width or not height:
            return jsonify({
                "status": "error",
                "message": "width and height are required"
            }), 400

        width = int(width)
        height = int(height)

        image = Image.open(image_file)
        resized = image.resize((width, height))

        img_io = io.BytesIO()

        if resized.mode in ("RGBA", "P"):
            resized = resized.convert("RGB")

        resized.save(img_io, format="JPEG", quality=90)
        img_io.seek(0)

        return send_file(
            img_io,
            mimetype="image/jpeg",
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if not check_auth(request):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    files = [f for f in request.files.getlist("image") if f and f.filename]
    if not files:
        return jsonify({"error": "no image provided"}), 400

    results = {}
    for file in files:
        if not _allowed_image(file.filename):
            results[file.filename] = {"error": "unsupported file type"}
            continue
        try:
            results[file.filename] = {"seo_text": _describe_image(file.read(), file.mimetype or "image/jpeg")}
        except Exception as exc:
            results[file.filename] = {"error": str(exc)}

    return jsonify({"results": results})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
