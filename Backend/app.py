"""
Main Flask application file
Imports and registers blueprints for different API endpoints
"""
from flask import Flask, jsonify
import os

# Import blueprints
from Backend.upload import upload_bp
from Backend.search import search_bp
from Backend.delete import delete_bp

# Initialize Flask application
app = Flask(__name__)

# Register blueprints
app.register_blueprint(upload_bp)
app.register_blueprint(search_bp)
app.register_blueprint(delete_bp)

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
