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
from backend_prefs import get_primary

JIOSAVAN_API_URL = os.getenv("JIOSAVAN_API_URL", "").rstrip("/")
ARC_API_URL = os.getenv("ARC_API_URL", "https://api.arcmusic.fun").rstrip("/")
ARC_API_KEY = os.getenv("ARC_API_KEY", "")


# ── JioSaavn sidecar ──────────────────────────────────────────────────────────

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


# ── ArcAPI (job-based async) ──────────────────────────────────────────────────

async def _arc_start_job(
    query: str, is_video: bool = False
) -> tuple[str | None, str | None]:
    """Start an ArcAPI download and return (job_id, direct_url)."""
    if not ARC_API_URL or not ARC_API_KEY:
        return None, None
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(
                f"{ARC_API_URL}/youtube/v2/download",
                params={
                    "query": query,
                    "isVideo": "true" if is_video else "false",
                    "api_key": ARC_API_KEY,
                },
                timeout=aiohttp.ClientTimeout(total=15),
            ) as r:
                if r.status != 200:
                    logger.warning("ArcAPI start job HTTP %s for %s", r.status, query)
                    return None, None
                data = await r.json()
                result = data.get("result") or {}
                direct_url = (
                    result.get("public_url")
                    or result.get("cdn")
                    or result.get("url")
                )
                if direct_url:
                    return None, direct_url
                return data.get("job_id"), None
    except Exception as e:
        logger.warning("ArcAPI start job error: %s", e)
        return None, None


async def _arc_poll_job(job_id: str, timeout: int = 60) -> str | None:
    """Poll /youtube/jobStatus until done → returns full download URL."""
    if not ARC_API_URL or not ARC_API_KEY:
        return None
    deadline = asyncio.get_event_loop().time() + timeout
    async with aiohttp.ClientSession() as s:
        while asyncio.get_event_loop().time() < deadline:
            try:
                async with s.get(
                    f"{ARC_API_URL}/youtube/jobStatus",
                    params={"job_id": job_id},
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as r:
                    if r.status != 200:
                        await asyncio.sleep(2)
                        continue
                    data = await r.json()
                    job = data.get("job", {})
                    status = job.get("status") or data.get("status")
                    if status == "done":
                        result = job.get("result", {})
                        public_url = (
                            result.get("public_url")
                            or result.get("cdn")
                            or result.get("url")
                        )
                        if public_url:
                            # public_url is a relative path like /media/ID.mp3
                            if public_url.startswith(("http://", "https://")):
                                return public_url
                            return f"{ARC_API_URL}{public_url}"
                        return None
                    if status in ("failed", "error"):
                        logger.warning("ArcAPI job %s failed: %s", job_id, data)
                        return None
            except Exception as e:
                logger.warning("ArcAPI poll error: %s", e)
            await asyncio.sleep(3)
    logger.warning("ArcAPI job %s timed out after %ss", job_id, timeout)
    return None


async def _arc_download(query: str, is_video: bool = False) -> str | None:
    """Full Arc flow: return a direct URL or start and poll a job."""
    job_id, direct_url = await _arc_start_job(query, is_video)
    if direct_url:
        return direct_url
    if not job_id:
        return None
    return await _arc_poll_job(job_id)


# ── YouTube metadata search (no download) ─────────────────────────────────────

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


# ── helpers ───────────────────────────────────────────────────────────────────

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
                with open(filepath, "wb") as f:
                    async for chunk in r.content.iter_chunked(65536):
                        f.write(chunk)
        return filepath
    except Exception as e:
        logger.warning("File write error: %s", e)
        return None


# ── YouTube class (public API) ────────────────────────────────────────────────

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
            # ArcAPI uses YouTube IDs — search YouTube for metadata/ID, download via Arc
            return await _yt_search_meta(query, m_id, video)

        # auto: JioSaavn → YouTube metadata (Arc used at download time)
        saavn = await _jiosaavn_search(query)
        if saavn:
            return _make_track_from_saavn(saavn, query, m_id)
        return await _yt_search_meta(query, m_id, video)

    async def search_youtube(
        self, query: str, m_id: int, video: bool = False
    ) -> Track | None:
        """Search YouTube metadata directly, bypassing the music backend."""
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
            stream_url = await _arc_download(
                f"https://www.youtube.com/watch?v={video_id}",
                is_video=video,
            )
            if stream_url:
                result = await _download_to_file(stream_url, filename)
                if result:
                    logger.info("Downloaded via ArcAPI [arc]: %s", filename)
                    _schedule_delete(result)
                    return result
            logger.warning("ArcAPI download failed [arc] for: %s", video_id)
            return None

        # auto: JioSaavn first → ArcAPI fallback
        url = await _jiosaavn_download(video_id)
        if url:
            result = await _download_to_file(url, filename)
            if result:
                logger.info("Downloaded via JioSaavn [auto]: %s", filename)
                _schedule_delete(result)
                return result

        stream_url = await _arc_download(
            f"https://www.youtube.com/watch?v={video_id}",
            is_video=video,
        )
        if stream_url:
            result = await _download_to_file(stream_url, filename)
            if result:
                logger.info("Downloaded via ArcAPI [auto fallback]: %s", filename)
                _schedule_delete(result)
                return result

        logger.warning("All sources failed [auto] for: %s", video_id)
        return None
 