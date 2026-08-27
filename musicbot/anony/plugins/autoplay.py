from collections import defaultdict, deque

from pyrogram import filters, types

from anony import app, config, db, lang, yt
from anony.helpers import Track, buttons, can_manage_vc
from anony.plugins.suggest import _recommend, _resolve_video_id


AUTO_STATE: dict[int, bool] = {}
THUMBNAIL_STATE: dict[int, bool] = {}
_RECENT: dict[int, deque[str]] = defaultdict(lambda: deque(maxlen=15))


async def is_autoplay_on(chat_id: int) -> bool:
    enabled = await db.get_autoplay(chat_id)
    AUTO_STATE[chat_id] = enabled
    return enabled


async def toggle_autoplay(chat_id: int) -> bool:
    enabled = await db.toggle_autoplay(chat_id)
    AUTO_STATE[chat_id] = enabled
    return enabled


async def is_thumbnail_on(chat_id: int) -> bool:
    enabled = await db.get_thumbnail(chat_id)
    THUMBNAIL_STATE[chat_id] = enabled
    return enabled


async def toggle_thumbnail(chat_id: int) -> bool:
    enabled = await db.toggle_thumbnail(chat_id)
    THUMBNAIL_STATE[chat_id] = enabled
    return enabled


async def get_autoplay_track(chat_id: int, finished: Track | None) -> Track | None:
    """Return one related track for the normal queue lifecycle to play."""
    if not finished or not await is_autoplay_on(chat_id):
        return None

    video_id = await _resolve_video_id(finished)
    if not video_id:
        return None

    try:
        recommendations = await _recommend(video_id, limit=10)
    except Exception:
        return None

    recent = _RECENT[chat_id]
    for song in recommendations:
        recommendation_id = str(song.get("video_id") or "")
        if not recommendation_id or recommendation_id in recent:
            continue
        if recommendation_id == str(getattr(finished, "id", "")):
            continue

        track = None
        # Ask the existing YouTube adapter for full metadata and a thumbnail.
        try:
            track = await yt.search(
                f"https://www.youtube.com/watch?v={recommendation_id}",
                0,
                video=False,
            )
        except Exception:
            pass

        # The recommendation itself is enough to queue a playable item if the
        # metadata adapter is temporarily unavailable.
        if not track:
            track = Track(
                id=recommendation_id,
                title=(song.get("title") or "Recommended song")[:30],
                channel_name=song.get("artist") or "Unknown Artist",
                url=f"https://www.youtube.com/watch?v={recommendation_id}",
                video=False,
            )

        track.user = "ᴀᴜᴛᴏᴘʟᴀʏ"
        track.user_id = 0
        recent.append(recommendation_id)
        return track

    return None


@app.on_callback_query(filters.regex(r"^autoplay toggle ") & ~app.bl_users)
@lang.language()
@can_manage_vc
async def autoplay_toggle(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[2])
    enabled = await toggle_autoplay(chat_id)
    await query.answer(
        f"Aᴜᴛᴏᴘʟᴀʏ {'enabled 🟢' if enabled else 'disabled 🔴'}",
        show_alert=True,
    )
    try:
        await query.edit_message_reply_markup(
            reply_markup=buttons.controls(chat_id)
        )
    except Exception:
        pass


@app.on_callback_query(filters.regex(r"^thumbnail toggle ") & ~app.bl_users)
@lang.language()
@can_manage_vc
async def thumbnail_toggle(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[2])
    enabled = await toggle_thumbnail(chat_id)
    await query.answer(
        f"Tʜᴜᴍʙɴᴀɪʟ {'enabled 🟢' if enabled else 'disabled 🔴'}",
        show_alert=True,
    )
    try:
        await query.edit_message_reply_markup(
            reply_markup=buttons.controls(chat_id)
        )
    except Exception:
        pass
