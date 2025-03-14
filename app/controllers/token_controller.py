from flask import Blueprint, request

from app import AUTHENTICATED_ROLE
from app.annotations.authenticatedAnnotation import Authenticated
from app.annotations.requiredParamsAnnotation import RequiredParams
from app.services import jwt
from app.services.interfaces.itoken_service import TokenService
from app.utils.singleton import Singleton


class TokenController(Singleton):
    blueprint = Blueprint('token', __name__)
    service: TokenService = None

    @staticmethod
    @blueprint.route('/company/<string:company_name>/invite', methods=['GET'])
    @Authenticated(required_roles=['director'])
    @RequiredParams()
    def createInvitation(user_sub: str, expiration_minutes: int = 30, company_name: str = 'default', authentication: dict = None):
        from app.controllers.database_controller import DatabaseController
        company = DatabaseController.service.get_document('companies', {'director_sub': authentication.get('sub'), 'name': company_name})
        if company:
            return f"{request.host_url}company/{company_name}/join?token={TokenController.service.create_invitation_token(company.get('name'), user_sub, expiration_minutes)}"
        return 'Company not found or you are not director of this company'

    @staticmethod
    @blueprint.route('/company/<string:company_name>/join', methods=['GET'])
    @Authenticated(required_roles=[AUTHENTICATED_ROLE])
    @RequiredParams()
    def joinToCompany(token: str, company_name: str = 'default', authentication: dict = None):
        try:
            payload_company_name, user_sub = TokenController.service.decode_token(token)

        except jwt.ExpiredSignatureError:
            return {"error": "Token has expired."}, 401

        except jwt.InvalidTokenError:
            return {"error": "Invalid token."}, 401

        if payload_company_name == company_name and user_sub == authentication.get('sub'):
            return {"result": "Joined"}, 200
        else:
            return {"error": 'You are not allowed to join to this company'}, 403
