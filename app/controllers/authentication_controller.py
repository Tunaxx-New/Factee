import json
from collections import Counter

from flask import request, redirect, url_for, session, make_response, jsonify
from flask import Blueprint, render_template

from app import AUTHENTICATED_ROLE, patreon_service
from app.annotations.authenticatedAnnotation import Authenticated
from app.annotations.requiredParamsAnnotation import RequiredParams
from app.controllers.database_controller import DatabaseController
from app.services.interfaces.iauthentication_service import AuthenticationService
from app.utils.singleton import Singleton


class AuthenticationController(Singleton):
    blueprint = Blueprint('authentication', __name__)
    service: AuthenticationService = None

    @staticmethod
    @blueprint.route('/login', methods=['GET', 'POST'])
    @RequiredParams()
    def login(source_redirect: str = '/'):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            token, message, status = AuthenticationController.service.login(username, password)

            if token:
                # Store the token in the session
                session['access_token'] = token
                session.modified = True

                response = make_response(redirect(url_for('authentication.profile')))
                response.set_cookie('access_token', token, httponly=False, secure=True, samesite='Lax')
                return response
        session['source_redirect'] = source_redirect
        return redirect(AuthenticationController.service.redirect_login())

    @staticmethod
    @blueprint.route('/callback', methods=['GET'])
    def callback():
        if request.args.get('error'):
            return jsonify(error=request.args.get('error'), description=request.args.get('error_description'))

        session.permanent = True
        token, refresh_token = AuthenticationController.service.callback(
            f"{request.scheme}://{request.host}{request.path}",
            request.args.get('code'), request.args.get('session_state'))
        session['access_token'] = token
        response = make_response(redirect(session.get('source_redirect')))
        response.set_cookie('access_token', token, httponly=True, secure=True)
        response.set_cookie('refresh_token', refresh_token, httponly=True, secure=True)

        authentication = AuthenticationController.service.get_roles(token)
        facts, labels, prefer_type = AuthenticationController.get_user_summary(authentication.get('sub'))
        response.set_cookie('primary_color', prefer_type.get('color', ''), httponly=True, secure=True)
        response.set_cookie('username', authentication.get('username'), httponly=True, secure=True)

        return response

    @staticmethod
    @blueprint.route('/logout', methods=['GET'])
    @Authenticated(required_roles=[], is_necessary=False)
    def logout(authentication):
        """Log out the user by clearing the session and cookies."""

        # Clear session data
        session.clear()

        AuthenticationController.service.logout(request.cookies.get('refresh_token'))

        # Create response and clear cookies
        referrer = request.referrer or "/"
        if referrer.endswith("/profile"):
            referrer = f"{referrer}/{authentication.get('username', '')}"

        response = make_response(redirect(referrer))
        response.set_cookie('access_token', '', expires=0, httponly=True, secure=True)
        response.set_cookie('primary_color', '', expires=0, httponly=True, secure=True)
        response.set_cookie('username', '', expires=0, httponly=True, secure=True)
        response.set_cookie('session', '', expires=0, httponly=True, secure=True)

        return response

    @staticmethod
    @blueprint.route('/register', methods=['GET'])
    def register():
        return redirect(AuthenticationController.service.redirect_register())

    @staticmethod
    def get_user_summary(user_id):
        facts, labels = DatabaseController.service.get_user_summary(user_id)

        type_counts = Counter()
        type_info_map = {}  # Store type details by their _id
        for fact in facts:
            if fact.get("source_info"):
                for source in fact["source_info"]:
                    if source.get("type_info"):
                        for type_entry in source["type_info"]:
                            type_id = type_entry["_id"]
                            type_counts[type_id] += 1  # Count occurrences
                            type_info_map[type_id] = type_entry  # Store full type details

        if not type_counts:
            return facts, labels, {}

        most_common_type_id, _ = type_counts.most_common(1)[0]

        return facts, labels, type_info_map.get(most_common_type_id)

    @staticmethod
    @blueprint.route('/profile')
    @Authenticated(required_roles=[AUTHENTICATED_ROLE])
    def profile(authentication):
        user = AuthenticationController.service.get_public_info_by_username(authentication.get('username', '')) or []
        patreon = request.args.get('_id', None)
        if not patreon:
            patreon = patreon_service.profile(is_redirect=False)

        if len(user) <= 0:
            user = {}
        else:
            try:
                user = user[0]
            except KeyError:
                return {'data': user}, 400

        user.update(authentication)

        facts, labels, prefer_type = AuthenticationController.get_user_summary(authentication.get('sub'))

        response = make_response(render_template('profile.html',
                                               user=user,
                                               facts=facts,
                                               labels=labels,
                                               _primary_color=prefer_type.get('color', None),
                                               prefer_type=prefer_type,
                                               redirect_manage_profile=AuthenticationController.service.redirect_profile_manage(),
                                                patreon=patreon))
        response.set_cookie('primary_color', prefer_type.get('color', None), httponly=True, secure=True)
        return response

    @staticmethod
    @blueprint.route('/profile/<username>')
    def public_profile(username):
        user = AuthenticationController.service.get_public_info_by_username(username) or []
        if len(user) <= 0:
            user = {}
        else:
            try:
                user = user[0]
            except KeyError:
                return {'data': user}, 400

        user['name'] = user.get('firstName') + ' ' + user.get('lastName')

        facts, labels, prefer_type = AuthenticationController.get_user_summary(user.get('id'))

        return render_template('profile.html',
                               user=user,
                               facts=facts,
                               labels=labels,
                               _primary_color=prefer_type.get('color', None),
                               prefer_type=prefer_type,
                               isSideProfile=True)
