import os
import re
import asyncio
import aiohttp
import threading
from time import sleep
from pathlib import Path

from py_yt import Playlist, VideosSearch

from anony import logger
from anony.helpers import Track, utils
from anony.helpers._api import NexGenApi
from backend_prefs import get_primary

JIOSAVAN_API_URL = os.getenv("JIOSAVAN_API_URL", "").rstrip("/")
# NexGenBots config (used instead of Arc)
NEXGEN_API_URL = os.getenv("API_URL", "https://pvtz.nexgenbots.xyz").rstrip("/")
NEXGEN_VIDEO_API_URL = os.getenv("VIDEO_API_URL", "https://api.video.nexgenbots.xyz").rstrip("/")
NEXGEN_API_KEY = os.getenv("API_KEY", "")


# ----------------- JioSaavn sidecar ------------------------------------------------

async def _jiosaavn_search(query: str) -> dict | None:
    if not JIOSAVAN_API_URL:
        return None
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{JIOSAVAN_API_URL}/search",
                params={"q": query},
                timeout=aiohttp.ClientTimeout(total=8),
            ) as r:
                if r.status != 200:
                    logger.warning("JioSaavn search HTTP %s", r.status)
                    return None
                data = await r.json()
                tracks = data.get("tracks") or []
                return tracks[0] if tracks else None
    except Exception as e:
        logger.warning("JioSaavn search error: %s", e)
        return None


async def _jiosaavn_download(song_id: str) -> str | None:
    if not JIOSAVAN_API_URL:
        return None
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{JIOSAVAN_API_URL}/download",
                params={"id": song_id},
                timeout=aiohttp.ClientTimeout(total=8),
            ) as r:
                if r.status != 200:
                    logger.warning("JioSaavn download HTTP %s id=%s", r.status, song_id)
                    return None
                data = await r.json()
                return data.get("url") or None
    except Exception as e:
        logger.warning("JioSaavn download error: %s", e)
        return None


# ----------------- NexGenBots integration (replaces Arc flow) ----------------------

# Shared NexGenApi client (lazy-init)
_nexgen_client: NexGenApi | None = None


async def _get_nexgen_client() -> NexGenApi | None:
    global _nexgen_client
    if _nexgen_client:
        return _nexgen_client
    if not NEXGEN_API_URL or not NEXGEN_API_KEY:
        logger.warning("NexGen config missing: API_URL or API_KEY not set")
        return None
    _nexgen_client = NexGenApi(
        api_url=NEXGEN_API_URL,
        api_key=NEXGEN_API_KEY,
        video_api_url=NEXGEN_VIDEO_API_URL,
    )
    try:
        await _nexgen_client.get_session()
    except Exception as e:
        logger.warning("Failed to create NexGen session: %s", e)
        _nexgen_client = None
    return _nexgen_client


async def _nexgen_download(video_id: str, is_video: bool = False) -> str | None:
    """
    Use NexGenApi to download the media file.
    Returns local filepath (e.g., downloads/{id}.mp4) or None on failure.
    """
    client = await _get_nexgen_client()
    if not client:
        return None
    try:
        # NexGenApi.download will poll the provider and save file to downloads/
        result = await client.download(video_id, video=is_video)
        return result
    except Exception as e:
        logger.warning("NexGen download error for %s: %s", video_id, e)
        return None


# ----------------- YouTube metadata search (no download) --------------------------

async def _yt_search_meta(query: str, m_id: int, video: bool) -> Track | None:
    try:
        _search = VideosSearch(query, limit=1, with_live=False)
        results = await _search.next()
    except Exception:
        return None
    if results and results.get("result"):
        data = results["result"][0]
        return Track(
            id=data.get("id"),
            channel_name=data.get("channel", {}).get("name"),
            duration=data.get("duration"),
            duration_sec=utils.to_seconds(data.get("duration")),
            message_id=m_id,
            title=data.get("title")[:25],
            thumbnail=data.get("thumbnails", [{}])[-1].get("url", "").split("?")[0],
            url=data.get("link"),
            view_count=data.get("viewCount", {}).get("short"),
            video=video,
        )
    return None


# ----------------- helpers --------------------------------------------------------

def _make_track_from_saavn(saavn: dict, query: str, m_id: int) -> Track:
    dur_sec = saavn.get("duration") or 0
    try:
        dur_sec = int(dur_sec)
    except (ValueError, TypeError):
        dur_sec = 0
    m, s = divmod(dur_sec, 60)
    return Track(
        id=saavn.get("id", ""),
        channel_name=saavn.get("artists", ""),
        duration=f"{m}:{s:02d}",
        duration_sec=dur_sec,
        message_id=m_id,
        title=(saavn.get("title") or query)[:25],
        thumbnail=saavn.get("thumbnail", ""),
        url=saavn.get("url", ""),
        view_count="",
        video=False,
    )


def _schedule_delete(filepath: str, delay: int = 300) -> None:
    """Delete a downloaded file after `delay` seconds in a daemon thread."""
    def _worker():
        sleep(delay)
        try:
            os.remove(filepath)
            logger.info("Cache cleanup: removed %s", filepath)
        except Exception:
            pass
    threading.Thread(target=_worker, daemon=True).start()


async def _download_to_file(url: str, filepath: str) -> str | None:
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=aiohttp.ClientTimeout(total=90)) as r:
                if r.status != 200:
                    return None
                # Write in synchronous fashion inside async context to avoid mixing aiofiles here,
                # but this preserves original behavior. If desired, change to aiofiles.
                with open(filepath, "wb") as f:
                    async for chunk in r.content.iter_chunked(65536):
                        f.write(chunk)
        return filepath
    except Exception as e:
        logger.warning("File write error: %s", e)
        return None


# ----------------- YouTube class (public API) -----------------------------------

class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        self.iregex = re.compile(
            r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)"
            r"(?!/(watch\?v=[A-Za-z0-9_-]{11}|shorts/[A-Za-z0-9_-]{11}"
            r"|playlist\?list=PL[A-Za-z0-9_-]+|[A-Za-z0-9_-]{11}))\S*"
        )

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def invalid(self, url: str) -> bool:
        return bool(re.match(self.iregex, url))

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        mode = get_primary()

        if mode == "jio":
            saavn = await _jiosaavn_search(query)
            if saavn:
                return _make_track_from_saavn(saavn, query, m_id)
            logger.warning("JioSaavn search returned nothing for: %s", query)
            return None

        if mode == "arc":
            # Arc mode now uses NexGenBots under the hood
            return await _yt_search_meta(query, m_id, video)

        # auto: JioSaavn → YouTube metadata (NexGen used at download time)
        saavn = await _jiosaavn_search(query)
        if saavn:
            return _make_track_from_saavn(saavn, query, m_id)
        return await _yt_search_meta(query, m_id, video)

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            if not plist or "videos" not in plist:
                return tracks
            for data in plist["videos"][:limit]:
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails", [{}])[-1].get("url", "").split("?")[0],
                    url=data.get("link", "").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)
        except Exception:
            pass
        return tracks

    async def download(self, video_id: str, video: bool = False) -> str | None:
        ext = "mp4" if video else "m4a"
        filename = f"downloads/{video_id}.{ext}"
        if Path(filename).exists():
            return filename

        mode = get_primary()

        if mode == "jio":
            url = await _jiosaavn_download(video_id)
            if url:
                result = await _download_to_file(url, filename)
                if result:
                    logger.info("Downloaded via JioSaavn [jio]: %s", filename)
                    _schedule_delete(result)
                    return result
            logger.warning("JioSaavn download failed [jio] for: %s", video_id)
            return None

        if mode == "arc":
            # Use NexGenBots instead of ArcAPI
            result = await _nexgen_download(video_id, is_video=video)
            if result:
                logger.info("Downloaded via NexGenBots [arc->nexgen]: %s", result)
                _schedule_delete(result)
                return result
            logger.warning("NexGen download failed [arc->nexgen] for: %s", video_id)
            return None

        # auto: JioSaavn first → NexGen fallback
        url = await _jiosaavn_download(video_id)
        if url:
            result = await _download_to_file(url, filename)
            if result:
                logger.info("Downloaded via JioSaavn [auto]: %s", filename)
                _schedule_delete(result)
                return result

        # fallback to NexGenBots
        result = await _nexgen_download(video_id, is_video=video)
        if result:
            logger.info("Downloaded via NexGenBots [auto fallback]: %s", result)
            _schedule_delete(result)
            return result

        logger.warning("All sources failed [auto] for: %s", video_id)
        return None
