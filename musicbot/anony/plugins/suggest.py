# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.

import asyncio
import html
import re

from pyrogram import filters, types

from anony import anon, app, db, lang, queue, yt
from anony.helpers import Track, buttons, can_manage_vc


_VIDEO_ID = re.compile(r"(?<![A-Za-z0-9_-])([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])")
_YT_MUSIC = None


def _get_video_id(media) -> str | None:
    for value in (getattr(media, "id", None), getattr(media, "url", None)):
        if not value:
            continue
        match = _VIDEO_ID.search(str(value))
        if match:
            return match.group(1)
    return None


async def _recommend(video_id: str) -> list[dict]:
    global _YT_MUSIC
    if _YT_MUSIC is None:
        from ytmusicapi import YTMusic

        _YT_MUSIC = YTMusic()

    def fetch():
        result = _YT_MUSIC.get_watch_playlist(videoId=video_id)
        songs = []
        seen = {video_id}
        for item in result.get("tracks", []):
            item_id = item.get("videoId")
            if not item_id or item_id in seen:
                continue
            seen.add(item_id)
            artist = (
                item.get("artists", [{}])[0].get("name", "Unknown Artist")
                if item.get("artists")
                else "Unknown Artist"
            )
            label = f"{item.get('title', 'Unknown')} — {artist}"
            songs.append(
                {
                    "video_id": item_id,
                    "label": label[:58],
                    "title": item.get("title", "Unknown"),
                    "artist": artist,
                }
            )
            if len(songs) == 10:
                break
        return songs

    return await asyncio.to_thread(fetch)


async def _resolve_video_id(media) -> str | None:
    video_id = _get_video_id(media)
    if video_id:
        return video_id

    title = getattr(media, "title", None)
    artist = getattr(media, "channel_name", None)
    if not title:
        return None

    global _YT_MUSIC
    if _YT_MUSIC is None:
        from ytmusicapi import YTMusic

        _YT_MUSIC = YTMusic()

    def search():
        results = _YT_MUSIC.search(
            f"{title} {artist or ''}".strip(),
            filter="songs",
            limit=1,
        )
        return results[0].get("videoId") if results else None

    try:
        return await asyncio.to_thread(search)
    except Exception:
        return None


def _song_from_saved(song: dict, user: str, user_id: int) -> Track:
    return Track(
        id=song.get("id", ""),
        title=song.get("title", "Unknown")[:25],
        channel_name=song.get("artist", ""),
        duration=song.get("duration", "00:00"),
        duration_sec=song.get("duration_sec", 0),
        url=song.get("url", ""),
        thumbnail=song.get("thumbnail", ""),
        user=user,
        user_id=user_id,
    )


async def _play_track_now(chat_id: int, track: Track) -> str | None:
    if not await db.get_call(chat_id):
        return "Start a song in the voice chat first, then choose a recommendation."

    current = queue.get_current(chat_id)
    if not current:
        return "Nothing is currently playing."

    if not track.file_path:
        track.file_path = await yt.download(track.id, video=track.video)
    if not track.file_path:
        return "I couldn't download that song. Please try another recommendation."

    try:
        if current.message_id:
            await app.delete_messages(
                chat_id=chat_id, message_ids=current.message_id, revoke=True
            )
    except Exception:
        pass

    queue.force_add(chat_id, track)
    _lang = await lang.get_lang(chat_id)
    message = await app.send_message(chat_id=chat_id, text=_lang["play_next"])
    track.message_id = message.id
    await anon.play_media(chat_id, message, track)
    return None


@app.on_callback_query(filters.regex(r"^suggest ") & ~app.bl_users)
async def suggest_list(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    current = queue.get_current(chat_id)
    if not current:
        return await query.answer("Nothing is currently playing.", show_alert=True)

    video_id = await _resolve_video_id(current)
    if not video_id:
        return await query.answer(
            "Suggestions are unavailable for this track.", show_alert=True
        )

    try:
        songs = await _recommend(video_id)
    except Exception:
        return await query.answer(
            "YouTube Music recommendations are unavailable right now.",
            show_alert=True,
        )
    if not songs:
        return await query.answer("No recommendations found.", show_alert=True)

    text = (
        "🎵 <b>ʏᴏᴜ ᴍᴀʏ ʟɪᴋᴇ ᴛʜᴇsᴇ ᴛʀᴀᴄᴋs</b>\n\n"
        "Choose a song below and I'll play it in this voice chat."
    )
    await query.answer()
    await query.message.reply_text(
        text,
        reply_markup=buttons.suggestions_markup(chat_id, songs),
    )


@app.on_callback_query(filters.regex(r"^suggest_back ") & ~app.bl_users)
async def suggest_back(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    await query.answer()
    await query.message.delete()


@app.on_callback_query(filters.regex(r"^suggest_play ") & ~app.bl_users)
@can_manage_vc
async def suggest_play(_, query: types.CallbackQuery):
    _, chat_id_text, video_id = query.data.split()
    chat_id = int(chat_id_text)

    track = await yt.search_youtube(
        f"https://www.youtube.com/watch?v={video_id}",
        query.message.id,
    )
    if not track:
        return await query.answer("Song metadata could not be loaded.", show_alert=True)
    track.user = query.from_user.mention
    track.user_id = query.from_user.id
    error = await _play_track_now(chat_id, track)
    if error:
        return await query.answer(error, show_alert=True)
    await query.answer("Playing selected song…")
    await query.message.delete()


@app.on_callback_query(filters.regex(r"^fav ") & ~app.bl_users)
async def add_current_favorite(_, query: types.CallbackQuery):
    chat_id = int(query.data.split()[1])
    current = queue.get_current(chat_id)
    if not current or not getattr(current, "title", None):
        return await query.answer("Nothing can be added to favorites.", show_alert=True)

    song = {
        "id": current.id,
        "title": current.title,
        "artist": current.channel_name or "",
        "duration": current.duration,
        "duration_sec": current.duration_sec,
        "url": current.url or "",
        "thumbnail": current.thumbnail or "",
    }
    added = await db.add_favorite(query.from_user.id, song)
    await query.answer("💗 Added to your favorites." if added else "Already in your favorites.")


@app.on_message(filters.command("myfav") & ~app.bl_users)
async def my_favorites(_, message: types.Message):
    songs = await db.get_favorites(message.from_user.id)
    if not songs:
        return await message.reply_text(
            "💗 <b>Your favorites are empty.</b>\nTap FAV while a song is playing.",
            quote=True,
        )

    lines = "\n".join(
        f"<b>{index + 1}.</b> {html.escape(song.get('title', 'Unknown'))}"
        for index, song in enumerate(songs)
    )
    await message.reply_text(
        f"💗 <b>{html.escape(message.from_user.first_name)}'s favorite songs</b>\n\n{lines}\n\n"
        "Tap a song below to play it in the current voice chat.",
        reply_markup=buttons.favorites_markup(songs),
        quote=True,
    )


@app.on_callback_query(filters.regex(r"^favplay ") & ~app.bl_users)
@can_manage_vc
async def play_favorite(_, query: types.CallbackQuery):
    index = int(query.data.split()[1])
    songs = await db.get_favorites(query.from_user.id)
    if index < 0 or index >= len(songs):
        return await query.answer("That favorite no longer exists.", show_alert=True)

    song = songs[index]
    track = _song_from_saved(
        song,
        query.from_user.mention,
        query.from_user.id,
    )
    error = await _play_track_now(query.message.chat.id, track)
    if error:
        return await query.answer(error, show_alert=True)
    await query.answer("Playing favorite…")
    await query.message.delete()