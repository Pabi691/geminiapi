import os
from vertexai.preview.vision_models import ImageGenerationModel
import vertexai
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

# Initialize Vertex AI
vertexai.init(project="disco-mountain-396008", location="us-central1")

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get('prompt')
        if not prompt:
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
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
