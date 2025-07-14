import os
import json
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS

import google.generativeai as genai
from google.generativeai import types


app = Flask(__name__)
CORS(app)

# ------------------------------------------------
# Gemini Configuration
# ------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is not set. API calls will likely fail.")

genai.configure(api_key=GEMINI_API_KEY)

# ------------------------------------------------
# Routes
# ------------------------------------------------

@app.route("/")
def home():
    return "API is alive!", 200

@app.route("/api/generate-image", methods=["POST"])
def generate_image():
    try:
        data = request.get_json()
        user_prompt = data.get("prompt")

        if not user_prompt:
            return jsonify({"error": "Prompt is required."}), 400

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-preview-image-generation"
        )

        # Call with proper modalities
        response = model.generate_content(
            contents=[user_prompt],
            generation_config=types.GenerationConfig(
                response_mime_type="application/json"
            ),
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="BLOCK_NONE"
                )
            ],
            # The KEY fix:
            response_modality=["TEXT", "IMAGE"]
        )

        result_text = None
        image_base64 = None

        for part in response.candidates[0].content.parts:
            if part.text is not None:
                result_text = part.text
            elif part.inline_data is not None:
                image_bytes = part.inline_data.data
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        if image_base64:
            # Return base64 Data URL
            return jsonify({
                "imageUrl": f"data:image/png;base64,{image_base64}",
                "text": result_text
            }), 200
        else:
            return jsonify({
                "error": "No image was returned.",
                "text": result_text
            }), 500

    except Exception as e:
        print(f"Error in generate_image: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# ------------------------------------------------
# Run Locally
# ------------------------------------------------

if __name__ == "__main__":
    app.run(port=5000, debug=True)
