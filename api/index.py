import os
import json
import time
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.generativeai import GenerativeModel, configure

app = Flask(__name__)
CORS(app)

@app.before_request
def log_request_path():
    print(f"DEBUG: Incoming request path: {request.path}")

# Fetch API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is not set. API calls will likely fail.")

try:
    configure(api_key=GEMINI_API_KEY)
    print("Google Generative AI configured successfully.")

    # Optional: list models to confirm access
    from google.generativeai import models
    found_gemini_pro_generate_content = False
    print("\n--- Listing available Gemini models ---")
    for m in models.list_models():
        print(f"  Model: {m.name}, Supported Methods: {m.supported_generation_methods}")
        if m.name == 'models/gemini-pro' and 'generateContent' in m.supported_generation_methods:
            found_gemini_pro_generate_content = True
    print("--- End of model list ---")
    if found_gemini_pro_generate_content:
        print("SUCCESS: models/gemini-pro supports generateContent for this key.")
    else:
        print("WARNING: models/gemini-pro does NOT support generateContent for this key/region!")
except Exception as e:
    print(f"ERROR: Failed to configure Google Generative AI or list models: {e}")

# Initialize the model
model_text = GenerativeModel(model_name="gemini-2.5-pro")

# Root route
@app.route('/', methods=['GET'])
def home():
    print(f"DEBUG: Entering home route. Request path: {request.path}")
    return "API is alive! Flask is working on Vercel.", 200

@app.route('/api/generate-design-idea', methods=['POST'])
def generate_design_idea():
    print(f"DEBUG: Entering generate_design_idea route. Request path: {request.path}")
    try:
        data = request.get_json()
        user_prompt = data.get('prompt')

        if not user_prompt:
            print("Error: Prompt is required for generate-design-idea")
            return jsonify({'error': 'Prompt is required'}), 400

        # Shortened prompt for fewer tokens
        prompt_text = (
            f"Create a short, catchy T-shirt slogan (max 10 words) about \"{user_prompt}\". "
            f"Suggest a color hex code and a font style (e.g. bold, italic) "
            f"and a font family from this list: Outfit, Dancing Script, Arial, Verdana, "
            f"Georgia, Times New Roman, Hind Siliguri, Noto Sans Bengali. "
            f"Respond ONLY as JSON with keys: slogan, color, fontStyle, fontFamily. "
            f"Example: {{\"slogan\": \"Coffee Lover\", \"color\": \"#A0522D\", "
            f"\"fontStyle\": \"bold\", \"fontFamily\": \"Outfit\"}}"
        )

        # Retry logic for 429 errors
        max_retries = 3
        retry_delay_sec = 10
        for attempt in range(1, max_retries + 1):
            try:
                response = model_text.generate_content(prompt_text)
                ai_response_text = response.text
                break
            except Exception as e:
                if "429" in str(e) or "quota" in str(e).lower():
                    if attempt < max_retries:
                        wait_time = retry_delay_sec * attempt
                        print(f"Rate limit hit. Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print("Exceeded max retries due to rate limits.")
                        return jsonify({
                            'error': 'Rate limit exceeded. Try again later.'
                        }), 429
                else:
                    raise e

        print(f"AI raw response for design idea: {ai_response_text}")

        # Parse JSON or fallback
        try:
            design_suggestion = json.loads(ai_response_text)
        except json.JSONDecodeError:
            print(f"Warning: AI response not perfect JSON for design idea: {ai_response_text}")
            # Regex extraction fallback
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

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    print(f"DEBUG: Entering generate_image route. Request path: {request.path}")
    try:
        data = request.get_json()
        user_prompt = data.get('prompt')

        if not user_prompt:
            print("Error: Prompt is required for generate-image")
            return jsonify({'error': 'Prompt is required'}), 400

        # Placeholder logic
        imageUrl = "https://via.placeholder.com/200?text=AI+Generated+Image"
        
        print(f"Returning image URL: {imageUrl}")
        return jsonify({'imageUrl': imageUrl}), 200

    except Exception as e:
        print(f"Error in generate_image: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
