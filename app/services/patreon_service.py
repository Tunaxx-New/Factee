import urllib

from flask import session, redirect, url_for, request, make_response
import requests
from requests_oauthlib import OAuth2Session
from oauthlib.oauth2 import BackendApplicationClient

from app.annotations.authenticatedAnnotation import Authenticated
from app.routes.iauthentication_route import IAuthenticationRoute
from app.services.interfaces.idonation_service import IDonationService


class PatreonService(IDonationService, IAuthenticationRoute):
    def __init__(self, client_id, client_secret, name, host, master_token):
        self.PATREON_REDIRECT_URI = f'{host}/{self.path}/callback'
        self.AUTHENTICATION_URL = 'https://www.patreon.com/oauth2/authorize'
        super().__init__()

        self.CLIENT_ID = client_id
        self.CLIENT_SECRET = client_secret
        self.PATREON_API_URL = 'https://www.patreon.com/api/oauth2/v2/campaigns'
        self.TOKEN_URL = 'https://www.patreon.com/api/oauth2/token'
        self.NAME = name

        self.token = master_token
        self.campaigns_id = self.get_campaigns(self.token)

    def get_subscribers(self) -> list[dict]:
        data = self.get_subscribers_data()

        subscribers = []
        for patron in data:
            subscribers.append((patron.get('relationships').get('user').get('data').get('id'), patron.get('attributes').get('currently_entitled_amount_cents')))

        return subscribers

    def get_user_cents(self) -> int:
        current_user = self.profile(is_redirect=False)
        users = self.get_subscribers()
        for user in users:
            if current_user.get('data', {}).get('id', None) == user[0]:
                return user[1]
        return 0

    def get_subscribers_data(self) -> list:
        data, included, meta = self.get_patrons(self.token, self.campaigns_id)
        return data

    # Step 2: Get Patrons using the Patreon API
    def get_campaigns(self, access_token):
        # Specify fields to include in the API response
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        # Make the API request
        response = requests.get(
            f'{self.PATREON_API_URL}',
            params={'fields[campaign]': 'creation_name'},
            headers=headers
        )

        campaigns_data = response.json()
        if response.status_code == 200:
            if 'data' in campaigns_data:
                for campaign in campaigns_data['data']:
                    if campaign['attributes']['creation_name'] == self.NAME:
                        return campaign['id']
        print(f"Error fetching campaigns: {response.status_code}")
        return None

    # Step 2: Get Patrons using the Patreon API
    def get_patrons(self, access_token, campaign_id) -> (list, list, dict):
        # Specify fields to include in the API response
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        patrons = []  # List to hold all patrons
        included = []  # List to hold included data
        meta = {}  # Dictionary to hold meta information
        next_cursor = None

        while True:
            # Make the API request
            response = requests.get(
                f'{self.PATREON_API_URL}/{campaign_id}/members',
                params={
                    'include': 'currently_entitled_tiers,user',
                    'fields[member]': 'currently_entitled_amount_cents',
                    'page[cursor]': next_cursor
                },
                headers=headers
            )

            data = response.json()

            patrons.extend(data.get('data', []))
            included.extend(data.get('included', []))
            meta = data.get('meta', {})

            next_cursor = meta.get('pagination', {}).get('cursors', {}).get('next')
            if next_cursor is None:
                break

        return patrons, included, meta

    def get_authenticated_token(self) -> str:
        return request.cookies.get('patreon_access_token', None)

    @property
    def blueprint_name(self) -> str:
        return 'patreon_authentication'

    @property
    def path(self) -> str:
        return 'patreon'

    def login(self):
        return redirect(f"{self.AUTHENTICATION_URL}?response_type=code&client_id={self.CLIENT_ID}&redirect_uri={self.PATREON_REDIRECT_URI}")

    def logout(self):
        session.pop('patreon_token', None)
        session.pop('patron_profile', None)
        return redirect(request.referrer)

    def callback(self):
        code = request.args.get('code')
        if code:
            # Exchange the authorization code for an access token
            token_response = requests.post(self.TOKEN_URL, data={
                'client_id': self.CLIENT_ID,
                'client_secret': self.CLIENT_SECRET,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': self.PATREON_REDIRECT_URI
            })
            token_data = token_response.json()
            token = token_data.get('access_token')
            response = make_response(redirect(url_for(f'{self.blueprint_name}.profile')))
            response.set_cookie('patreon_access_token', token, httponly=True, secure=True)
            return response

        return 'Failed to retrieve authorization code'

    @IAuthenticationRoute.Authenticated()
    def profile(self, authenticated_token, redirect_=None, is_redirect=True):
        if not redirect_:
            redirect_ = url_for('authentication.profile')

        user_response = requests.get('https://www.patreon.com/api/oauth2/v2/identity?fields[user]=full_name,thumb_url', headers={
            'Authorization': f'Bearer {authenticated_token}'
        })
        data = user_response.json()
        if is_redirect:
            return redirect(f'{redirect_}?patreon={data}')
        else:
            return data
