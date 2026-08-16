import asyncio
import importlib

from pyrogram import idle
from pytgcalls.exceptions import NoActiveGroupCall

import config
from anony import LOGGER, app, userbot
from anony.core.call import Anony
from anony.misc import sudo
from anony.plugins import ALL_MODULES
from anony.utils.database import get_banned_users, get_gbanned
from config import BANNED_USERS


async def init():
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
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
