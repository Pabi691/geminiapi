import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.generativeai import GenerativeModel, configure

app = Flask(__name__)
CORS(app) # Allow all origins for now

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("WARNING: GEMINI_API_KEY is not set. API calls will likely fail.")
    # For robust production, you might raise an error here
    # or return an error response, e.g.:
    # return jsonify({'error': 'Server configuration error: API key missing'}), 500

try:
    configure(api_key=GEMINI_API_KEY)
    print("Google Generative AI configured successfully.")
except Exception as e:
    print(f"ERROR: Failed to configure Google Generative AI: {e}")
    # Consider handling this more gracefully if you want the app to partially work

model_text = GenerativeModel(model_name="gemini-pro")

# Your simple root route (optional, but good for health checks)
@app.route('/', methods=['GET'])
def home():
    print("Received GET request for /")
    return "API is alive! Flask is working on Vercel.Working.", 200

@app.route('/generate-design-idea', methods=['POST'])
def generate_design_idea():
    print("Received request for /generate-design-idea")
    try:
        data = request.get_json()
        user_prompt = data.get('prompt')

        if not user_prompt:
            print("Error: Prompt is required for generate-design-idea")
            return jsonify({'error': 'Prompt is required'}), 400

        prompt_text = f"""Generate a short, creative slogan (max 10 words) for a T-shirt about "{user_prompt}".
        Also suggest a primary color (hex code, e.g., #RRGGBB) and a font style (e.g., 'normal', 'bold', 'italic').
        Format your response strictly as a JSON object with 'slogan', 'color', 'fontStyle' and 'fontFamily' keys.
        For fontFamily, choose from 'Outfit', 'Dancing Script', 'Arial', 'Verdana', 'Georgia', 'Times New Roman', 'Hind Siliguri', 'Noto Sans Bengali'.
        Example: {{ "slogan": "Coffee Lover", "color": "#A0522D", "fontStyle": "bold", "fontFamily": "Outfit" }}"""

        response = model_text.generate_content(prompt_text)
        ai_response_text = response.text
        print(f"AI raw response for design idea: {ai_response_text}") # Log raw AI response

        design_suggestion = {}
        try:
            design_suggestion = json.loads(ai_response_text)
        except json.JSONDecodeError:
            print(f"Warning: AI response not perfect JSON for design idea: {ai_response_text}")
            import re
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

@app.route('/generate-image', methods=['POST'])
def generate_image():
    print("Received request for /generate-image")
    try:
        data = request.get_json()
        user_prompt = data.get('prompt')

        if not user_prompt:
            print("Error: Prompt is required for generate-image")
            return jsonify({'error': 'Prompt is required'}), 400

        # IMPORTANT: Placeholder for actual image generation logic
        # You need to integrate a real text-to-image API here (e.g., Stability AI, DALL-E 3)
        # The 'google-generativeai' library primarily focuses on text/multimodal content,
        # not direct text-to-image generation that returns image URLs for Konva.js.
        # You would typically sign up for an API key with an image generation service.

        # For demonstration purposes, we return a placeholder image URL:
        imageUrl = "https://via.placeholder.com/200?text=AI+Generated+Image" # Replace with actual image URL from your AI service
        
        print(f"Returning image URL: {imageUrl}")
        return jsonify({'imageUrl': imageUrl}), 200

    except Exception as e:
        print(f"Error in generate_image: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
