from abc import ABC, abstractmethod


class IDonationService(ABC):
    @abstractmethod
    def get_subscribers(self) -> list[tuple]:
        """
        :return: list of emails
        """
        pass

    @abstractmethod
    def get_user_cents(self) -> int:
        """
        :return: get user cents currently
        """
        pass

    @abstractmethod
    def get_subscribers_data(self) -> list:
        pass
