import os
import json
import time
import re
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS

import google.generativeai as genai
from google.generativeai import types

# -------------------------------
# Flask App
# -------------------------------

app = Flask(__name__)
CORS(app)

@app.before_request
def log_request_path():
    print(f"DEBUG: Incoming request path: {request.path}")

# -------------------------------
# Gemini Configuration
# -------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is not set. API calls will likely fail.")

# Configure Gemini SDK
genai.configure(api_key=GEMINI_API_KEY)

# -------------------------------
# Root
# -------------------------------

@app.route('/', methods=['GET'])
def home():
    print(f"DEBUG: Entering home route. Request path: {request.path}")
    return "API is alive! Flask is working on Vercel.", 200

# -------------------------------
# Generate Design Idea (Text)
# -------------------------------

@app.route('/api/generate-design-idea', methods=['POST'])
def generate_design_idea():
    print(f"DEBUG: Entering generate_design_idea route. Request path: {request.path}")
    try:
        data = request.get_json()
        user_prompt = data.get('prompt')

        if not user_prompt:
            print("Error: Prompt is required for generate-design-idea")
            return jsonify({'error': 'Prompt is required'}), 400

        prompt_text = (
            f"Create a short, catchy T-shirt slogan (max 10 words) about \"{user_prompt}\". "
            f"Suggest a color hex code and a font style (e.g. bold, italic) "
            f"and a font family from this list: Outfit, Dancing Script, Arial, Verdana, "
            f"Georgia, Times New Roman, Hind Siliguri, Noto Sans Bengali. "
            f"Respond ONLY as JSON with keys: slogan, color, fontStyle, fontFamily. "
            f"Example: {{\"slogan\": \"Coffee Lover\", \"color\": \"#A0522D\", "
            f"\"fontStyle\": \"bold\", \"fontFamily\": \"Outfit\"}}"
        )

        model = genai.GenerativeModel("gemini-2.5-pro")

        response = model.generate_content(
            contents=prompt_text
        )
        ai_response_text = response.candidates[0].content.parts[0].text

        print(f"AI raw response for design idea: {ai_response_text}")

        try:
            design_suggestion = json.loads(ai_response_text)
        except json.JSONDecodeError:
            print(f"Warning: AI response not perfect JSON for design idea: {ai_response_text}")
            slogan_match = re.search(r'"slogan"\s*:\s*"(.*?)"', ai_response_text)
            color_match = re.search(r'"color"\s*:\s*"(#[\da-fA-F]{6})"', ai_response_text)
            font_style_match = re.search(r'"fontStyle"\s*:\s*"(.*?)"', ai_response_text)
            font_family_match = re.search(r'"fontFamily"\s*:\s*"(.*?)"', ai_response_text)

            design_suggestion = {
                "slogan": slogan_match.group(1) if slogan_match else "Creative Slogan",
                "color": color_match.group(1) if color_match else "#000000",
                "fontStyle": font_style_match.group(1) if font_style_match else "normal",
                "fontFamily": font_family_match.group(1) if font_family_match else "Outfit"
            }

        print(f"Returning design suggestion: {design_suggestion}")
        return jsonify(design_suggestion), 200

    except Exception as e:
        print(f"Error in generate_design_idea: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# -------------------------------
# Generate Image
# -------------------------------

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    print(f"DEBUG: Entering generate_image route. Request path: {request.path}")
    try:
        data = request.get_json()
        user_prompt = data.get('prompt')

        if not user_prompt:
            print("Error: Prompt is required for generate-image")
            return jsonify({'error': 'Prompt is required'}), 400

        # Note: The 'gemini-2.0-flash-preview-001' model is NOT designed for direct
        # text-to-image generation output via response_mime_type="image/png".
        # It's primarily for text responses, even with multi-modal inputs.
        # To generate images, you need a dedicated image generation API/service.

        model = genai.GenerativeModel("gemini-2.0-flash-preview-001")

        response = model.generate_content(
            contents=[user_prompt]
            # Removed: generation_config because 'image/png' is not an allowed output MIME type for this model.
            # This model will generate text, not a direct image.
        )

        image_base64 = None
        generated_text_response = None

        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                # This block will likely NOT be reached as this model doesn't output inline_data for text-to-image
                image_bytes = part.inline_data.data
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                print("DEBUG: Image data received (unlikely with this model/config).")
                break
            elif part.text is not None:
                generated_text_response = part.text
                print(f"DEBUG: Model returned text response: {generated_text_response}")
                break # Get the first text part and break

        if image_base64:
            # If by some chance image data IS received (e.g., if model capabilities change or for other model types)
            image_url = f"data:image/png;base64,{image_base64}"
            print(f"DEBUG: Generated image data URL length: {len(image_url)}")
            return jsonify({"imageUrl": image_url}), 200
        else:
            # This path is the most likely outcome with gemini-2.0-flash-preview-001
            print(f"ERROR: Image generation not supported. Model provided text or no image data.")
            return jsonify({
                "error": "Image generation not directly supported by the current model with this configuration.",
                "details": "The 'gemini-2.0-flash-preview-001' model does not output images directly. "
                           "It is primarily a text-generating model. If you need text-to-image functionality, "
                           "please use a dedicated image generation API (e.g., Google Cloud's Imagen, DALL-E, Stable Diffusion).",
                "model_text_response": generated_text_response # Return any text response from the model
            }), 500

    except Exception as e:
        print(f"Error in generate_image: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# -------------------------------
# Run Locally
# -------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
