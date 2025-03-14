import re

import requests
from flask import Response

from app.services.interfaces.iauthentication_service import AuthenticationService


class KeyCloak(AuthenticationService):

    def __init__(self, keycloak_server, realm, client_id, client_secret, redirect_uri, admin_secret):
        self.KEYCLOAK_SERVER = keycloak_server
        self.REALM = realm
        self.CLIENT_ID = client_id
        self.CLIENT_SECRET = client_secret
        self.REDIRECT_URI = redirect_uri
        self.ADMIN_SECRET = admin_secret
        self.ADMIN_TOKEN = self.get_admin_token()

    def get_admin_token(self):
        token_url = f"{self.KEYCLOAK_SERVER}/realms/{self.REALM}/protocol/openid-connect/token"

        data = {
            'client_id': 'admin-cli',
            'client_secret': self.ADMIN_SECRET,
            'grant_type': 'client_credentials'
        }

        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.post(token_url, data=data, headers=headers)

        if response.status_code == 200:
            return response.json()['access_token']
        else:
            raise Exception("Failed to obtain admin token")

    def login(self, email: str, password: str) -> (str, str, int):
        # Keycloak token endpoint
        token_url = f"{self.KEYCLOAK_SERVER}/realms/{self.REALM}/protocol/openid-connect/token"

        # Requesting the token
        response = requests.post(token_url, data={
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET,
            'username': email,
            'password': password,
            'grant_type': 'password',
            'scope': 'openid'
        })

        if response.status_code == 200:
            return response.json()['access_token'], "", 0
        return response.text, "", response.status_code

    def logout(self, refresh_token: str):
        logout_url = f"{self.KEYCLOAK_SERVER}/realms/{self.REALM}/protocol/openid-connect/logout"
        response = requests.post(logout_url, data={
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET,
            'refresh_token': refresh_token
        })
        if response.status_code == 204:
            return "Logout successful", 0
        return response.text, response.status_code

    def callback(self, redirect_uri: str, code: str, session_state: str) -> (str, str):
        token_url = f"{self.KEYCLOAK_SERVER}/realms/{self.REALM}/protocol/openid-connect/token"

        data = {
            'grant_type': 'authorization_code',
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET,
            'code': code,
            'session_state': session_state,
            'redirect_uri': redirect_uri
        }

        response = requests.post(token_url, data=data)
        token = response.json().get('access_token', '')
        refresh_token = response.json().get('refresh_token', '')
        return token, refresh_token

    def redirect_login(self) -> str:
        return f"{self.KEYCLOAK_SERVER}/realms/{self.REALM}/protocol/openid-connect/auth?response_type=code&client_id={self.CLIENT_ID}&redirect_uri={self.REDIRECT_URI}&scope=openid"

    def redirect_register(self) -> str:
        return f"{self.KEYCLOAK_SERVER}/realms/{self.REALM}/protocol/openid-connect/registrations?response_type=code&client_id={self.CLIENT_ID}&redirect_uri={self.REDIRECT_URI}&scope=openid"

    def profile(self, token: str) -> (dict, str, int):
        user_info_url = f"{self.KEYCLOAK_SERVER}/realms/{self.REALM}/protocol/openid-connect/userinfo"

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        response = requests.get(user_info_url, headers=headers)

        return "", response.text, response.status_code

    def get_roles(self, token: str) -> dict:
        token_introspect_url = f"{self.KEYCLOAK_SERVER}/realms/{self.REALM}/protocol/openid-connect/token/introspect"

        data = {
            'token': token,
            'client_id': self.CLIENT_ID,
            'client_secret': self.CLIENT_SECRET
        }

        response = requests.post(token_introspect_url, data=data)

        return response.json()

    def get_public_info(self, sub: str) -> (dict, str, int):
        self.ADMIN_TOKEN = self.get_admin_token()
        url = f"{self.KEYCLOAK_SERVER}/admin/realms/{self.REALM}/users/{sub}"
        headers = {
            'Authorization': f'Bearer {self.ADMIN_TOKEN}',
            'Content-Type': 'application/json'
        }

        response = requests.get(url, headers=headers)
        user_data = response.json()
        return {
            "id": user_data.get("id"),
            "username": user_data.get("username"),
            "first_name": user_data.get("firstName"),
            "last_name": user_data.get("lastName"),
            "email": user_data.get("email"),
            "enabled": user_data.get("enabled"),
            "created_at": user_data.get("createdTimestamp"),
        }

    def get_public_info_by_username(self, username: str) -> (dict, str, int):
        self.ADMIN_TOKEN = self.get_admin_token()
        url = f"{self.KEYCLOAK_SERVER}/admin/realms/{self.REALM}/users?username={username}"
        headers = {
            'Authorization': f'Bearer {self.ADMIN_TOKEN}',
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers)
        return response.json()

    def redirect_profile_manage(self) -> str:
        return f"{self.KEYCLOAK_SERVER}/realms/{self.REALM}/account"
