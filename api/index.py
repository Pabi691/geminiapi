import os
import json
import tempfile
import base64

from flask import Flask, request, jsonify
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

app = Flask(__name__)

# === Step 1: Decode service account JSON and save it to a temp file ===
creds_b64 = os.environ.get("GOOGLE_CREDENTIALS_BASE64")
if not creds_b64:
    raise Exception("Missing GOOGLE_CREDENTIALS_BASE64 environment variable")

# Decode and write the credentials to a temporary file
creds_json = base64.b64decode(creds_b64).decode("utf-8")
temp_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
with open(temp_file_path, "w") as f:
    f.write(creds_json)

# Point to the temp file for Google SDK auth
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_file_path

# === Step 2: Initialize Vertex AI ===
vertexai.init(project="disco-mountain-396008", location="us-central1")


# === Step 3: Define the image generation route ===
import logging

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        if not prompt:
            logging.error("No prompt provided")
            return jsonify({'error': 'Prompt is required'}), 400

        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")
        images = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            language="en",
            aspect_ratio="1:1",
            safety_filter_level="block_some",
            person_generation="allow_adult"
        )

        image_bytes = images[0]._image_bytes
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        image_url = f"data:image/png;base64,{image_base64}"

        return jsonify({'imageUrl': image_url}), 200

    except Exception as e:
        logging.exception("Internal server error")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


# === Optional: local run for testing ===
if __name__ == '__main__':
    app.run(debug=True)
