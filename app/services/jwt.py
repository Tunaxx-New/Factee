import jwt
import datetime

from app.services.interfaces.itoken_service import TokenService


class Jwt(TokenService):
    def __init__(self, secret: str):
        self.SECRET = secret

    def create_invitation_token(self, company_name: str, user_id: str, expiration_minutes: int = 30):
        # Define the payload
        payload = {
            'company_name': company_name,
            'user_sub': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=expiration_minutes)
        }

        # Create the token using the secret key from your Flask app config
        token = jwt.encode(payload, self.SECRET, algorithm='HS256')

        return token

    def decode_token(self, token: str) -> (str, str):
        payload = jwt.decode(token, self.SECRET, algorithms=['HS256'])
        return payload.get('company_name'), payload.get('user_sub')
