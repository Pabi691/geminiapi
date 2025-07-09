# api/index.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import os # Keep os for checking env var if you want, but simplify

app = Flask(__name__)
CORS(app) # Allow all origins for this test

# A simple root route to see if the app is even alive
@app.route('/', methods=['GET'])
def home():
    print("Received GET request for /")
    return "API is alive! Flask is working on Vercel.", 200

# Your original API routes, but with simplified responses for testing
@app.route('/generate-design-idea', methods=['POST'])
def generate_design_idea_test():
    print("Received POST request for /generate-design-idea")
    try:
        data = request.get_json()
        prompt = data.get('prompt', 'no prompt provided')
        return jsonify({
            'message': f'Hello from generate-design-idea! Prompt: {prompt}',
            'status': 'success'
        }), 200
    except Exception as e:
        print(f"Error in generate_design_idea_test: {e}")
        return jsonify({'error': 'Internal server error during test', 'details': str(e)}), 500

@app.route('/generate-image', methods=['POST'])
def generate_image_test():
    print("Received POST request for /generate-image")
    try:
        data = request.get_json()
        prompt = data.get('prompt', 'no prompt provided')
        return jsonify({
            'message': f'Hello from generate-image! Prompt: {prompt}',
            'imageUrl': 'https://via.placeholder.com/150?text=TestImage'
        }), 200
    except Exception as e:
        print(f"Error in generate_image_test: {e}")
        return jsonify({'error': 'Internal server error during test', 'details': str(e)}), 500

# No if __name__ == '__main__': block for Vercel
