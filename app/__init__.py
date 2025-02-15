from flask import Flask
from flask_cors import CORS
from app.config.config import *

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    CORS(app, resources={r"/*": {"origins": ["https://master--aashay-jain.netlify.app", "http://localhost:3000", "https://aashay-jain.netlify.app"]}})
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.email_sender import email_sender_bp
    from app.routes.schema_manager import schema_manager_bp
    from app.routes.healthcheck import healthcheck_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(email_sender_bp, url_prefix='/email_sender')
    app.register_blueprint(schema_manager_bp, url_prefix='/schema_manager')
    app.register_blueprint(healthcheck_bp,url_prefix='/healthcheck')

    return app
