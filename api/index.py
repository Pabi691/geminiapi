from vertexai.preview.vision_models import ImageGenerationModel
import vertexai
import base64

# Initialize Vertex AI once
PROJECT_ID = os.getenv("GEMINI_API_KEY")
vertexai.init(project=PROJECT_ID, location="us-central1")

# Image generation route using Imagen 3.0
@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    print(f"DEBUG: Entering generate_image route. Request path: {request.path}")
    try:
        data = request.get_json()
        user_prompt = data.get('prompt')

        if not user_prompt:
            print("Error: Prompt is required for generate-image")
            return jsonify({'error': 'Prompt is required'}), 400

        # Load Imagen 3.0 model
        model = ImageGenerationModel.from_pretrained("imagen-3.0-generate-002")

        images = model.generate_images(
            prompt=user_prompt,
            number_of_images=1,
            language="en",
            aspect_ratio="1:1",
            safety_filter_level="block_some",
            person_generation="allow_adult"
        )

        image_bytes = images[0]._image_bytes  # Raw image bytes

        # Convert image to base64 for web use
        image_base64 = base64.b64encode(image_bytes).decode("utf-8")
        image_url = f"data:image/png;base64,{image_base64}"

        print(f"Image generated successfully. Size: {len(image_bytes)} bytes")
        return jsonify({'imageUrl': image_url}), 200

    except Exception as e:
        print(f"Error in generate_image: {e}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
