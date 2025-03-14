from abc import ABC, abstractmethod
from functools import wraps

from flask import Blueprint, session


class IAuthenticationRoute(ABC):
    def __init__(self):
        self._blueprint = Blueprint(self.blueprint_name, __name__)
        self.register_routes()

    @property
    @abstractmethod
    def blueprint_name(self) -> str:
        """
        Abstract property to define a unique name for the Blueprint.
        """
        pass

    @property
    @abstractmethod
    def path(self) -> str:
        """
        Abstract property to define the unique path.
        """
        pass

    @property
    def blueprint(self) -> Blueprint:
        return self._blueprint

    def register_routes(self):
        """
        Registers required routes by setting them to the abstract methods.
        """
        self._blueprint.add_url_rule(f'/{self.path}/login', 'login', self.login, methods=['GET'])
        self._blueprint.add_url_rule(f'/{self.path}/logout', 'logout', self.logout, methods=['GET'])
        self._blueprint.add_url_rule(f'/{self.path}/callback', 'callback', self.callback, methods=['GET'])
        self._blueprint.add_url_rule(f'/{self.path}/profile', 'profile', self.profile, methods=['GET'])

    @abstractmethod
    def login(self):
        """
        Abstract login method to be implemented by subclasses.
        """
        pass

    @abstractmethod
    def logout(self):
        """
        Abstract logout method to be implemented by subclasses.
        """
        pass

    @abstractmethod
    def callback(self):
        """
        Abstract callback method to be implemented by subclasses.
        """
        pass

    @abstractmethod
    def get_authenticated_token(self) -> str:
        """
        Abstract get authentication from session or response to wrap to authenticated route
        @:return authenticated id
        """
        pass

    @staticmethod
    def Authenticated():
        def decorator(func):
            @wraps(func)
            def wrapper(self, *args, **kwargs):
                return func(self, *args, **kwargs, authenticated_token=self.get_authenticated_token())
            return wrapper
        return decorator

    @abstractmethod
    def profile(self, authenticated_token, is_redirect=True):
        """
        Abstract profile method to be implemented by subclasses.
        """
        pass
