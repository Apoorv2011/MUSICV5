# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic


from pyrogram import enums, types

from anony import app, config, lang
from anony.core.lang import lang_codes


class Inline:
    def __init__(self):
        self.ikm = types.InlineKeyboardMarkup
        self.ikb = self._styled_button

    @staticmethod
    def _styled_button(**kwargs) -> types.InlineKeyboardButton:
        """Create a colorful inline button without changing its action."""
        kwargs.setdefault("style", enums.ButtonStyle.PRIMARY)
        return types.InlineKeyboardButton(**kwargs)

    def cancel_dl(self, text) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=text, callback_data=f"cancel_dl")]])

    @staticmethod
    def _progress_bar(timer: str) -> str:
        """Convert 'MM:SS | ──◉── | -MM:SS' timer into a visual progress bar label.

        The update_timer task in misc.py produces:
            '{played} | {dashes}◉{dashes} | -{remaining}'
        We parse elapsed and remaining to compute ratio and render ▰/▱ bar.
        """
        try:
            parts = [p.strip() for p in timer.split("|")]
            if len(parts) == 3:
                def to_secs(t: str) -> int:
                    t = t.lstrip("-").strip()
                    p = t.split(":")
                    return int(p[0]) * 60 + int(p[1]) if len(p) == 2 else int(p[0])
                elapsed   = to_secs(parts[0])
                remaining = to_secs(parts[2])
                total     = elapsed + remaining
                if total > 0:
                    ratio   = elapsed / total
                    bar_len = 10
                    filled  = round(ratio * bar_len)
                    bar     = "▰" * filled + "▱" * (bar_len - filled)
                    def fmt(s: int) -> str:
                        m, s2 = divmod(s, 60)
                        return f"{m:02d}:{s2:02d}"
                    return f"⏱ {fmt(elapsed)} {bar} {fmt(total)}"
        except Exception:
            pass
        return timer

    def controls(
        self,
        chat_id: int,
        status: str = None,
        timer: str = None,
        remove: bool = False,
    ) -> types.InlineKeyboardMarkup:
        keyboard = []
        if status:
            keyboard.append(
                [self.ikb(text=status, callback_data=f"controls status {chat_id}")]
            )
        elif timer:
            bar_label = self._progress_bar(timer)
            keyboard.append(
                [self.ikb(text=bar_label, callback_data=f"controls status {chat_id}")]
            )

        if not remove:
            keyboard.append(
                [
                    self.ikb(text="▶️", callback_data=f"controls resume {chat_id}"),
                    self.ikb(text="⏸", callback_data=f"controls pause {chat_id}"),
                    self.ikb(text="🔄", callback_data=f"controls replay {chat_id}"),
                    self.ikb(text="⏭", callback_data=f"controls skip {chat_id}"),
                    self.ikb(text="⏹", callback_data=f"controls stop {chat_id}"),
                ]
            )
            keyboard.append(
                [self.ikb(text="🎨 ᴅᴇsɪɢɴ", callback_data=f"design pick {chat_id}")]
            )
            keyboard.append(
                [
                    self.ikb(
                        text="💡 sᴜɢɢᴇsᴛ",
                        callback_data=f"suggest {chat_id}",
                    ),
                    self.ikb(
                        text="💗 ғᴀᴠ",
                        callback_data=f"fav {chat_id}",
                    ),
                ]
            )
            keyboard.append(
                [self.ikb(text="╳  ᴄʟᴏsᴇ  ╳", callback_data=f"controls close {chat_id}")]
            )
        return self.ikm(keyboard)

    def suggestions_markup(
        self, chat_id: int, songs: list[dict]
    ) -> types.InlineKeyboardMarkup:
        rows = [
            [
                self.ikb(
                    text=f"♪ {song['label']}",
                    callback_data=f"suggest_play {chat_id} {song['video_id']}",
                )
            ]
            for song in songs
        ]
        rows.append(
            [self.ikb(text="↩ ʙᴀᴄᴋ ᴛᴏ ᴘʟᴀʏᴇʀ", callback_data=f"suggest_back {chat_id}")]
        )
        return self.ikm(rows)

    def favorites_markup(self, songs: list[dict]) -> types.InlineKeyboardMarkup:
        rows = [
            [
                self.ikb(
                    text=f"{index + 1}. ♪ {song.get('title', 'Unknown')[:42]}",
                    callback_data=f"favplay {index}",
                )
            ]
            for index, song in enumerate(songs)
        ]
        return self.ikm(rows)

    def help_markup(
        self, _lang: dict, back: bool = False
    ) -> types.InlineKeyboardMarkup:
        if back:
            rows = [
                [
                    self.ikb(text=_lang["back"], callback_data="help back"),
                    self.ikb(text=_lang["close"], callback_data="help close"),
                ]
            ]
        else:
            cbs = ["admins", "auth", "blist", "lang", "ping", "play", "queue", "stats", "sudo"]
            buttons = [
                self.ikb(text=_lang[f"help_{i}"], callback_data=f"help {cb}")
                for i, cb in enumerate(cbs)
            ]
            rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]

        return self.ikm(rows)

    def lang_markup(self, _lang: str) -> types.InlineKeyboardMarkup:
        langs = lang.get_languages()

        buttons = [
            self.ikb(
                text=f"{name} ({code}) {'✔️' if code == _lang else ''}",
                callback_data=f"lang_change {code}",
            )
            for code, name in langs.items()
        ]
        rows = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]
        return self.ikm(rows)

    def ping_markup(self, text: str) -> types.InlineKeyboardMarkup:
        return self.ikm([[self.ikb(text=text, url=config.SUPPORT_CHAT)]])

    def play_queued(
        self, chat_id: int, item_id: str, _text: str
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=_text, callback_data=f"controls force {chat_id} {item_id}"
                    )
                ]
            ]
        )

    def queue_markup(
        self, chat_id: int, _text: str, playing: bool
    ) -> types.InlineKeyboardMarkup:
        _action = "pause" if playing else "resume"
        return self.ikm(
            [[self.ikb(text=_text, callback_data=f"controls {_action} {chat_id} q")]]
        )

    def settings_markup(
        self, lang: dict, admin_only: bool, cmd_delete: bool, language: str, chat_id: int
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(
                        text=lang["play_mode"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(text=admin_only, callback_data="settings play"),
                ],
                [
                    self.ikb(
                        text=lang["cmd_delete"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(text=cmd_delete, callback_data="settings delete"),
                ],
                [
                    self.ikb(
                        text=lang["language"] + " ➜",
                        callback_data="settings",
                    ),
                    self.ikb(text=lang_codes[language], callback_data="language"),
                ],
            ]
        )

    def start_key(
        self, lang: dict, private: bool = False
    ) -> types.InlineKeyboardMarkup:
        rows = [
            [
                self.ikb(
                    text="✦ 𝐀ᴅᴅ 𝐌‌ᴇ 𝐓‌ᴏ 𝐘‌ᴏᴜʀ 𝐆‌ʀᴏᴜᴘ ✦",
                    url=f"https://t.me/{app.username}?startgroup=true",
                )
            ],
            [
                self.ikb(text="🎵 𝐇‌єʟᴘ 𝐀ηᴅ 𝐂‌σᴍᴍᴧηᴅs", callback_data="help"),
                self.ikb(text="𝐂‌ʜᴧᴛ ↗", url="https://t.me/apurvapex1"),
            ],
            [
                self.ikb(text="𝐀ᴘᴜʀᴠ ", url="https://t.me/@IsolatedBytes"),
                self.ikb(text="𝐒‌ᴜᴘᴘσꝛᴛ ↗", url=config.SUPPORT_CHAT),
            ],
            [
                self.ikb(text="𝐂‌ʜᴧηηєʟ ↗", url=config.SUPPORT_CHANNEL),
            ],
        ]
        if not private:
            rows += [[self.ikb(text=lang["language"], callback_data="language")]]
        return self.ikm(rows)

    def yt_key(self, link: str) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self.ikb(text="❐", copy_text=link),
                    self.ikb(text="Youtube", url=link),
                ],
            ]
        )
