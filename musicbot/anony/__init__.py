import time
import asyncio
import logging
from logging.handlers import RotatingFileHandler

# --- Minimal logging + compatibility export FIRST so imports cannot fail ---
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

# Quiet noisy libraries (still safe to set now)
logging.getLogger("httpx").setLevel(logging.ERROR)
logging.getLogger("ntgcalls").setLevel(logging.CRITICAL)
logging.getLogger("pymongo").setLevel(logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pytgcalls").setLevel(logging.ERROR)

__version__ = "3.0.3"

# Import Config object (you can choose to call config.check() here or in main)
from config import Config

config = Config()
# Keep current behavior and validate immediately:
# config.check()  # <-- optional: if you'd like check to run here, uncomment

# The rest of the module (instantiate app components).
# IMPORTANT: avoid running functions that may raise before LOGGER is defined.
# The following instantiations are standard in your project:
import player_style as _ps
_ps.set_default(config.PLAYER_STYLE)

from anony.core.bot import Bot
app = Bot()

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
    # tasks variable may be defined elsewhere; guard against missing name
    try:
        tasks
    except NameError:
        return

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
