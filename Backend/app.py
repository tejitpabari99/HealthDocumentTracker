"""
Main Flask application file
Imports and registers blueprints for different API endpoints
"""
from flask import Flask, jsonify
from flask_cors import CORS
import os

# Import logging utilities
from Backend.utils.logger import setup_logging, get_logger
from Backend.utils.middleware import setup_request_logging, setup_authentication

# Initialize logging BEFORE anything else
setup_logging()
logger = get_logger(__name__)

# Import blueprints from api package
from Backend.api.search import search_bp
from Backend.api.users import users_bp
from Backend.api.documents import documents_bp
from Backend.api.search_activity import search_activity_bp

# Initialize Flask application
app = Flask(__name__)

# Setup authentication middleware (extracts user_id from request)
setup_authentication(app)
logger.info("Authentication middleware enabled")

# Setup request/response logging middleware
setup_request_logging(app)

logger.info("Flask application initialized")

# Enable CORS for all routes
CORS(app, resources={
    r"/*": {
        "origins": "*",  # Allow all origins (change this to specific origins in production)
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
logger.info("CORS enabled for all routes")

# Register blueprints
app.register_blueprint(search_bp)
logger.info("Registered blueprint: search")

app.register_blueprint(users_bp)
logger.info("Registered blueprint: users")

app.register_blueprint(documents_bp)
logger.info("Registered blueprint: documents")

app.register_blueprint(search_activity_bp)
logger.info("Registered blueprint: search_activity")

@app.route('/', methods=['GET'])
def index():
    """Root endpoint"""
    logger.debug("Root endpoint accessed")
    return jsonify({'message': 'Welcome to the Health Document Tracker API'}), 200

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    logger.debug("Health check endpoint accessed")
    return jsonify({'status': 'healthy', 'service': 'HealthDocumentTracker'}), 200

if __name__ == '__main__':
    # Run the Flask application
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Flask application on port {port} (debug={debug})")
    app.run(host='0.0.0.0', port=port, debug=debug)
