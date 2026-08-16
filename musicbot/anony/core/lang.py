import json
from functools import wraps
from pathlib import Path

from pyrogram import errors

from anony import db, logger

lang_codes = {
    "ar": "العربية",
    "de": "Deutsch",
    "en": "English",
    "es": "Español",
    "fr": "Français",
    "hi": "हिन्दी",
    "ja": "日本語",
    "my": "မြန်မာဘာသာ",
    "pa": "ਪੰਜਾਬੀ",
    "pt": "Português",
    "ru": "Русский",
    "tr": "Türkçe",
    "zh": "中文"
}


class Language:
    """
    Language class for managing multilingual support using JSON language files.
    """

    def __init__(self):
        self.lang_codes = lang_codes
        # Resolve absolute directory relative to this file's location
        BASE_DIR = Path(__file__).resolve().parent.parent
        self.lang_dir = BASE_DIR / "locales"
        
        # Fallback search if locales folder is in root
        if not self.lang_dir.exists():
            self.lang_dir = Path("anony/locales").resolve()

        self.languages = self.load_files()

    def load_files(self):
        languages = {}
        if self.lang_dir.exists():
            lang_files = {file.stem: file for file in self.lang_dir.glob("*.json")}
            for lang_code, lang_file in lang_files.items():
                try:
                    with open(lang_file, "r", encoding="utf-8") as file:
                        languages[lang_code] = json.load(file)
                except Exception as e:
                    logger.warning(f"Failed to load language file {lang_file}: {e}")
        
        logger.info(f"Loaded languages: {', '.join(languages.keys()) if languages else 'None'}")
        return languages

    def _get_lang_dict(self, lang_code: str) -> dict:
        """Safely fetch language dictionary with fallbacks."""
        if lang_code in self.languages:
            return self.languages[lang_code]
        if "en" in self.languages:
            return self.languages["en"]
        if self.languages:
            return next(iter(self.languages.values()))
        return {}

    async def get_lang(self, chat_id: int) -> dict:
        try:
            lang_code = await db.get_lang(chat_id)
        except Exception:
            lang_code = "en"
        return self._get_lang_dict(lang_code)

    def get_languages(self) -> dict:
        if not self.lang_dir.exists():
            return {}
        files = {f.stem for f in self.lang_dir.glob("*.json")}
        return {code: self.lang_codes[code] for code in sorted(files) if code in self.lang_codes}

    def language(self):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                fallen = next(
                    (
                        arg
                        for arg in args
                        if hasattr(arg, "chat") or hasattr(arg, "message")
                    ),
                    None,
                )

                if not fallen or not getattr(fallen, "from_user", None):
                    return

                if hasattr(fallen, "chat"):
                    chat = fallen.chat
                elif hasattr(fallen, "message"):
                    chat = fallen.message.chat
                else:
                    chat = None

                if not chat:
                    return

                if hasattr(db, "blacklisted") and chat.id in db.blacklisted:
                    logger.info(f"Chat {chat.id} is blacklisted, leaving...")
                    return await chat.leave()

                try:
                    lang_code = await db.get_lang(chat.id)
                except Exception:
                    lang_code = getattr(fallen.from_user, "language_code", "en") or "en"

                lang_dict = self._get_lang_dict(lang_code)

                setattr(fallen, "lang", lang_dict)
                try:
                    return await func(*args, **kwargs)
                except (errors.ChannelPrivate, errors.MessageIdInvalid, errors.MessageNotModified):
                    return
                except (
                    errors.Forbidden, errors.exceptions.Forbidden,
                    errors.ChatWriteForbidden, errors.exceptions.ChatWriteForbidden,
                ):
                    return

            return wrapper

        return decorator
