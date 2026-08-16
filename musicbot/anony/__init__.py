# musicbot/anony/__init__.py
import time
import asyncio
import logging
from logging.handlers import RotatingFileHandler

# Ensure logging & LOGGER exist immediately so imports cannot fail
logging.basicConfig(
    format="[%(asctime)s - %(levelname)s] - %(name)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
    handlers=[
        RotatingFileHandler("log.txt", maxBytes=10485760, backupCount=5),
        logging.StreamHandler(),
    ],
    level=logging.INFO,
)

# Module-level logger
logger = logging.getLogger(__name__)

# Backwards-compatible LOGGER factory so `from anony import LOGGER` works
def LOGGER(name: str):
    return logger.getChild(name)

# Quiet noisy libraries
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("ntgcalls").setLevel(logging.CRITICAL)
logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)

__version__ = "3.0.3"

# Import config object but DO NOT call config.check() here (main will call it).
from config import Config
config = Config()

tasks = []
boot = time.time()

import player_style as _ps
_ps.set_default(config.PLAYER_STYLE)

from anony.core.bot import Bot
app = Bot()

from anony.core.dir import ensure_dirs
ensure_dirs()

from anony.core.userbot import Userbot
userbot = Userbot()

from anony.core.mongo import MongoDB
db = MongoDB()

from anony.core.lang import Language
lang = Language()

from anony.core.telegram import Telegram
from anony.core.youtube import YouTube
tg = Telegram()
yt = YouTube()

from anony.helpers import Queue, Thumbnail
queue = Queue()
thumb = Thumbnail()

from anony.core.calls import TgCall
anon = TgCall()


async def stop() -> None:
    logger.info("Stopping...")
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.exceptions.CancelledError:
            pass

    await app.exit()
    await userbot.exit()
    await db.close()
    await thumb.close()

    logger.info("Stopped.\n")
