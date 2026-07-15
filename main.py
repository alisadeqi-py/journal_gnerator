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
app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024  # 50 MB
Image.MAX_IMAGE_PIXELS = None
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
        print(f"[resize] received file: {filename}, mimetype: {image_file.mimetype}")

        width = request.form.get("width")
        height = request.form.get("height")
        print(f"[resize] requested dimensions: width={width}, height={height}")

        if not width or not height:
            print("[resize] missing width or height — rejecting")
            return jsonify({
                "status": "error",
                "message": "width and height are required"
            }), 400

        width = int(width)
        height = int(height)

        with Image.open(io.BytesIO(image_file.read())) as image:
            image.load()
            print(f"[resize] original size: {image.size}, mode: {image.mode}")

            resized = image.resize((width, height))

            if resized.mode in ("RGBA", "P"):
                print(f"[resize] converting mode {resized.mode} -> RGB")
                resized = resized.convert("RGB")

            img_io = io.BytesIO()
            resized.save(img_io, format="JPEG", quality=90)
            resized.close()

        size_kb = img_io.tell() / 1024
        img_io.seek(0)
        print(f"[resize] done — output size: {size_kb:.1f} KB, sending as {filename}")

        return send_file(
            img_io,
            mimetype="image/jpeg",
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"[resize] error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/compress-image", methods=["POST", "OPTIONS"])
def compress_image():
    if not check_auth(request):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    if "image" not in request.files:
        return jsonify({"status": "error", "message": "No image uploaded"}), 400

    try:
        image_file = request.files["image"]
        filename = image_file.filename
        image_bytes = image_file.read()
        original_size = len(image_bytes)

        print(f"[compress] ── INPUT ──────────────────────────")
        print(f"[compress]   filename : {filename}")
        print(f"[compress]   mimetype : {image_file.mimetype}")
        print(f"[compress]   size     : {original_size / 1024 / 1024:.2f} MB ({original_size:,} bytes)")

        limit = 5 * 1024 * 1024  # 5 MB

        if original_size <= limit:
            print(f"[compress] ── OUTPUT ─────────────────────────")
            print(f"[compress]   already under 5 MB — returning as-is")
            print(f"[compress]   size     : {original_size / 1024 / 1024:.2f} MB")
            print(f"[compress] ──────────────────────────────────")
            return send_file(
                io.BytesIO(image_bytes),
                mimetype=image_file.mimetype or "image/jpeg",
                as_attachment=True,
                download_name=filename
            )

        with Image.open(io.BytesIO(image_bytes)) as image:
            image.load()
            print(f"[compress]   dimensions: {image.size[0]}x{image.size[1]} px")
            print(f"[compress]   mode     : {image.mode}")

            if image.mode in ("RGBA", "P"):
                print(f"[compress]   converting {image.mode} → RGB")
                image = image.convert("RGB")

            print(f"[compress] ── COMPRESSING ───────────────────")
            best_buf = None
            best_quality = None
            for quality in range(95, 9, -5):
                buf = io.BytesIO()
                image.save(buf, format="JPEG", quality=quality, optimize=True)
                size = buf.tell()
                print(f"[compress]   quality={quality:>3} → {size / 1024 / 1024:.2f} MB ({size:,} bytes)")
                if size <= limit:
                    best_buf = buf
                    best_quality = quality
                    break

            if best_buf is None:
                buf = io.BytesIO()
                image.save(buf, format="JPEG", quality=10, optimize=True)
                best_buf = buf
                best_quality = 10
                print(f"[compress]   could not reach 5 MB even at quality=10 — returning best effort")

        best_buf.seek(0)
        final_size = best_buf.getbuffer().nbytes
        reduction = (1 - final_size / original_size) * 100

        print(f"[compress] ── OUTPUT ─────────────────────────")
        print(f"[compress]   filename : {filename}")
        print(f"[compress]   quality  : {best_quality}")
        print(f"[compress]   size     : {final_size / 1024 / 1024:.2f} MB ({final_size:,} bytes)")
        print(f"[compress]   reduced  : {reduction:.1f}%")
        print(f"[compress] ──────────────────────────────────")

        return send_file(
            best_buf,
            mimetype="image/jpeg",
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        print(f"[compress] error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


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
