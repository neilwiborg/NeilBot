from abc import abstractmethod
from typing import Protocol, runtime_checkable


@runtime_checkable
class Downloader(Protocol):
    """Defines a protocol for downloading music from any source."""

    @staticmethod
    @abstractmethod
    def getSource() -> str:
        """Get the source of this song download, i.e. the platform.

        Returns:
            str: the name of the song source
        """
        ...

    @abstractmethod
    async def validateAndStoreURLOrSearch(self, url_or_search: str) -> bool:
        """Validates a URL or search query to make sure it leads to a valid song.

        If the URL or search query is valid, information about the song is stored as
        well.

        Args:
            url_or_search (str): either a URL or a search query

        Returns:
            bool: whether or not the URL or search query is valid
        """
        ...

    @abstractmethod
    async def downloadSong(self) -> str | None:
        """Downloads the song from the information stored in the object.

        If no information has already been stored, then None is returned.

        Returns:
            str | None: the filename of the downloaded song
        """
        ...

    @abstractmethod
    def getSongName(self) -> str | None:
        """Get the name of the song from the information stored in the object.

        If no information has already been stored, then None is returned.

        Returns:
            str | None: the song name, or None if no song information is stored.
        """
        ...

    @abstractmethod
    def getSongURL(self) -> str | None:
        """Get the URL of the song from the information stored in the object.

        If no information has already been stored, then None is returned.

        Returns:
            str | None: the song URL, or None if no song information is stored.
        """
        ...
