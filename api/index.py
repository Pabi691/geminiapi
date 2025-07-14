import os
import json
import time
import re
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS

import google.generativeai as genai
from google.generativeai import types # Corrected import from previous step

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

# IMPORTANT CHANGE: Remove the client = genai.Client() line.
# The google.generativeai library is designed to be used directly through the 'genai' module
# or by creating model instances like genai.GenerativeModel().
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

        # IMPORTANT CHANGE: Get the model instance directly from genai
        model = genai.GenerativeModel("gemini-2.5-pro")

        # Call Gemini text model using the model instance
        response = model.generate_content( # Changed from client.models.generate_content
            contents=prompt_text
        )
        ai_response_text = response.candidates[0].content.parts[0].text

        print(f"AI raw response for design idea: {ai_response_text}")

        # Try parsing JSON
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

        # IMPORTANT CHANGE: Get the model instance directly from genai
        # For image generation, the model name is different.
        model = genai.GenerativeModel("gemini-2.0-flash-preview-001") # Using a stable image model name

        # Call Gemini image model using the model instance
        response = model.generate_content( # Changed from client.models.generate_content
            contents=[user_prompt], # Contents should be a list of parts, if it's just text, it can be [user_prompt]
            generation_config=types.GenerationConfig( # IMPORTANT: Changed 'config' to 'generation_config'
                response_mime_type="image/png" # IMPORTANT: Use response_mime_type for direct image output
            )
        )

        image_base64 = None

        for part in response.candidates[0].content.parts:
            # Check for inline_data to get the image
            if part.inline_data is not None:
                image_bytes = part.inline_data.data
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")
                break # Once image is found, break the loop
            elif part.text is not None:
                # Log any text responses, but we expect an image here
                print("Model text (unexpected for image output):", part.text)


        if not image_base64:
            print("Error: No image base64 data found in Gemini response.")
            return jsonify({"error": "No image generated."}), 500

        # Create a data URL
        image_url = f"data:image/png;base64,{image_base64}"
        print(f"Generated image data URL length: {len(image_url)}")

        return jsonify({"imageUrl": image_url}), 200

    except Exception as e:
        print(f"Error in generate_image: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# -------------------------------
# Run Locally
# -------------------------------

if __name__ == "__main__":
    app.run(debug=True, port=5000)
