import json
import os
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
    def login(source_redirect: str = None):
        """
        Login get web and post authentication
        ---
        parameters:
          - name: source_redirect
            in: path
            type: string
            required: false
            description: Source redirect to 302 requests
          - name: username
            in: path
            type: string
            required: false
            description: username
          - name: password
            in: path
            type: string
            required: false
            description: password
        responses:
          200:
            description: redirecting to authentication service or rendered page
        """
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']

            token, message, status = AuthenticationController.service.login(username, password)

            if token:
                # Store the token in the session
                session['access_token'] = token
                session.modified = True

                response = make_response(redirect(url_for('authentication.profile')))
                response.set_cookie('access_token', token, httponly=True, secure=True, samesite='Lax')
                return response
        session['source_redirect'] = source_redirect or request.referrer
        return redirect(AuthenticationController.service.redirect_login())

    @staticmethod
    @blueprint.route('/callback', methods=['GET'])
    def callback():
        """
        Callback get to redirect from authentication service, saves token, saves cookies
        ---
        responses:
          200:
            description: redirecting to saved source_redirect in session
        """
        if request.args.get('error'):
            return jsonify(error=request.args.get('error'), description=request.args.get('error_description'))

        session.permanent = True
        token, refresh_token = AuthenticationController.service.callback(
            f"{os.getenv('HOST')}{request.path}",
            request.args.get('code'), request.args.get('session_state'))
        session['access_token'] = token
        response = make_response(redirect(session.get('source_redirect')))
        response.set_cookie('access_token', token, httponly=True, secure=True, samesite='Lax')
        response.set_cookie('refresh_token', refresh_token, httponly=True, secure=True, samesite='Lax')

        authentication = AuthenticationController.service.get_roles(token)
        if not authentication.get('active', True):
            return response

        facts, labels, prefer_type = AuthenticationController.get_user_summary(authentication.get('sub'))
        response.set_cookie('primary_color', prefer_type.get('color', '#000000'), httponly=True, secure=True, samesite='Lax')
        response.set_cookie('username', authentication.get('username'), httponly=True, secure=True, samesite='Lax')

        return response

    @staticmethod
    @blueprint.route('/logout', methods=['GET'])
    @Authenticated(required_roles=[], is_necessary=False)
    def logout(authentication):
        """
        Log out the user by clearing the session and cookies.
        ---
        tags:
          - authenticated
        responses:
          200:
            description: render some referrer page and clears cookies with session
        """

        # Clear session data
        session.clear()

        AuthenticationController.service.logout(request.cookies.get('refresh_token'))

        # Create response and clear cookies
        referrer = request.referrer or "/"
        if referrer.endswith("/profile"):
            referrer = f"{referrer}/{authentication.get('username', '')}"

        allowed_hosts = [os.getenv('HOST')]
        if referrer and any(
                referrer.startswith(f"{host}") for host in
                allowed_hosts):
            response = make_response(redirect(referrer))
        else:
            response = make_response(redirect(url_for('web.home')))

        response.set_cookie('access_token', '', expires=0, httponly=True, secure=True, samesite='Lax')
        response.set_cookie('primary_color', '', expires=0, httponly=True, secure=True, samesite='Lax')
        response.set_cookie('username', '', expires=0, httponly=True, secure=True, samesite='Lax')
        response.set_cookie('session', '', expires=0, httponly=True, secure=True, samesite='Lax')

        return response

    @staticmethod
    @blueprint.route('/register', methods=['GET'])
    def register():
        """
        Register redirect page
        ---
        responses:
          200:
            description: redirecting to service authentication register page
        """
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
        """
        Getting current user data and collecting into profile
        ---
        tags:
          - authenticated
        parameters:
          - name: _id
            in: path
            type: string
            required: false
            description: Patreon _id
        responses:
          200:
            description: renders current user profile
          400:
            description: User not found and not logged in
        """
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
                                               _primary_color=prefer_type.get('color', '#000000'),
                                               prefer_type=prefer_type,
                                               redirect_manage_profile=AuthenticationController.service.redirect_profile_manage(),
                                               patreon=patreon))
        response.set_cookie('primary_color', prefer_type.get('color', '#000000'), httponly=True, secure=True, samesite='Lax')
        return response

    @staticmethod
    @blueprint.route('/profile/<username>')
    def public_profile(username):
        """
        Getting user data and collecting into profile
        ---
        parameters:
          - name: username
            in: path
            type: string
            required: true
            description: User name
        responses:
          200:
            description: renders user profile
          400:
            description: user with id not found
        """
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
                               _primary_color=prefer_type.get('color', '#000000'),
                               prefer_type=prefer_type,
                               isSideProfile=True)
