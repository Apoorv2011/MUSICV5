from os import getenv
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.API_ID = int(getenv("API_ID", 0))
        self.API_HASH = getenv("API_HASH")

        self.BOT_TOKEN = getenv("BOT_TOKEN")
        self.MONGO_URL = getenv("MONGO_URL")

        self.LOGGER_ID = int(getenv("LOGGER_ID", 0))
        self.OWNER_ID = int(getenv("OWNER_ID", 0))

        self.DURATION_LIMIT = int(getenv("DURATION_LIMIT", 60)) * 60
        self.QUEUE_LIMIT = int(getenv("QUEUE_LIMIT", 20))
        self.PLAYLIST_LIMIT = int(getenv("PLAYLIST_LIMIT", 20))

        # Automatically strips quotes, spaces, and line breaks from Railway UI multi-line values
        raw1 = getenv("SESSION1") or getenv("TELEGRAM_SESSION") or getenv("SESSION") or ""
        self.SESSION1 = "".join(raw1.replace('"', '').replace("'", "").split()) or None

        raw2 = getenv("SESSION2") or ""
        self.SESSION2 = "".join(raw2.replace('"', '').replace("'", "").split()) or None

        raw3 = getenv("SESSION3") or ""
        self.SESSION3 = "".join(raw3.replace('"', '').replace("'", "").split()) or None

        self.SUPPORT_CHANNEL = getenv(
            "SUPPORT_CHANNEL", "https://t.me/MeisouUpdates"
        )
        self.SUPPORT_CHAT = getenv(
            "SUPPORT_CHAT", "https://t.me/+4bmTAqbosiY2NWE1"
        )

        self.AUTO_LEAVE: bool = getenv("AUTO_LEAVE", "False").lower() == "true"
        self.AUTO_END: bool = getenv("AUTO_END", "False").lower() == "true"
    
        self.THUMB_GEN: bool = getenv("THUMB_GEN", "True").lower() == "true"
        self.VIDEO_PLAY: bool = getenv("VIDEO_PLAY", "True").lower() == "true"

        try:
            self.PLAYER_STYLE: int = int(getenv("PLAYER_STYLE", "4"))
        except (ValueError, TypeError):
            self.PLAYER_STYLE: int = 4
        self.AUTO_ROTATE: bool = getenv("AUTO_ROTATE", "False").lower() == "true"
        self.THUMBNAIL_REVEAL: bool = getenv("THUMBNAIL_REVEAL", "False").lower() == "true"

        self.LANG_CODE = getenv("LANG_CODE", "en")

        self.COOKIES_URL = [
            url for url in getenv("COOKIES_URL", "").split(" ")
            if url and "batbin.me" in url
        ]
        self.CREDIT_LINK = getenv("CREDIT_LINK", "https://t.me/apurvapex1")
        self.DEFAULT_THUMB = getenv("DEFAULT_THUMB", "https://te.legra.ph/file/3e40a408286d4eda24191.jpg")
        self.PING_IMG = getenv("PING_IMG", "https://iili.io/C0dXsHJ.jpg")
        self.START_IMG = getenv("START_IMG", "anony/assets/start.jpg")

    def check(self):
        missing = [
            var
            for var in ["API_ID", "API_HASH", "BOT_TOKEN", "MONGO_URL", "LOGGER_ID", "OWNER_ID", "SESSION1"]
            if not getattr(self, var)
        ]
        if missing:
            raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")
