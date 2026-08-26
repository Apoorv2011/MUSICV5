import asyncio
import re
import aiofiles
import aiohttp


def extract_video_id(url_or_id: str) -> str:
    """Extracts 11-character YouTube video ID from raw input or full URLs."""
    if not url_or_id:
        return ""
    regex = r"(?:v=|\/([0-9A-Za-z_-]{11}).*|youtu\.be\/([0-9A-Za-z_-]{11}))"
    match = re.search(regex, str(url_or_id))
    if match:
        return match.group(1) or match.group(2)
    return str(url_or_id).strip()


class NexGenApi:
    def __init__(
        self,
        api_url: str,
        api_key: str,
        video_api_url: str,
        retries: int = 10,
        timeout: int = 40,
    ):
        self.api_url = api_url
        self.video_api_url = video_api_url
        self.api_key = api_key
        self.chunk_limit = 128 * 1024
        self.dl_cache = {}
        self.v_cache = {}
        self.retries = retries
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: aiohttp.ClientSession | None = None
        self.headers = {"Accept": "application/json"}

    async def get_session(self) -> None:
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)

    async def save_file(self, vid_id: str, url: str, video: bool = False) -> str | None:
        try:
            await self.get_session()
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return None

                file_name = None
                cd = resp.headers.get("Content-Disposition")
                if cd:
                    match = re.search(r'filename="?(.+?)"?$', cd)
                    if match:
                        file_name = match.group(1)
                if not file_name:
                    file_name = vid_id + (".mp4" if video else ".mp3")

                fname = f"downloads/{file_name}"
                async with aiofiles.open(fname, "wb") as f:
                    async for chunk in resp.content.iter_chunked(self.chunk_limit):
                        if chunk:
                            await f.write(chunk)

                if video:
                    self.v_cache[vid_id] = fname
                else:
                    self.dl_cache[vid_id] = fname

                return fname
        except Exception:
            pass
        return None

    async def download(self, vid_id: str, video: bool = False) -> str | None:
        vid_id = extract_video_id(vid_id)
        if video and vid_id in self.v_cache:
            return self.v_cache[vid_id]
        elif not video and vid_id in self.dl_cache:
            return self.dl_cache[vid_id]

        await self.get_session()
        endp = f"{self.api_url}/song/{vid_id}?api={self.api_key}"
        if video:
            endp = f"{self.video_api_url}/video/{vid_id}?api={self.api_key}"

        for _ in range(self.retries):
            try:
                async with self.session.get(endp, headers=self.headers) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()

                    status = data.get("status")
                    dl_link = data.get("link")
                    if not status:
                        return None

                    if status == "done":
                        if not dl_link:
                            return None
                        # Downloads full CDN file locally
                        return await self.save_file(vid_id, dl_link, video)
                    elif status == "downloading":
                        await asyncio.sleep(4)
                        continue
                    else:
                        break
            except Exception:
                break
        return None


class ShrutiApi:
    def __init__(self, api_url: str, api_key: str, retries: int = 10, timeout: int = 40):
        self.api_url = api_url
        self.api_key = api_key
        self.chunk_limit = 128 * 1024
        self.dl_cache = {}
        self.v_cache = {}
        self.retries = retries
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: aiohttp.ClientSession | None = None
        self.headers = {"Accept": "application/json"}

    async def get_session(self) -> None:
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)

    async def save_file(self, vid_id: str, url: str, video: bool = False) -> str | None:
        try:
            await self.get_session()
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return None

                file_name = None
                cd = resp.headers.get("Content-Disposition")
                if cd:
                    match = re.search(r'filename="?(.+?)"?$', cd)
                    if match:
                        file_name = match.group(1)
                if not file_name:
                    file_name = vid_id + (".mp4" if video else ".m4a")

                fname = f"downloads/{file_name}"
                async with aiofiles.open(fname, "wb") as f:
                    async for chunk in resp.content.iter_chunked(self.chunk_limit):
                        if chunk:
                            await f.write(chunk)

                if video:
                    self.v_cache[vid_id] = fname
                else:
                    self.dl_cache[vid_id] = fname

                return fname
        except Exception:
            pass
        return None

    async def download(self, vid_id: str, video: bool = False) -> str | None:
        vid_id = extract_video_id(vid_id)
        if video and vid_id in self.v_cache:
            return self.v_cache[vid_id]
        elif not video and vid_id in self.dl_cache:
            return self.dl_cache[vid_id]

        await self.get_session()
        media_type = "video" if video else "audio"
        endp = f"{self.api_url}/download?url={vid_id}&type={media_type}&api_key={self.api_key}"

        for _ in range(self.retries):
            try:
                async with self.session.get(endp, headers=self.headers) as resp:
                    if resp.status != 200:
                        await asyncio.sleep(2)
                        continue

                    try:
                        data = await resp.json()
                        status = data.get("status")
                        if status == "success":
                            # Downloads CDN file locally
                            return await self.save_file(vid_id, endp, video)
                    except Exception:
                        return await self.save_file(vid_id, endp, video)

            except Exception:
                await asyncio.sleep(2)
                continue

        return None
