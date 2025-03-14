from abc import ABC, abstractmethod


class ImageService(ABC):
    @abstractmethod
    def get_avatar(self, username: str):
        """
        @:return Avatar
        """
        pass

    @abstractmethod
    def get_default(self):
        """
        @:return default image
        """
        pass
