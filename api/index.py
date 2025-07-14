import os
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# Configure Gemini
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

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

        # Correct call — no response_modality argument
        response = model.generate_content(user_prompt)

        result_text = None
        image_base64 = None

        for part in response.candidates[0].content.parts:
            if part.text is not None:
                result_text = part.text
            elif part.inline_data is not None:
                # Extract the image bytes and convert to base64
                image_bytes = part.inline_data.data
                image_base64 = base64.b64encode(image_bytes).decode("utf-8")

        if image_base64:
            return jsonify({
                "imageUrl": f"data:image/png;base64,{image_base64}",
                "text": result_text
            }), 200
        else:
            return jsonify({
                "error": "No image returned.",
                "text": result_text
            }), 500

    except Exception as e:
        print("Error in generate_image:", e)
        return jsonify({
            "error": "Internal server error",
            "details": str(e)
        }), 500

if __name__ == "__main__":
    app.run(port=5000, debug=True)
