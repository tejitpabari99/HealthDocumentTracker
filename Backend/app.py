"""
Main Flask application file
Imports and registers blueprints for different API endpoints
"""
from flask import Flask, jsonify
from flask_cors import CORS
import os

# Import blueprints
from Backend.upload import upload_bp
from Backend.search import search_bp

# Initialize Flask application
app = Flask(__name__)

# Enable CORS for all routes
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Allow all origins (change this to specific origins in production)
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Register blueprints
app.register_blueprint(upload_bp)
app.register_blueprint(search_bp)

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    return jsonify({'message': 'Welcome to the Health Document Tracker API'}), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'HealthDocumentTracker'}), 200

if __name__ == '__main__':
    # Run the Flask application
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
