import asyncio
import functools
from collections.abc import Callable
from typing import Any

import aiohttp
import validators
import yt_dlp


class YouTubeDownloader:
    """Uses the Downloader protocol and downloads songs from YouTube."""

    def __init__(self):
        # store information about the song
        self._songInfo: dict[str, Any] | None = None

        # setup options for YouTube downloader
        self._YDL_OPTIONS = {
            "format": "bestaudio",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": "song.%(ext)s",
        }

    @staticmethod
    def getSource() -> str:
        """Get the source of this song download, i.e. the platform.

        Returns:
            str: the name of the song source
        """
        return "YouTube"

    @staticmethod
    def _to_thread(func: Callable) -> Any:
        """Helper method to run synchronous code asynchronously in a separate thread.

        Args:
            func (Callable): a synchronous function to run asynchronously

        Returns:
            Any: the return result of func
        """

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await asyncio.to_thread(func, *args, **kwargs)

        return wrapper

    async def _getURLFromURLorSearch(self, url_or_search: str) -> str | None:
        """Get the URL for a YouTube URL or search.

        If a URL is provided, the URL is validated to confirm it leads to a YouTube
        video.

        If a search query is provided, a URL to the first search result is returned. If
        no search results are found, then None is returned.

        Args:
            url_or_search (str): either a YouTube url or a search query

        Returns:
            str | None: A valid YouTube video URL, or None if no video is found
        """
        with yt_dlp.YoutubeDL(self._YDL_OPTIONS) as ydl:
            # check if string is a valid url, that it contains the youtube.com domain,
            # and that the URL leads to a valid YouTube video
            if (
                validators.url(url_or_search)
                and "youtube.com" in url_or_search.lower()
                and await self._validYouTubeVideo(url_or_search)
            ):
                return url_or_search
            else:
                # url_or_search is a search query
                search_results = ydl.sanitize_info(
                    ydl.extract_info(f"ytsearch:{url_or_search}", download=False)
                )["entries"]
                # if search query returned results
                if search_results:
                    video: dict[str, Any] | None = search_results[0]
                    # if we found a matching video, then return the video url
                    if video:
                        return video["webpage_url"]
        # if the URL was not valid or the search query did not return any results,
        # then return None
        return None

    async def _validYouTubeVideo(self, url: str) -> bool:
        """Checks whether a YouTube URL leads to a valid YouTube video.

        Assumes that url is a valid url to the YouTube website.

        Args:
            url (str): A valid url to YouTube.com

        Returns:
            bool: whether or not the url leads to a valid YouTube video.
        """
        # start an aiohttp client session
        async with aiohttp.ClientSession() as session:
            # send a get request to the url
            async with session.get(url) as resp:
                # check if response is OK
                if resp.status == 200:
                    # read the response stream
                    content = await resp.text()
                    return "Video unavailable" not in content
        return False

    async def _getVideoInformation(self, url: str) -> None:
        """Fetch information about a song using the song URL.

        Assumes the given URL is valid.

        Args:
            url (str): A valid YouTube video URL
        """
        with yt_dlp.YoutubeDL(self._YDL_OPTIONS) as ydl:
            self._songInfo = ydl.sanitize_info(ydl.extract_info(url, download=False))

    async def validateAndStoreURLOrSearch(self, url_or_search: str) -> bool:
        """Validates a URL or search query to make sure it leads to a YouTube video.

        If the URL or search query is valid, information about the song is stored as
        well.

        Args:
            url_or_search (str): either a YouTube URL or search query

        Returns:
            bool: whether or not the URL or search query is valid
        """
        url = await self._getURLFromURLorSearch(url_or_search)
        if url:
            await self._getVideoInformation(url)
            return True
        return False

    @_to_thread
    def _downloadFromYouTube(self, url) -> str:
        """Downloads the song from YouTube using the given URL.

        Returns:
            str: the filename of the downloaded song
        """
        with yt_dlp.YoutubeDL(self._YDL_OPTIONS) as ydl:
            ydl.download(url)
            return "song.mp3"

    async def downloadSong(self) -> str | None:
        """Downloads the song from YouTube using the information stored in this object.

        If no information has already been stored, then None is returned.

        Returns:
            str | None: the filename of the downloaded song, or None if no song
            information is stored.
        """
        url = self.getSongURL()
        if url:
            filename = await self._downloadFromYouTube(url)
            return filename
        return None

    def getSongName(self) -> str | None:
        """Get the name of the song from the information stored in the object.

        If no information has already been stored, then None is returned.

        Returns:
            str | None: the song name, or None if no song information is stored.
        """
        return self._songInfo["title"] if self._songInfo else None

    def getSongURL(self) -> str | None:
        """Get the URL of the song from the information stored in the object.

        If no information has already been stored, then None is returned.

        Returns:
            str | None: the song URL, or None if no song information is stored.
        """
        return self._songInfo["webpage_url"] if self._songInfo else None
