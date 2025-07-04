import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.generativeai import GenerativeModel, configure

# IMPORTANT: For Vercel, you DO NOT use python-dotenv or load_dotenv()
# Vercel handles environment variables securely via its dashboard.
# You will set GEMINI_API_KEY directly in Vercel's project settings.

app = Flask(__name__)
# Enable CORS for all origins during development.
# For production, consider restricting this to your frontend's domain:
# CORS(app, origins=["https://your-frontend-domain.com"]) # Replace with your actual frontend domain
CORS(app)

# Configure Google Generative AI with your API key
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # Vercel will inject this
if not GEMINI_API_KEY:
    # This check is good for local testing, but on Vercel, it should always be set
    print("Warning: GEMINI_API_KEY is not set. API calls will fail.")
    # In a production environment, you might want to raise an error or return a specific response

configure(api_key=GEMINI_API_KEY)

model_text = GenerativeModel(model_name="gemini-pro")

@app.route('/generate-design-idea', methods=['POST'])
def generate_design_idea():
    try:
        data = request.get_json()
        user_prompt = data.get('prompt')

        if not user_prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        prompt_text = f"""Generate a short, creative slogan (max 10 words) for a T-shirt about "{user_prompt}".
        Also suggest a primary color (hex code, e.g., #RRGGBB) and a font style (e.g., 'normal', 'bold', 'italic').
        Format your response strictly as a JSON object with 'slogan', 'color', 'fontStyle' and 'fontFamily' keys.
        For fontFamily, choose from 'Outfit', 'Dancing Script', 'Arial', 'Verdana', 'Georgia', 'Times New Roman', 'Hind Siliguri', 'Noto Sans Bengali'.
        Example: {{ "slogan": "Coffee Lover", "color": "#A0522D", "fontStyle": "bold", "fontFamily": "Outfit" }}"""

        response = model_text.generate_content(prompt_text)
        ai_response_text = response.text

        design_suggestion = {}
        try:
            design_suggestion = json.loads(ai_response_text)
        except json.JSONDecodeError:
            print(f"Warning: AI response not perfect JSON: {ai_response_text}")
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

        return jsonify(design_suggestion), 200

    except Exception as e:
        print(f"Error in generate_design_idea: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

@app.route('/generate-image', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        user_prompt = data.get('prompt')

        if not user_prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        # IMPORTANT: Placeholder for actual image generation logic
        # You need to integrate a real text-to-image API here (e.g., Stability AI, DALL-E 3)
        # The 'google-generativeai' library primarily focuses on text/multimodal content,
        # not direct text-to-image generation that returns image URLs for Konva.js.
        # You would typically sign up for an API key with an image generation service.

        # For demonstration purposes, we return a placeholder image URL:
        imageUrl = "https://via.placeholder.com/200?text=AI+Generated+Image" # Replace with actual image URL from your AI service

        return jsonify({'imageUrl': imageUrl}), 200

    except Exception as e:
        print(f"Error in generate_image: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

# Vercel needs a `handler` function for serverless functions
# The Flask `app` object is usually sufficient for Vercel to detect it as the WSGI application.
# No need for `if __name__ == '__main__':` block for Vercel deployment.
