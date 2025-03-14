from abc import ABC, abstractmethod


class DatabaseService(ABC):

    @abstractmethod
    def __init__(self, database_name, host):
        pass

    @abstractmethod
    def create_fact(self,
                    title: str,
                    context: str,
                    page: int,
                    quote: str,
                    source_id: str,
                    user_id: str) -> dict:
        """
        @:return created fact
        Fact composite of title and context text, brings with source and page, belongs to user
        """
        pass

    @abstractmethod
    def create_source(self,
                      title: str,
                      author: str,
                      year: int,
                      _type_id: str,
                      link: str) -> dict:
        """
        @:return created source
        Source is a fact linking material. API referencing.
        """
        pass

    @abstractmethod
    def react(self,
              _id: str,
              _collection: str,
              _label: str,
              user_id: str) -> tuple[dict[str, str], int]:
        """
        @:return some reaction to article or fact
        Source is a fact linking material. API referencing.
        """
        pass

    @abstractmethod
    def get_documents(self, collection: str, query: dict) -> list[dict]:
        """
        @:return documents
        """
        pass

    @abstractmethod
    def get_documents_pipeline(self, collection: str, pipeline: list) -> list[dict]:
        """
        @:return documents
        """
        pass

    @abstractmethod
    def get_document(self, collection: str, query: dict) -> dict:
        """
        @:return document
        """
        pass

    @abstractmethod
    def count_documents(self, collection: str, query: dict) -> int:
        """
        @:return count of query docuemnts
        """
        pass

    @abstractmethod
    def get_user_summary(self, user_id: str):
        """
        @:return aggregation for user
        """
        pass
