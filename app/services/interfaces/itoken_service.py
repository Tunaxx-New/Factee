from abc import ABC, abstractmethod


class TokenService(ABC):

    @abstractmethod
    def __init__(self, secret: str):
        pass

    @abstractmethod
    def create_invitation_token(self, company_name: str, user_id: str, expiration_minutes: int = 30):
        """
        @:return
        """
        pass

    @abstractmethod
    def decode_token(self, token: str) -> (str, str):
        """
        @:return decoded payload
        """
        pass

