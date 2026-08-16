import asyncio
import importlib

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
# Try to import a pre-existing LOGGER factory (some repo variants export LOGGER).
# Otherwise import the module-level logger and create a small LOGGER factory locally.
try:
    from anony import LOGGER, app, userbot  # type: ignore
except Exception:
    from anony import logger, app, userbot  # type: ignore

    def LOGGER(name: str):
        return logger.getChild(name)

from anony.core.call import Anony
from anony.misc import sudo
from anony.plugins import ALL_MODULES
from anony.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS


def _has_sessions() -> bool:
    """
    Check for any session/assistant environment names used by different repo versions.
    This keeps the check backwards-compatible.
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


async def init():
    if not _has_sessions():
        LOGGER(__name__).error("Assistant client variables not defined, exiting...")
        exit()

    await sudo()

    try:
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except Exception:
        # ignore DB errors during boot so we can still surface better startup errors later
        pass

    await app.start()

    # import all plugins (keeps the same behavior as older main)
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
        # ignore and continue if streaming fails
        pass

    await Anony.decor()
    LOGGER("anony").info("AnonX Music Bot Started Successfully.")
    await idle()
    await app.stop()
    await userbot.stop()
    LOGGER("anony").info("Stopping AnonX Music Bot...")


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())
