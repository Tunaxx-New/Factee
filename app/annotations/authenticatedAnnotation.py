from functools import wraps
from flask import jsonify, session, request, redirect, url_for


def Authenticated(required_roles: list[str], is_necessary=True):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from app.controllers.authentication_controller import AuthenticationController
            from app.services.interfaces.iauthentication_service import AuthenticationService

            service: AuthenticationService = AuthenticationController.service

            token = session.get('access_token')
            if not token:
                token = request.cookies.get('access_token')

            if is_necessary:
                if not token:
                    return redirect(url_for('authentication.login', source_redirect=request.path))

            authentication: dict = service.get_roles(token)

            if authentication and not authentication.get('active', True):
                return redirect(url_for('authentication.login', source_redirect=request.path))

            if not all(role in authentication.get('realm_access', {}).get('roles', []) for role in required_roles):
                return jsonify({"message": "User does not have the required roles."}), 403

            return f(*args, authentication=authentication, **kwargs)

        return decorated_function

    return decorator
