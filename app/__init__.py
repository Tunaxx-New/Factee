import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from flask_pymongo import PyMongo
from urllib.parse import quote

load_dotenv()
AUTHENTICATED_ROLE = os.getenv('DEFAULT_ROLE')

from app.routes.iauthentication_route import IAuthenticationRoute
from app.services.patreon_service import PatreonService
patreon_service: PatreonService = PatreonService(os.getenv('PATREON_CLIENT_ID'),
                                                       os.getenv('PATREON_CLIENT_SECRET'),
                                                       os.getenv('PATREON_CAMPAIGN_NAME'),
                                                       os.getenv('HOST'),
                                                       os.getenv('PATREON_CLIENT_MASTER_TOKEN'))

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.secret_key = os.urandom(24)
    app.config.from_object('app.config.Config')

    from app.controllers.web_controller import web_bp
    app.register_blueprint(web_bp)

    from app.controllers.authentication_controller import AuthenticationController
    from app.services.keycloak import KeyCloak
    AuthenticationController.service = KeyCloak(os.getenv('KEYCLOAK_SERVER'),
                                                os.getenv('REALM'),
                                                os.getenv('CLIENT_ID'),
                                                os.getenv('CLIENT_SECRET'),
                                                quote("http://localhost:5000/callback", safe=''),
                                                os.getenv('KEYCLOAK_ADMIN_SECRET'))
    app.register_blueprint(AuthenticationController.blueprint)

    from app.services.mongo import Mongo
    from app.controllers.database_controller import DatabaseController
    DatabaseController.service = Mongo('Factee', 'mongodb://localhost:27017/')
    app.register_blueprint(DatabaseController.blueprint)

    from app.controllers.token_controller import TokenController
    from app.services.jwt import Jwt
    TokenController.service = Jwt(app.config.get('SECRET_KEY'))
    app.register_blueprint(TokenController.blueprint)

    from app.controllers.image_controller import ImageController
    from app.services.image_generator import ImageGenerator
    ImageController.service = ImageGenerator()
    app.register_blueprint(ImageController.blueprint)

    app.register_blueprint(patreon_service.blueprint)

    return app
