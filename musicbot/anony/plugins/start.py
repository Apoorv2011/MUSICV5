# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import asyncio
import os
import random
import time

import psutil
from pyrogram import enums, filters, types

from anony import app, boot, config, db, lang
from anony.helpers import buttons, utils


# ── fullscreen animation effect IDs ────────────────────────────────────────
_EFFECTS = [
    5104841245755180586,   # 🔥 Fire
    5044134455711629726,   # 💜 Heart
    5046509860389126442,   # 🎉 Party
]

# ── sticker cache ───────────────────────────────────────────────────────────
_STICKER_CACHE = "cache/start_sticker.txt"


def _load_sticker_id() -> str | None:
    try:
        if os.path.exists(_STICKER_CACHE):
            s = open(_STICKER_CACHE).read().strip()
            return s or None
    except Exception:
        pass
    return None


def _save_sticker_id(file_id: str) -> None:
    os.makedirs("cache", exist_ok=True)
    with open(_STICKER_CACHE, "w") as f:
        f.write(file_id)


def _format_uptime(seconds: int) -> str:
    days, remainder = divmod(max(0, seconds), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    if days:
        return f"{days}ᴅ:{hours}ʜ:{minutes}ᴍ"
    if hours:
        return f"{hours}ʜ:{minutes}ᴍ:{seconds}s"
    return f"{minutes}ᴍ:{seconds}s"


async def _build_start_pm(user_mention: str) -> str:
    """Build the branded DM welcome text with live bot statistics."""
    uptime = _format_uptime(int(time.time() - boot))
    disk = psutil.disk_usage("/").percent
    cpu = psutil.cpu_percent(interval=0)
    ram = psutil.virtual_memory().percent
    users = len(await db.get_users())
    chats = len(await db.get_chats())
    return (
        f"✦ Ꭲʜᴧηᴋ 𝐘‌συ {user_mention}, 𝐅‌σꝛ 𝚺ηᴛєꝛɪηɢ 𝐈η 𝐘ᴜᴋɪ 𝐑‌єᴧʟϻ.\n"
        f"➻ 𝐏‌ꝛєsєηᴛɪηɢ ˹𝐘ᴜᴋɪ ꭙ 𝐌ᴜꜱɪᴄ˼ ♪ 🌸 "
        f"(𝐔𝐩𝐝𝐚𝐭𝐢𝐧𝐠) ㋡ — Λη 𝐈ϻϻєꝛsɪᴠє 𝛅σηɪᴄ 𝚺xᴘєꝛɪєηᴄє.\n\n"
        f"➤ 𝐄‌ηɢɪηєєʀєᴅ 𝐅‌σꝛ 𝐅‌ʟυɪᴅ 𝐕‌σɪᴄє 𝛅ᴛꝛєᴧϻɪηɢ Ληᴅ "
        f"𝐔‌ηɪηᴛєꝛꝛυᴘᴛєᴅ 𝐏‌ʟᴧʏʙᴧᴄᴋ.\n"
        f"➤ 𝐑‌єᴘʟɪᴄᴧᴛє Ꭲʜє 𝚺ηᴛɪꝛє 𝚺ᴄσsʏsᴛєϻ 𝐈ηᴛσ 𝐘‌συꝛ "
        f"𝐎‌ᴡη 𝐈ᴅєηᴛɪᴛʏ 𝐖‌ɪᴛʜ 𝐉‌υsᴛ Λ 𝐅‌єᴡ Ꭲᴧᴘs.\n"
        "•── ⋅ ⋅ ⋅ ──────── ⋅ • ⋅ ──────── ⋅ ⋅ ⋅ ──•\n"
        "➤ 𝐎‌ᴘєη Ꭲʜє 𝐇‌єʟᴘ 𝐏‌ᴧηєʟ Ꭲσ 𝐔‌ηᴄσᴠєꝛ 𝚺ᴠєꝛʏ "
        "𝐂‌ᴧᴘᴧʙɪʟɪᴛʏ.\n\n"
        "<blockquote>"
        f"<tg-spoiler>✫ υρϯɪᴍє : {uptime}</tg-spoiler>\n"
        f"<tg-spoiler>✫ ᴅɪsᴋ : {disk:.1f}%  |  ᴄᴘᴜ : {cpu:.1f}%</tg-spoiler>\n"
        f"<tg-spoiler>✫ ʀᴀᴍ : {ram:.1f}%</tg-spoiler>\n"
        f"<tg-spoiler>✫ υѕєʀѕ : {users}  |  ᴄнαᴛѕ : {chats}</tg-spoiler>"
        "</blockquote>\n\n"
        "🫧 ᴅєνєℓσᴩєʀ 🪽 ➪ 𝐀ᴘᴜʀᴠ ✔︎"
    )


# ── owner sticker capture ────────────────────────────────────────────────────

@app.on_message(filters.private & filters.sticker)
async def _capture_sticker(_, m: types.Message):
    """When the bot owner sends a sticker in private, save its file_id."""
    if m.from_user.id != config.OWNER_ID:
        return
    _save_sticker_id(m.sticker.file_id)
    await m.reply_text(
        "✅ <b>sᴛɪᴄᴋᴇʀ sᴀᴠᴇᴅ!</b>\n"
        "I'll send this to every user who /start's me 🎁",
        quote=True,
    )


# ── help command ─────────────────────────────────────────────────────────────

@app.on_message(filters.command(["help"]) & filters.private & ~app.bl_users)
@lang.language()
async def _help(_, m: types.Message):
    await m.reply_text(
        text=m.lang["help_menu"],
        reply_markup=buttons.help_markup(m.lang),
        quote=True,
    )


# ── start command ─────────────────────────────────────────────────────────────

@app.on_message(filters.command(["start"]))
@lang.language()
async def start(_, message: types.Message):
    if message.from_user.id in app.bl_users and message.from_user.id not in db.notified:
        return await message.reply_text(message.lang["bl_user_notify"])

    if len(message.command) > 1 and message.command[1] == "help":
        return await _help(_, message)

    private = message.chat.type == enums.ChatType.PRIVATE

    if private:
        effect_id = random.choice(_EFFECTS)
        sticker_id = _load_sticker_id()

        # 1️⃣  Send sticker — give the user 3 seconds to actually see it, then delete
        if sticker_id:
            try:
                sticker_msg = await app.send_sticker(
                    chat_id=message.chat.id,
                    sticker=sticker_id,
                )
                await asyncio.sleep(3)
                await sticker_msg.delete()
            except Exception:
                pass

        # 2️⃣  Fire fullscreen animation via a text message (effect_id is only
        #     guaranteed on text/sticker messages, not photos).
        #     Wait 2.5s so the animation (fire/heart/party ~2s) finishes fully,
        #     then delete the trigger text before the photo arrives.
        try:
            effect_msg = await app.send_message(
                chat_id=message.chat.id,
                text="🎶",
                effect_id=effect_id,
            )
            await asyncio.sleep(2.5)
            await effect_msg.delete()
        except Exception:
            pass

        # 3️⃣  Intro photo arrives after animation is done
        _text = await _build_start_pm(message.from_user.mention)
        key   = buttons.start_key(message.lang, private=True)

        try:
            await app.send_photo(
                chat_id=message.chat.id,
                photo=config.START_IMG,
                caption=_text,
                reply_markup=key,
            )
        except Exception:
            await message.reply_text(text=_text, reply_markup=key, quote=False)

        # Register new user
        if await db.is_user(message.from_user.id):
            return
        await utils.send_log(message)
        await db.add_user(message.from_user.id)

    else:
        # Group /start
        _text = message.lang["start_gp"].format(app.name)
        key = buttons.start_key(message.lang, private=False)
        await message.reply_photo(
            photo=config.START_IMG,
            caption=_text,
            reply_markup=key,
            quote=True,
        )
        if await db.is_chat(message.chat.id):
            return
        await utils.send_log(message, True)
        await db.add_chat(message.chat.id)


# ── settings command ──────────────────────────────────────────────────────────

@app.on_message(filters.command(["playmode", "settings"]) & filters.group & ~app.bl_users)
@lang.language()
async def settings(_, message: types.Message):
    admin_only = await db.get_play_mode(message.chat.id)
    cmd_delete = await db.get_cmd_delete(message.chat.id)
    _language = await db.get_lang(message.chat.id)
    await message.reply_text(
        text=message.lang["start_settings"].format(message.chat.title),
        reply_markup=buttons.settings_markup(
            message.lang, admin_only, cmd_delete, _language, message.chat.id
        ),
        quote=True,
    )


@app.on_message(filters.new_chat_members, group=7)
@lang.language()
async def _new_member(_, message: types.Message):
    if message.chat.type != enums.ChatType.SUPERGROUP:
        return await message.chat.leave()

    await asyncio.sleep(3)
    for member in message.new_chat_members:
        if member.id == app.id:
            if await db.is_chat(message.chat.id):
                return
            await utils.send_log(message, True)
            await db.add_chat(message.chat.id)
