
import re

from pyrogram import errors, filters, types

from anony import anon, app, db, lang, queue, tg, yt
from anony.helpers import admin_check, buttons, can_manage_vc


BOT_PLAY_BUTTON_DETAILS = """✦ ʙσϯ ρℓαγ ʙυϯϯση ᴅєϯαɪʟѕ :
ᴍαηαɢє γσυʀ ᴍυѕɪᴄ ρℓαγʙαᴄκ ᴅɪʀєᴄϯℓγ ϯнʀσυɢн ɪηℓɪηє ʙυϯϯσηѕ ωɪϯн єαѕє.

✦ ʙσϯ ρℓαγ ʙυϯϯση ᴅєϯαɪʟѕ :
⇢ ▷ : ʀєѕυᴍє ϯнє ραυѕєᴅ ѕϯʀєαᴍ.
⇢ ɪɪ : ραυѕє ϯнє σηɢσɪηɢ ѕϯʀєαᴍ.
⇢ ↻ : ʀєρℓαγ ϯнє ᴄυʀʀєηϯ ѕσηɢ ғʀσᴍ ѕϯαʀϯ.
⇢ ‣‣ɪ : ѕκɪρ ϯнє ᴄυʀʀєηϯ ϯʀαᴄκ αηᴅ ρℓαγ ηєχϯ.
⇢ ▢ : ѕϯσρ ϯнє ρℓαγʙαᴄκ αηᴅ ᴄℓєαʀ ǫυєυє.

✦ ʙσϯ ρℓαγ ʙυϯϯση ᴅєϯαɪʟѕ :
⇢ -𝟷𝟻ˢ : ѕєєκ ʙαᴄκωαʀᴅ ʙγ 15 ѕєᴄσηᴅѕ.
⇢ 𝟷𝟻ˢ+ : ѕєєκ ғσʀωαʀᴅ ʙγ 15 ѕєᴄσηᴅѕ.
⇢ ᴍσʀє : σρєη αᴅναηᴄєᴅ ѕєϯϯɪηɢѕ ᴍєηυ.

⫷ ѕєϯϯɪηɢѕ & ᴍσᴅєѕ :
⇢ ⊘ : ᴍυϯє αѕѕɪѕϯαηϯ ɪη νɪᴅєσ ᴄнαϯ.
⇢ ♷ : єηαʙℓє σʀ ᴅɪѕαʙℓє ℓσσρ ᴍσᴅє.
⇢ ᴀ‣I : ϯσɢɢℓє αυϯσ-ѕκɪρ σʀ ϯʀαᴄκ ᴍσᴅє.
⇢ ⏣ : υηᴍυϯє αѕѕɪѕϯαηϯ ɪη νɪᴅєσ ᴄнαϯ.
⇢ ♫ αυϯσρℓαγ : ϯσɢɢℓє αυϯσᴍαϯɪᴄαℓℓγ ρℓαγ ʀєℓαϯєᴅ ѕσηɢѕ σғ/ση.
⇢ ⎘ ϯнυᴍʙηαɪℓ : ϯσɢɢℓє ϯнυᴍʙηαɪʟ ᴅɪѕρℓαγ ση/σғғ.

❏ αℓℓ ʙυϯϯσηѕ σηℓγ ғσʀ ɢʀσυρ αᴅᴍɪηѕ."""

_MUSIC_HELP_KEYS = {
    "admins",
    "auth",
    "blist",
    "lang",
    "ping",
    "play",
    "queue",
    "stats",
    "sudo",
}

_SEARCH_HELP_TEXT = {
    "pinterest": "✦ <b>Pɪɴᴛᴇʀᴇsᴛ</b>\n\nPinterest search is available from this menu.",
    "song": "✦ <b>Sᴏɴɢ</b>\n\nUse <code>/play song name</code> to search and play a song.",
    "lyrics": "✦ <b>Lʏʀɪᴄs</b>\n\nLyrics search is available from this menu.",
    "wallpaper": "✦ <b>Wᴀʟʟᴘᴀᴘᴇʀ</b>\n\nUse <code>/img your wallpaper prompt</code> to generate a wallpaper.",
}

_MANAGEMENT_HELP_TEXT = {
    "claude": "✦ <b>Cʟᴀᴜᴅᴇ</b>\n\nUse <code>/ai your question</code> to chat with Claude.",
    "fun": "✦ <b>Fᴜɴ & Gᴀᴍᴇs</b>\n\nFun and game commands are grouped here.",
    "image": "✦ <b>Iᴍᴀɢᴇ</b>\n\nUse <code>/img your prompt</code> to generate an image.",
    "group": "✦ <b>Gʀᴏᴜᴘ</b>\n\nUse the group, authorization, blacklist, and settings commands from the Music menu.",
    "nast": "✦ <b>Nᴀsᴛ</b>\n\nNast tools are grouped here.",
    "mass": "✦ <b>Mᴀss Aᴄᴛɪᴏɴ</b>\n\nUse <code>/broadcast</code> to send a message to the bot's chats.",
    "ping": "✦ <b>Pɪɴɢ</b>\n\nUse <code>/ping</code> to check bot latency and system status.",
}

_EXTRA_HELP_TEXT = {
    "tagall": "✦ <b>Tᴀɢ-Aʟʟ</b>\n\nTag-all tools are grouped in Extra.",
    "textedit": "✦ <b>Tᴇxᴛ Eᴅɪᴛ</b>\n\nText editing tools are grouped in Extra.",
    "autobroad": "✦ <b>Aᴜᴛᴏ Bʀᴏᴀᴅ</b>\n\nAutomatic broadcast tools are grouped in Extra.",
    "util": "✦ <b>Uᴛɪʟ / Fᴜɴ</b>\n\nUtility and fun tools are grouped in Extra.",
}


async def _edit_help_page(query: types.CallbackQuery, text: str, markup) -> None:
    """Edit either a text help message or the caption of the /start photo."""
    await query.answer()
    try:
        if query.message.photo:
            await query.edit_message_caption(caption=text, reply_markup=markup)
        else:
            await query.edit_message_text(text=text, reply_markup=markup)
    except Exception:
        pass


@app.on_callback_query(filters.regex("cancel_dl") & ~app.bl_users)
@lang.language()
async def cancel_dl(_, query: types.CallbackQuery):
    await query.answer()
    await tg.cancel(query)


@app.on_callback_query(filters.regex("controls") & ~app.bl_users)
@lang.language()
@can_manage_vc
async def _controls(_, query: types.CallbackQuery):
    args = query.data.split()
    action, chat_id = args[1], int(args[2])
    qaction = len(args) == 4
    user = query.from_user.mention

    if not await db.get_call(chat_id):
        try:
            return await query.answer(query.lang["not_playing"], show_alert=True)
        except errors.QueryIdInvalid:
            try:
                await query.message.delete()
            except Exception:
                pass
            return

    if action == "status":
        return await query.answer()

    if action == "close":
        await query.answer()
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    if action in ("seekback", "seekforward"):
        media = queue.get_current(chat_id)
        if not media or not media.duration_sec:
            return await query.answer(
                query.lang["play_seek_no_dur"], show_alert=True
            )

        current_time = max(1, media.time or 1)
        delta = -15 if action == "seekback" else 15
        target = current_time + delta
        if target < 1:
            target = 1
        if target + 5 > media.duration_sec:
            target = max(1, media.duration_sec - 5)

        await query.answer(
            f"Seeking {'backward' if delta < 0 else 'forward'} 15 seconds…"
        )
        await anon.play_media(chat_id, query.message, media, target)
        media.time = target
        return

    await query.answer(query.lang["processing"], show_alert=True)

    if action == "pause":
        if not await db.playing(chat_id):
            return await query.answer(
                query.lang["play_already_paused"], show_alert=True
            )
        await anon.pause(chat_id)
        if qaction:
            return await query.edit_message_reply_markup(
                reply_markup=buttons.queue_markup(chat_id, query.lang["paused"], False)
            )
        status = query.lang["paused"]
        reply = query.lang["play_paused"].format(user)

    elif action == "resume":
        if await db.playing(chat_id):
            return await query.answer(query.lang["play_not_paused"], show_alert=True)
        await anon.resume(chat_id)
        if qaction:
            return await query.edit_message_reply_markup(
                reply_markup=buttons.queue_markup(chat_id, query.lang["playing"], True)
            )
        reply = query.lang["play_resumed"].format(user)

    elif action == "skip":
        await anon.play_next(chat_id)
        status = query.lang["skipped"]
        reply = query.lang["play_skipped"].format(user)

    elif action == "force":
        pos, media = queue.check_item(chat_id, args[3])
        if not media or pos == -1:
            return await query.edit_message_text(query.lang["play_expired"])

        m_id = queue.get_current(chat_id).message_id
        queue.force_add(chat_id, media, remove=pos)
        try:
            await app.delete_messages(
                chat_id=chat_id, message_ids=[m_id, media.message_id], revoke=True
            )
            media.message_id = None
        except Exception:
            pass

        msg = await app.send_message(chat_id=chat_id, text=query.lang["play_next"])
        if not media.file_path:
            media.file_path = await yt.download(media.id, video=media.video)
        media.message_id = msg.id
        return await anon.play_media(chat_id, msg, media)

    elif action == "replay":
        media = queue.get_current(chat_id)
        media.user = user
        await anon.replay(chat_id)
        status = query.lang["replayed"]
        reply = query.lang["play_replayed"].format(user)

    elif action == "stop":
        await anon.stop(chat_id)
        status = query.lang["stopped"]
        reply = query.lang["play_stopped"].format(user)

    try:
        if action in ["skip", "replay", "stop"]:
            await query.message.reply_text(reply, quote=False)
            await query.message.delete()
        else:
            mtext = re.sub(
                r"\n\n<blockquote>.*?</blockquote>",
                "",
                query.message.caption.html or query.message.text.html,
                flags=re.DOTALL,
            )
            keyboard = buttons.controls(
                chat_id, status=status if action != "resume" else None
            )
        await query.edit_message_text(
            f"{mtext}\n\n<blockquote>{reply}</blockquote>", reply_markup=keyboard
        )
    except Exception:
        pass


@app.on_callback_query(filters.regex("help") & ~app.bl_users)
@lang.language()
async def _help(_, query: types.CallbackQuery):
    data = query.data.split()
    if len(data) == 1:
        return await _edit_help_page(
            query,
            query.lang.get("help_main", query.lang["help_menu"]),
            buttons.help_main_markup(query.lang),
        )

    page = data[1]
    if page == "close":
        await query.answer()
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    if page == "back" or page == "main":
        return await _edit_help_page(
            query,
            query.lang.get("help_main", query.lang["help_menu"]),
            buttons.help_main_markup(query.lang),
        )

    if page == "music":
        if len(data) == 2:
            return await _edit_help_page(
                query,
                query.lang.get("help_music", query.lang["help_menu"]),
                buttons.help_music_markup(query.lang),
            )
        key = data[2]
        if key in _MUSIC_HELP_KEYS:
            return await _edit_help_page(
                query,
                query.lang[f"help_{key}"],
                buttons.help_detail_markup(query.lang, "help music"),
            )

    if page == "management":
        if len(data) == 2:
            return await _edit_help_page(
                query,
                query.lang.get("help_management", query.lang["help_menu"]),
                buttons.management_markup(query.lang),
            )
        key = data[2]
        if key == "action":
            return await _edit_help_page(
                query,
                query.lang["help_admins"],
                buttons.help_detail_markup(query.lang, "help management"),
            )
        if key in _MANAGEMENT_HELP_TEXT:
            return await _edit_help_page(
                query,
                _MANAGEMENT_HELP_TEXT[key],
                buttons.help_detail_markup(query.lang, "help management"),
            )

    if page == "search":
        if len(data) == 2:
            return await _edit_help_page(
                query,
                query.lang.get("help_search", query.lang["help_menu"]),
                buttons.search_markup(query.lang),
            )
        key = data[2]
        if key in _SEARCH_HELP_TEXT:
            return await _edit_help_page(
                query,
                _SEARCH_HELP_TEXT[key],
                buttons.help_detail_markup(query.lang, "help search"),
            )

    if page == "extra":
        if len(data) == 2:
            return await _edit_help_page(
                query,
                query.lang.get("help_extra", query.lang["help_menu"]),
                buttons.extras_markup(query.lang),
            )
        key = data[2]
        if key in _EXTRA_HELP_TEXT:
            return await _edit_help_page(
                query,
                _EXTRA_HELP_TEXT[key],
                buttons.help_detail_markup(query.lang, "help extra"),
            )

    if page == "bot":
        return await _edit_help_page(
            query,
            BOT_PLAY_BUTTON_DETAILS,
            buttons.help_detail_markup(query.lang, "help main"),
        )

    # Keep compatibility with old help callback data such as help admins.
    if page in _MUSIC_HELP_KEYS:
        return await _edit_help_page(
            query,
            query.lang[f"help_{page}"],
            buttons.help_detail_markup(query.lang, "help music"),
        )

    await query.answer()


@app.on_callback_query(filters.regex("settings") & ~app.bl_users)
@lang.language()
@admin_check
async def _settings_cb(_, query: types.CallbackQuery):
    cmd = query.data.split()
    if len(cmd) == 1:
        return await query.answer()
    await query.answer(query.lang["processing"], show_alert=True)

    chat_id = query.message.chat.id
    _admin = await db.get_play_mode(chat_id)
    _delete = await db.get_cmd_delete(chat_id)
    _language = await db.get_lang(chat_id)

    if cmd[1] == "delete":
        _delete = not _delete
        await db.set_cmd_delete(chat_id, _delete)
    elif cmd[1] == "play":
        await db.set_play_mode(chat_id, _admin)
        _admin = not _admin
    await query.edit_message_reply_markup(
        reply_markup=buttons.settings_markup(
            query.lang,
            _admin,
            _delete,
            _language,
            chat_id,
        )
    )
