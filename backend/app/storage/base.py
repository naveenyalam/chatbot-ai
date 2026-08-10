import abc

class BaseStorage(abc.ABC):
    @abc.abstractmethod
    def save_file(self, file_content: bytes, filename: str) -> str:
        """
        Saves file content and returns the absolute storage path/URI.
        """
        pass

    @abc.abstractmethod
    def delete_file(self, storage_path: str) -> None:
        """
        Deletes the file from storage.
        """
        pass
