from abc import ABC, abstractmethod


class AuthenticationService(ABC):

    @abstractmethod
    def login(self, email: str, password: str) -> (str, str, int):
        """
        @:return (access token, response string)
        """
        pass

    @abstractmethod
    def logout(self, refresh_token: str):
        """
        @:return logout session
        """
        pass

    @abstractmethod
    def callback(self, redirect_uri: str, code: str, session_state: str) -> (str, str):
        """
        Callback from login
        @:return token
        """
        pass

    @abstractmethod
    def profile(self, token: str) -> (dict, str, int):
        """
        @:return profile document
        """
        pass

    @abstractmethod
    def get_public_info(self, sub: str) -> (dict, str, int):
        """
        @:return public info of user
        """
        pass

    @abstractmethod
    def get_public_info_by_username(self, username: str) -> (dict, str, int):
        """
        @:return public info of user
        """
        pass

    @abstractmethod
    def get_roles(self, token: str) -> dict:
        """
        @:return roles of user
        """
        pass

    @abstractmethod
    def redirect_login(self) -> str:
        """
        @:return redirect url for login
        """
        pass

    @abstractmethod
    def redirect_register(self) -> str:
        """
        @:return redirect url for register
        """
        pass

    @abstractmethod
    def redirect_profile_manage(self) -> str:
        """
        @:return redirect url for account console
        """
        pass
