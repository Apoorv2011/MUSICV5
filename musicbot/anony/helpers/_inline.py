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

    @staticmethod
    def _button_style(index: int):
        """Cycle through Telegram's button colors for the help menus."""
        styles = (
            enums.ButtonStyle.PRIMARY,
            getattr(enums.ButtonStyle, "SUCCESS", enums.ButtonStyle.PRIMARY),
            getattr(enums.ButtonStyle, "DANGER", enums.ButtonStyle.PRIMARY),
        )
        return styles[index % len(styles)]

    def _color_button(self, text: str, callback_data: str, index: int):
        return self.ikb(
            text=text,
            callback_data=callback_data,
            style=self._button_style(index),
        )

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
            try:
                from anony.plugins.autoplay import AUTO_STATE, THUMBNAIL_STATE
                autoplay_on = AUTO_STATE.get(chat_id, True)
                thumbnail_on = THUMBNAIL_STATE.get(
                    chat_id, getattr(config, "THUMB_GEN", True)
                )
            except Exception:
                autoplay_on = True
                thumbnail_on = getattr(config, "THUMB_GEN", True)

            keyboard.append(
                [
                    self._color_button("▷", f"controls resume {chat_id}", 1),
                    self._color_button("II", f"controls pause {chat_id}", 0),
                    self._color_button("↻", f"controls replay {chat_id}", 1),
                    self._color_button("‣‣I", f"controls skip {chat_id}", 0),
                    self._color_button("▢", f"controls stop {chat_id}", 2),
                ]
            )
            keyboard.append(
                [
                    self._color_button(
                        "-𝟷𝟻", f"controls seekback {chat_id}", 2
                    ),
                    self._color_button(
                        "𝟷𝟻+", f"controls seekforward {chat_id}", 1
                    ),
                ]
            )
            keyboard.append(
                [
                    self._color_button("✦ sᴜɢɢᴇsᴛ", f"suggest {chat_id}", 0),
                    self._color_button("✦ ғᴀᴠ", f"fav {chat_id}", 2),
                ]
            )
            keyboard.append(
                [
                    self._color_button(
                        f"ᴀᴜᴛᴏᴘʟᴀʏ {'🟢' if autoplay_on else '🔴'}",
                        f"autoplay toggle {chat_id}",
                        1 if autoplay_on else 2,
                    ),
                    self._color_button(
                        f"ᴛʜᴜᴍʙɴᴀɪʟ {'🟢' if thumbnail_on else '🔴'}",
                        f"thumbnail toggle {chat_id}",
                        1 if thumbnail_on else 2,
                    ),
                ]
            )
            keyboard.append(
                [
                    self._color_button(
                        "◎ ᴄʟᴏsᴇ ◎", f"controls close {chat_id}", 2
                    )
                ]
            )
        return self.ikm(keyboard)

    def suggestions_markup(
        self, chat_id: int, songs: list[dict], video_id: str | None = None, page: int = 0
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
        nav_buttons = []
        if page > 0 and video_id:
            nav_buttons.append(
                self.ikb(text="⟨ Prev", callback_data=f"suggest_page {chat_id} {video_id} {page-1}")
            )
        nav_buttons.append(self.ikb(text="↩ ʙᴀᴄᴋ", callback_data=f"suggest_back {chat_id}"))
        if video_id:
            nav_buttons.append(
                self.ikb(text="Next ⟩", callback_data=f"suggest_page {chat_id} {video_id} {page+1}")
            )
        rows.append(nav_buttons)
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

    def _help_nav(self, _lang: dict, callback_data: str = "help main"):
        return [
            self._color_button(f"◎ {_lang.get('back', 'Back')} ◎", callback_data, 0),
            self._color_button(
                f"◎ {_lang.get('close', 'Close')} ◎", "help close", 2
            ),
        ]

    def help_main_markup(self, _lang: dict) -> types.InlineKeyboardMarkup:
        """Top-level help menu matching the requested category layout."""
        rows = [
            [
                self._color_button("☯ Mᴜsɪᴄ", "help music", 0),
                self._color_button("⚕ Mᴀɴᴀɢᴇᴍᴇɴᴛ", "help management", 1),
            ],
            [self._color_button("◉ Sᴇᴀʀᴄʜ", "help search", 2)],
            [
                self._color_button(
                    "Bᴏᴛ Pʟᴀʏ Bᴜᴛᴛᴏɴs", "help bot", 0
                )
            ],
            self._help_nav(_lang),
        ]
        return self.ikm(rows)

    def help_music_markup(self, _lang: dict) -> types.InlineKeyboardMarkup:
        """The original command categories, now nested under Music."""
        cbs = [
            "admins",
            "auth",
            "blist",
            "lang",
            "ping",
            "play",
            "queue",
            "stats",
            "sudo",
        ]
        buttons = [
            self._color_button(
                _lang.get(f"help_{i}", label),
                f"help music {cb}",
                index,
            )
            for index, (i, cb, label) in enumerate(
                (
                    (0, "admins", "Admins"),
                    (1, "auth", "Auth"),
                    (2, "blist", "Blacklist"),
                    (3, "lang", "Language"),
                    (4, "ping", "Ping"),
                    (5, "play", "Play"),
                    (6, "queue", "Queue"),
                    (7, "stats", "Stats"),
                    (8, "sudo", "Sudoers"),
                )
            )
        ]
        rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
        rows.append(self._help_nav(_lang))
        return self.ikm(rows)

    def management_markup(self, _lang: dict) -> types.InlineKeyboardMarkup:
        """Management categories based on the second reference image."""
        labels = (
            ("✦ Aᴄᴛɪᴏɴ", "help management action"),
            ("✦ Exᴛʀᴀ", "help extra"),
            ("✦ Cʟᴀᴜᴅᴇ", "help management claude"),
            ("✦ Fᴜɴ & Gᴀᴍᴇs", "help management fun"),
            ("✦ Iᴍᴀɢᴇ", "help management image"),
            ("✦ Gʀᴏᴜᴘ", "help management group"),
            ("✦ ᴍᴀsᴛɪ", "help management  masti"),
            ("✦ Mᴀss Aᴄᴛɪᴏɴ", "help management mass"),
            ("✦ Pɪɴɢ", "help management ping"),
        )
        buttons = [
            self._color_button(text, callback, index)
            for index, (text, callback) in enumerate(labels)
        ]
        rows = [buttons[i : i + 3] for i in range(0, len(buttons), 3)]
        rows.append(self._help_nav(_lang))
        return self.ikm(rows)

    def search_markup(self, _lang: dict) -> types.InlineKeyboardMarkup:
        """Search options requested for the Search category."""
        labels = (
            ("✦ Pɪɴᴛᴇʀᴇsᴛ", "help search pinterest"),
            ("✦ Sᴏɴɢ", "help search song"),
            ("✦ Lʏʀɪᴄs", "help search lyrics"),
            ("✦ Wᴀʟʟᴘᴀᴘᴇʀ", "help search wallpaper"),
        )
        buttons = [
            self._color_button(text, callback, index)
            for index, (text, callback) in enumerate(labels)
        ]
        rows = [buttons[:2], buttons[2:], self._help_nav(_lang)]
        return self.ikm(rows)

    def extras_markup(self, _lang: dict) -> types.InlineKeyboardMarkup:
        """Extra tools from the third reference image, excluding requested items."""
        labels = (
            ("✦ Tᴀɢ-Aʟʟ", "help extra tagall"),
            ("✦ Tᴇxᴛ Eᴅɪᴛ", "help extra textedit"),
            ("✦ Aᴜᴛᴏ Bʀᴏᴀᴅ", "help extra autobroad"),
            ("✦ Uᴛɪʟ / Fᴜɴ", "help extra util"),
        )
        buttons = [
            self._color_button(text, callback, index)
            for index, (text, callback) in enumerate(labels)
        ]
        return self.ikm(
            [
                buttons[:2],
                buttons[2:],
                [
                    self._color_button(
                        f"◎ {_lang.get('back', 'Back')} ◎", "help management", 0
                    ),
                    self._color_button("△ Mᴇɴᴜ", "help main", 1),
                    self._color_button(
                        f"◎ {_lang.get('close', 'Close')} ◎", "help close", 2
                    ),
                ],
            ]
        )

    def help_detail_markup(
        self, _lang: dict, back_callback: str = "help music"
    ) -> types.InlineKeyboardMarkup:
        return self.ikm(
            [
                [
                    self._color_button(
                        f"◎ {_lang.get('back', 'Back')} ◎",
                        back_callback,
                        0,
                    ),
                    self._color_button(
                        f"◎ {_lang.get('close', 'Close')} ◎",
                        "help close",
                        2,
                    ),
                ]
            ]
        )

    def help_markup(
        self, _lang: dict, back: bool = False
    ) -> types.InlineKeyboardMarkup:
        """Compatibility wrapper for plugins that still call help_markup."""
        if back:
            return self.help_detail_markup(_lang)
        return self.help_main_markup(_lang)

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
        self,
        lang: dict,
        admin_only: bool,
        cmd_delete: bool,
        language: str,
        chat_id: int,
        bio_link: bool = False,
    ) -> types.InlineKeyboardMarkup:
        from player_style import get_style

        style = get_style(chat_id)
        style_name = {
            1: "Design 1",
            2: "Design 2",
            3: "Design 3",
            4: "Default",
        }.get(style, f"Design {style}")

        return self.ikm(
            [
                [
                    self._color_button(
                        text=lang["play_mode"] + " ➜",
                        callback_data="settings",
                        index=0,
                    ),
                    self._color_button(
                        text=str(admin_only),
                        callback_data="settings play",
                        index=1 if admin_only else 2,
                    ),
                ],
                [
                    self._color_button(
                        text=lang["cmd_delete"] + " ➜",
                        callback_data="settings",
                        index=0,
                    ),
                    self._color_button(
                        text=str(cmd_delete),
                        callback_data="settings delete",
                        index=1 if cmd_delete else 2,
                    ),
                ],
                [
                    self._color_button(
                        text=lang["language"] + " ➜",
                        callback_data="settings",
                        index=0,
                    ),
                    self._color_button(
                        text=lang_codes[language],
                        callback_data="language",
                        index=1,
                    ),
                ],
                [
                    self._color_button(
                        text="Thumb design ➜",
                        callback_data=f"design pick {chat_id}",
                        index=0,
                    ),
                    self._color_button(
                        text=style_name,
                        callback_data=f"design pick {chat_id}",
                        index=1,
                    ),
                ],
                [
                    self._color_button(
                        text="Bio link ➜",
                        callback_data="settings",
                        index=0,
                    ),
                    self._color_button(
                        text=str(bio_link),
                        callback_data="settings biolink",
                        index=1 if bio_link else 2,
                    ),
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


