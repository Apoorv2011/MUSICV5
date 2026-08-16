# musicbot/anony/__main__.py
import asyncio
import importlib
import os
import pathlib
import urllib.request
import socket

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from anony import LOGGER, app, userbot
from anony.core.call import Anony
from anony.misc import sudo
from anony.plugins import ALL_MODULES
from anony.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS

ROOT_DIR = pathlib.Path(__file__).resolve().parent


def _has_sessions() -> bool:
    """
    Backwards-compatible check used by older main: keep the original STRING* checks
    while also accepting SESSION1/SESSION2/SESSION3 or TELEGRAM_SESSION/SESSION.
    """
    keys = [
        "STRING1",
        "STRING2",
        "STRING3",
        "STRING4",
        "STRING5",
        "SESSION1",
        "SESSION2",
        "SESSION3",
        "TELEGRAM_SESSION",
        "SESSION",
    ]
    for k in keys:
        if getattr(config, k, None):
            return True
    return False


def _download_cookies(urls, out_path: pathlib.Path) -> bool:
    """
    Download items from the provided URLs and append them into out_path.
    Returns True if any content was written.
    """
    if not urls:
        return False

    out_path.parent.mkdir(parents=True, exist_ok=True)
    wrote = False
    for url in urls:
        try:
            # small timeout so deploy doesn't hang forever
            with urllib.request.urlopen(url, timeout=10) as r:
                content = r.read()
                if content:
                    with open(out_path, "ab") as f:
                        f.write(content)
                        f.write(b"\n")
                    LOGGER("anony.startup").info("Saved cookies from %s", url)
                    wrote = True
        except (urllib.error.URLError, socket.timeout, Exception) as e:
            LOGGER("anony.startup").warning("Failed to download cookies from %s: %s", url, e)
    return wrote


async def init():
    # Keep the original behavior: config.check() already ran in anony.__init__.
    # Check sessions like the original code did.
    if not _has_sessions():
        LOGGER(__name__).error("Assistant client variables not defined, exiting...")
        exit()

    # If config exposes COOKIES_URL (a list), try to download them into a local file
    try:
        cookie_urls = getattr(config, "COOKIES_URL", []) or []
    except Exception:
        cookie_urls = []

    if cookie_urls:
        cookies_file = ROOT_DIR / "cookies" / "cookies.txt"
        if _download_cookies(cookie_urls, cookies_file):
            # Expose to the process as YTDLP_COOKIES for yt-dlp callers to use
            os.environ["YTDLP_COOKIES"] = str(cookies_file)
            LOGGER("anony.startup").info("YTDLP_COOKIES set to %s", cookies_file)
        else:
            LOGGER("anony.startup").warning("COOKIES_URL provided but no cookies were downloaded")

    await sudo()

    try:
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except Exception:
        pass

    await app.start()

    for module in ALL_MODULES:
        importlib.import_module("anony.plugins." + module)

    LOGGER("anony.plugins").info("Successfully loaded Modules...")
    await userbot.start()
    await Anony.start()

    try:
        await Anony.stream_call("https://batbin.me/raw/coelect")
    except NoActiveGroupCall:
        LOGGER("anony").error(
            "Please turn on the video chat of your log group/channel. Stopping Bot..."
        )
        exit()
    except Exception:
        pass

    await Anony.decor()
    LOGGER("anony").info(
        "AnonX Music Bot Started Successfully."
    )
    await idle()
    await app.stop()
    await userbot.stop()
    LOGGER("anony").info("Stopping AnonX Music Bot...")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
