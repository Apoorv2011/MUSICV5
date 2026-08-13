from ntgcalls import (ConnectionNotFound, TelegramServerError,
                      RTMPStreamingUnsupported, ConnectionError)
from pyrogram.errors import (ChatSendMediaForbidden, ChatSendPhotosForbidden,
                             MessageIdInvalid)
from pyrogram.types import InputMediaPhoto, Message
from pyrogram.enums import ParseMode
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

import aiohttp
import asyncio
import time
from urllib.parse import urljoin
import html
import re

from anony import (app, config, db, lang, logger,
                   queue, thumb, userbot, yt)
from anony.helpers import Media, Track, buttons


async def _nexgen_get_stream_link(vid_id: str, video: bool = False, timeout: int = 20, poll_interval: int = 3) -> str | None:
    """
    Poll NexGenBots API for a stream/download link without saving locally.
    Returns the public link (http(s)...) if provider returns status == 'done' and a 'link' field.
    """
    api_key = getattr(config, "API_KEY", None)
    if not api_key:
        return None

    base = config.VIDEO_API_URL if video else config.API_URL
    if not base:
        return None

    endpoint = f"{base.rstrip('/')}/{'video' if video else 'song'}/{vid_id}?api={api_key}"
    deadline = time.time() + timeout

    timeout_cfg = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
        while time.time() < deadline:
            try:
                async with session.get(endpoint) as resp:
                    if resp.status != 200:
                        logger.debug("NexGen returned HTTP %s for %s", resp.status, endpoint)
                    else:
                        data = await resp.json()
                        status = data.get("status")
                        link = data.get("link")
                        logger.debug("NexGen status=%s for vid=%s", status, vid_id)
                        if status == "done" and link:
                            # ensure absolute URL
                            if link.startswith("/"):
                                link = urljoin(base, link)
                            return link
            except Exception as e:
                logger.debug("Error polling NexGen endpoint: %s", e)
            await asyncio.sleep(poll_interval)
    logger.debug("NexGen did not return a link for %s within timeout", vid_id)
    return None


def _build_user_mention(media) -> str:
    """
    Build a safe HTML mention for the requester.
    - If media.user contains an <a href="tg://user?id=...">Name</a> or
      <a href="https://t.me/username">Name</a>, extract and reuse the link safely.
    - Otherwise prefer an explicit username attribute (media.username), then numeric id attributes.
    - Fall back to escaped plain name if nothing linkable is found.
    """
    raw_name = getattr(media, "user", "") or ""
    username = getattr(media, "username", None)  # explicit username if available
    # common id fields - adapt if your Track uses different names
    user_id_candidate = (
        getattr(media, "user_id", None)
        or getattr(media, "user_id_int", None)
        or getattr(media, "requested_by_id", None)
        or getattr(media, "requester_id", None)
    )

    # If raw_name contains an anchor, try to salvage it (common when upstream already built mention)
    if isinstance(raw_name, str) and "<a" in raw_name:
        # Try tg://user?id= numeric anchor
        m = re.search(r'<a\s+[^>]*href=["\']?tg://user\?id=(\d+)["\']?[^>]*\s*>(.*?)</a>', raw_name, re.I)
        if m:
            try:
                uid = int(m.group(1))
                display = html.escape(m.group(2) or "Unknown user")
                return f'<a href="tg://user?id={uid}">{display}</a>'
            except Exception:
                pass

        # Try t.me anchor
        m2 = re.search(r'<a\s+[^>]*href=["\']?(?:https?://)?t\.me/([^"\' >/]+)["\']?[^>]*\s*>(.*?)</a>', raw_name, re.I)
        if m2:
            uname = m2.group(1)
            display = html.escape(m2.group(2) or f"@{uname}")
            return f'<a href="https://t.me/{html.escape(uname)}">{display}</a>'

        # Fallback: strip tags and use visible text
        text_only = re.sub(r'<[^>]+>', '', raw_name).strip()
        if text_only:
            return html.escape(text_only)

    # If explicit username provided, link to t.me/<username>
    if username:
        clean_username = str(username).lstrip("@")
        display = html.escape(str(raw_name) or f"@{clean_username}")
        return f'<a href="https://t.me/{html.escape(clean_username)}">{display}</a>'

    # Numeric id candidates
    uid = None
    if user_id_candidate is not None:
        try:
            uid = int(user_id_candidate)
        except (TypeError, ValueError):
            uid = None

    if uid:
        display = html.escape(str(raw_name) or "Unknown user")
        return f'<a href="tg://user?id={uid}">{display}</a>'

    # fallback to escaped plain name
    return html.escape(str(raw_name) or "Unknown user")


class TgCall(PyTgCalls):
    def __init__(self):
        self.clients = []

    async def pause(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=True)
        return await client.pause(chat_id)

    async def resume(self, chat_id: int) -> bool:
        client = await db.get_assistant(chat_id)
        await db.playing(chat_id, paused=False)
        return await client.resume(chat_id)

    async def stop(self, chat_id: int) -> None:
        client = await db.get_assistant(chat_id)
        queue.clear(chat_id)
        await db.remove_call(chat_id)
        await db.set_loop(chat_id, 0)

        try:
            await client.leave_call(chat_id, close=False)
        except Exception:
            pass

    async def play_media(
        self,
        chat_id: int,
        message: Message,
        media: Media | Track,
        seek_time: int = 0,
    ) -> None:
        client = await db.get_assistant(chat_id)
        _lang = await lang.get_lang(chat_id)
        _thumb = (
            await thumb.get(media, chat_id)
            if isinstance(media, Track)
            else config.DEFAULT_THUMB
        ) if getattr(config, "THUMB_GEN", False) else None

        if not media.file_path:
            await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            return await self.play_next(chat_id)

        stream = types.MediaStream(
            media_path=media.file_path,
            audio_parameters=types.AudioQuality.HIGH,
            video_parameters=types.VideoQuality.HD_720p,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=(
                types.MediaStream.Flags.AUTO_DETECT
                if getattr(media, "video", False)
                else types.MediaStream.Flags.IGNORE
            ),
            ffmpeg_parameters=f"-ss {seek_time}" if seek_time > 1 else None,
        )

        try:
            await client.play(
                chat_id=chat_id,
                stream=stream,
                config=types.GroupCallConfig(auto_start=False),
            )

            if not seek_time:
                media.time = 1
                await db.add_call(chat_id)

                # Build safe HTML caption (escape user-supplied text)
                try:
                    url = media.url or ""
                    title = html.escape(media.title or "Unknown title")
                    duration = html.escape(media.duration or "Unknown duration")

                    user_mention = _build_user_mention(media)

                    escaped_url = html.escape(url, quote=True)

                    # HTML template
                    text = (
                        "<b>✦ STARTED STREAMING</b>\n\n"
                        f"◉ <b>TITLE :</b> <a href=\"{escaped_url}\">{title}</a>\n"
                        f"◉ <b>DURATION :</b> {duration}\n"
                        f"◉ <b>BY :</b> {user_mention}\n\n"
                        f"✦ <b>MADE BY…</b> <a href=\"https://t.me/IsolatedBytes\">@IsolatedBytes</a>"
                    )
                except Exception as e:
                    logger.warning("Language format error for play_media: %s — template=%r", e, _lang.get("play_media"))
                    # fallback plain text (still escaped)
                    title = html.escape(getattr(media, "title", "") or "Unknown title")
                    duration = html.escape(getattr(media, "duration", "") or "Unknown duration")
                    user_txt = html.escape(getattr(media, "user", "") or "Unknown user")
                    url_escaped = html.escape(getattr(media, "url", "") or "")
                    text = f"{title} — {duration}\nRequested by: {user_txt}\n{url_escaped}"

                keyboard = buttons.controls(chat_id)
                _reveal = getattr(config, "THUMBNAIL_REVEAL", False)

                try:
                    if _thumb:
                        # Two-step approach ensures caption is parsed correctly across pyrogram versions:
                        # 1) edit_media to set the new photo (no parse_mode here)
                        # 2) edit_message_caption to set caption with ParseMode.HTML
                        try:
                            await message.edit_media(
                                media=InputMediaPhoto(
                                    media=_thumb,
                                    has_spoiler=_reveal,
                                ),
                                reply_markup=keyboard,
                            )
                        except (MessageIdInvalid, ChatSendMediaForbidden, ChatSendPhotosForbidden) as e:
                            # If editing media fails, fall back to sending a new photo below
                            logger.debug("edit_media failed or not allowed: %s", e)
                            raise

                        # Now explicitly set caption using edit_message_caption which accepts parse_mode reliably
                        try:
                            await app.edit_message_caption(
                                chat_id=chat_id,
                                message_id=message.id,
                                caption=text,
                                parse_mode=ParseMode.HTML,
                                reply_markup=keyboard,
                            )
                        except Exception as e:
                            # If caption edit fails for any reason, fallback to sending a new photo message
                            logger.debug("edit_message_caption failed: %s", e)
                            sent = await app.send_photo(
                                chat_id=chat_id,
                                photo=_thumb,
                                caption=text,
                                reply_markup=keyboard,
                                has_spoiler=_reveal,
                                parse_mode=ParseMode.HTML,
                            )
                            media.message_id = sent.id
                    else:
                        # No thumbnail: edit text directly with ParseMode enum
                        await message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
                except (ChatSendMediaForbidden, ChatSendPhotosForbidden, MessageIdInvalid):
                    # Fallback: send a fresh message (covers cases where edits are forbidden)
                    if _thumb:
                        sent = await app.send_photo(
                            chat_id=chat_id,
                            photo=_thumb,
                            caption=text,
                            reply_markup=keyboard,
                            has_spoiler=_reveal,
                            parse_mode=ParseMode.HTML,
                        )
                    else:
                        sent = await app.send_message(
                            chat_id=chat_id,
                            text=text,
                            reply_markup=keyboard,
                            parse_mode=ParseMode.HTML,
                        )
                    media.message_id = sent.id

        except FileNotFoundError:
            await message.edit_text(_lang["error_no_file"].format(config.SUPPORT_CHAT))
            await self.play_next(chat_id)
        except exceptions.NoActiveGroupCall:
            await self.stop(chat_id)
            await message.edit_text(_lang["error_no_call"])
        except exceptions.NoAudioSourceFound:
            await message.edit_text(_lang["error_no_audio"])
            await self.play_next(chat_id)
        except (ConnectionError, ConnectionNotFound, TelegramServerError):
            await self.stop(chat_id)
            await message.edit_text(_lang["error_tg_server"])
        except RTMPStreamingUnsupported:
            await self.stop(chat_id)
            await message.edit_text(_lang["error_rtmp"])

    async def replay(self, chat_id: int) -> None:
        if not await db.get_call(chat_id):
            return

        media = queue.get_current(chat_id)
        _lang = await lang.get_lang(chat_id)
        msg = await app.send_message(chat_id=chat_id, text=_lang["play_again"])
        media.message_id = msg.id
        await self.play_media(chat_id, msg, media)

    async def play_next(self, chat_id: int) -> None:
        if loop := await db.get_loop(chat_id):
            await db.set_loop(chat_id, loop - 1)
            return await self.replay(chat_id)

        media = queue.get_next(chat_id)
        try:
            if media.message_id:
                await app.delete_messages(
                    chat_id=chat_id,
                    message_ids=media.message_id,
                    revoke=True,
                )
                media.message_id = 0
        except Exception:
            pass

        if not media:
            return await self.stop(chat_id)

        _lang = await lang.get_lang(chat_id)
        msg = await app.send_message(chat_id=chat_id, text=_lang["play_next"])

        # Attempt NexGenBots streaming link first (no local download)
        if not media.file_path:
            try:
                stream_link = await _nexgen_get_stream_link(media.id, video=getattr(media, "video", False), timeout=15, poll_interval=3)
                if stream_link:
                    media.file_path = stream_link
                    logger.info("Streaming via NexGen link for %s", media.id)
                else:
                    media.file_path = await yt.download(media.id, video=getattr(media, "video", False))
            except Exception as e:
                logger.warning("Error getting NexGen stream link, falling back to download: %s", e)
                media.file_path = await yt.download(media.id, video=getattr(media, "video", False))

            if not media.file_path:
                await self.play_next(chat_id)
                return await msg.edit_text(
                    _lang["error_no_file"].format(config.SUPPORT_CHAT)
                )

        media.message_id = msg.id
        await self.play_media(chat_id, msg, media)

    async def ping(self) -> float:
        pings = [client.ping for client in self.clients]
        return round(sum(pings) / len(pings), 2)

    async def decorators(self, client: PyTgCalls) -> None:
        @client.on_update()
        async def update_handler(_, update: types.Update) -> None:
            if isinstance(update, types.StreamEnded):
                if update.stream_type == types.StreamEnded.Type.AUDIO:
                    await self.play_next(update.chat_id)
            elif isinstance(update, types.ChatUpdate):
                if update.status in [
                    types.ChatUpdate.Status.KICKED,
                    types.ChatUpdate.Status.LEFT_GROUP,
                    types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                ]:
                    await self.stop(update.chat_id)

    async def boot(self) -> None:
        PyTgCallsSession.notice_displayed = True
        for ub in userbot.clients:
            client = PyTgCalls(ub, cache_duration=100)
            await client.start()
            self.clients.append(client)
            await self.decorators(client)
        logger.info("PyTgCalls client(s) started.")
