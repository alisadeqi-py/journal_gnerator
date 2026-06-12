import os
import asyncio
from flask import Flask, request, jsonify
from flask_cors import cross_origin
from services.openai_service import generate_tourism_guide
from services.wordpress_service import send_to_wordpress

app = Flask(__name__)

API_TOKEN = os.getenv("API_TOKEN", "GAPGPT_SECRET_TOKEN_2026_ALI")

def check_auth(req):
    auth_header = req.headers.get("Authorization")
    print("auth header", auth_header)
    return auth_header == f"Bearer {API_TOKEN}"

@app.route("/generate-guide", methods=["POST", "OPTIONS"])
@cross_origin(origin="*", headers=["Content-Type", "Authorization"])
def generate_guide():

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

    grok_response = asyncio.run(
        generate_tourism_guide(place_name, location, about_lines_limit)
    )

    if extra_fields:
        grok_response.update(extra_fields)

    wp_result = asyncio.run(
        send_to_wordpress(grok_response)
    )

    return jsonify({
        "status": "success",
        "wp_response": wp_result
    })

    # except Exception as e:
    #     return jsonify({
    #         "status": "error",
    #         "message": str(e)
    #     }), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)
