# anony/core/calls.py
from typing import Optional

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
from anony.helpers import Media, Track, buttons, utils
from backend_prefs import get_primary


async def _nexgen_get_stream_link(vid_id: str, video: bool = False, timeout: int = 20, poll_interval: int = 3) -> Optional[str]:
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
                            if link.startswith("/"):
                                link = urljoin(base, link)
                            return link
            except Exception as e:
                logger.debug("Error polling NexGen endpoint: %s", e)
            await asyncio.sleep(poll_interval)
    logger.debug("NexGen did not return a link for %s within timeout", vid_id)
    return None


async def _shruti_get_stream_link(vid_id: str, video: bool = False, timeout: int = 20, poll_interval: int = 3) -> Optional[str]:
    """Get streaming link from Shruti API (pass video ID only)."""
    api_url = getattr(config, "SHRUTI_API_URL", None)
    api_key = getattr(config, "SHRUTI_API_KEY", None)

    if not api_url or not api_key:
        logger.debug("Shruti config missing: SHRUTI_API_URL or SHRUTI_API_KEY not set")
        return None

    media_type = "video" if video else "audio"
    endpoint = f"{api_url.rstrip('/')}/download"
    deadline = time.time() + timeout

    timeout_cfg = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
        while time.time() < deadline:
            try:
                vid_only = vid_id
                # ensure we only pass the 11-char id
                try:
                    from anony.core.youtube import extract_video_id as _eid
                    vid_only = _eid(vid_id)
                except Exception:
                    pass

                params = {"url": vid_only, "type": media_type, "api_key": api_key}
                async with session.get(endpoint, params=params) as resp:
                    logger.debug("Shruti GET %s params=%s -> HTTP %s", endpoint, params, resp.status)
                    ctype = resp.headers.get("Content-Type", "")

                    if resp.status == 200 and "application/json" in (ctype or ""):
                        try:
                            data = await resp.json()
                        except Exception as e:
                            logger.debug("Shruti JSON parse error: %s", e)
                            data = None

                        if data:
                            status = data.get("status")
                            link = data.get("link") or data.get("url") or None
                            logger.debug("Shruti JSON status=%s link=%s", status, bool(link))
                            if link:
                                if link.startswith("/"):
                                    link = urljoin(api_url, link)
                                return link

                    if resp.status == 200 and any(x in (ctype or "") for x in ("audio/", "video/", "application/octet-stream")):
                        try:
                            from yarl import URL
                            full = str(URL(endpoint).with_query(params))
                            logger.debug("Shruti direct content available for %s; returning %s", vid_only, full)
                            return full
                        except Exception:
                            from urllib.parse import urlencode
                            return endpoint + "?" + urlencode(params)

                    logger.debug("Shruti not ready for %s (HTTP %s, Content-Type=%s)", vid_only, resp.status, ctype)
            except Exception as e:
                logger.debug("Error polling Shruti endpoint: %s", e)
            await asyncio.sleep(poll_interval)

    logger.debug("Shruti did not return a link for %s within timeout", vid_id)
    return None


async def _nubcoders_get_stream_link(video_id_or_url: str, timeout: int = 15) -> Optional[str]:
    """Use NubCoders /info to obtain a stream_url and return it (no download)."""
    api_url = getattr(config, "NUBCODERS_API_URL", None) or getattr(config, "NUBCODERS_API", None) or None
    token = getattr(config, "NUBCODERS_TOKEN", None)
    # Also allow env fallback if config not populated
    if not api_url:
        import os
        api_url = os.getenv("NUBCODERS_API_URL")
    if not token:
        import os
        token = os.getenv("NUBCODERS_TOKEN")
    if not api_url or not token:
        logger.debug("NubCoders config missing")
        return None
    try:
        from anony.core.youtube import extract_video_id as _eid
        vid = _eid(video_id_or_url)
    except Exception:
        vid = (video_id_or_url or "").strip()
    watch_url = f"https://www.youtube.com/watch?v={vid}"
    endpoint = f"{api_url.rstrip('/')}/info"
    params = {"token": token, "q": watch_url}
    timeout_cfg = aiohttp.ClientTimeout(total=timeout)
    async with aiohttp.ClientSession(timeout=timeout_cfg) as session:
        try:
            async with session.get(endpoint, params=params) as resp:
                logger.debug("NubCoders GET %s params=%s -> HTTP %s", endpoint, params, resp.status)
                if resp.status != 200:
                    txt = await resp.text()
                    logger.debug("NubCoders returned non-200: %s", txt)
                    return None
                try:
                    data = await resp.json()
                except Exception:
                    logger.debug("NubCoders returned non-json")
                    return None
                stream = data.get("stream_url") or data.get("streamUrl") or data.get("url") or data.get("stream")
                if stream and stream.startswith("/"):
                    stream = urljoin(api_url, stream)
                return stream
        except Exception as e:
            logger.debug("NubCoders get stream error: %s", e)
            return None


def _build_user_mention(media) -> str:
    raw_name = getattr(media, "user", "") or ""
    username = getattr(media, "username", None)
    user_id_candidate = (
        getattr(media, "user_id", None)
        or getattr(media, "user_id_int", None)
        or getattr(media, "requested_by_id", None)
        or getattr(media, "requester_id", None)
    )

    if isinstance(raw_name, str) and "<a" in raw_name:
        m = re.search(r'<a\s+[^>]*href=["\']?tg://user\?id=(\d+)["\']?[^>]*\s*>(.*?)</a>', raw_name, re.I)
        if m:
            try:
                uid = int(m.group(1))
                display = html.escape(m.group(2) or "Unknown user")
                return f'<a href="tg://user?id={uid}">{display}</a>'
            except Exception:
                pass
        m2 = re.search(r'<a\s+[^>]*href=["\']?(?:https?://)?t\.me/([^"\' >/]+)["\']?[^>]*\s*>(.*?)</a>', raw_name, re.I)
        if m2:
            uname = m2.group(1)
            display = html.escape(m2.group(2) or f"@{uname}")
            return f'<a href="https://t.me/{html.escape(uname)}">{display}</a>'
        text_only = re.sub(r'<[^>]+>', '', raw_name).strip()
        if text_only:
            return html.escape(text_only)

    if username:
        clean_username = str(username).lstrip("@")
        display = html.escape(str(raw_name) or f"@{clean_username}")
        return f'<a href="https://t.me/{html.escape(clean_username)}">{display}</a>'

    uid = None
    if user_id_candidate is not None:
        try:
            uid = int(user_id_candidate)
        except (TypeError, ValueError):
            uid = None

    if uid:
        display = html.escape(str(raw_name) or "Unknown user")
        return f'<a href="tg://user?id={uid}">{display}</a>'

    return html.escape(str(raw_name) or "Unknown user")


def _fmt_time(seconds: int) -> str:
    try:
        s = int(seconds)
    except Exception:
        return "0:00"
    m, s = divmod(s, 60)
    return f"{m}:{s:02d}"


def _progress_bar(position: int, duration: int, length: int = 12) -> str:
    try:
        pos = max(0, int(position))
        dur = max(1, int(duration))
    except Exception:
        return "▮" + "□" * (length - 1)

    filled = int((pos / dur) * length)
    if filled >= length:
        filled = length

    bar = ""
    for i in range(length):
        if i < filled - 1:
            bar += "█"
        elif i == filled - 1:
            bar += "◉"
        else:
            bar += "▭"
    return bar


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
                media.time = getattr(media, "time", 1) or 1
                await db.add_call(chat_id)

                try:
                    url = media.url or ""
                    title = html.escape(media.title or "Unknown title")
                    duration_seconds = getattr(media, "duration_sec", None)
                    if not duration_seconds:
                        duration_str_raw = getattr(media, "duration", "") or ""
                        try:
                            duration_seconds = utils.to_seconds(duration_str_raw) if duration_str_raw else 0
                        except Exception:
                            duration_seconds = 0
                    duration_text = _fmt_time(duration_seconds)

                    user_mention = _build_user_mention(media)
                    escaped_url = html.escape(url, quote=True)

                    # Build caption WITHOUT the time_line (progress). Controls area handles progress.
                    text = (
                        '<b>❖ 𝛅ᴛᴧʀᴛєᴅ 𝛅ᴛʀєᴧϻɪηɢ</b>\n\n'
                        f'◉ <b>❍ тɪᴛʟє :</b> <a href="{escaped_url}">{title}</a>\n'
                        f'◉ <b>❍ ᴅᴜʀᴧᴛɪση:</b> {duration_text}\n'
                        f'◉ <b>ʙʏ:</b> {user_mention}\n\n'
                        f'✦ <b>❖ ᴍᴀᴅᴇ ʙʏ...</b> <a href="https://t.me/IsolatedBytes">@IsolatedBytes</a>'
                    )
                except Exception as e:
                    logger.warning("Language format error for play_media: %s — template fallback", e)
                    title_fb = html.escape(getattr(media, "title", "") or "Unknown title")
                    dur_fb_raw = getattr(media, "duration", "") or ""
                    dur_fb = _fmt_time(utils.to_seconds(dur_fb_raw) if dur_fb_raw else 0)
                    user_fb = html.escape(getattr(media, "user", "") or "Unknown user")
                    url_fb = html.escape(getattr(media, "url", "") or "")
                    text = f"{title_fb} — {dur_fb}\nRequested by: {user_fb}\n{url_fb}"

                keyboard = buttons.controls(chat_id)
                _reveal = getattr(config, "THUMBNAIL_REVEAL", False)

                try:
                    if _thumb:
                        try:
                            await message.edit_media(
                                media=InputMediaPhoto(
                                    media=_thumb,
                                    has_spoiler=_reveal,
                                ),
                                reply_markup=keyboard,
                            )
                        except (MessageIdInvalid, ChatSendMediaForbidden, ChatSendPhotosForbidden) as e:
                            logger.debug("edit_media failed or not allowed: %s", e)
                            raise

                        try:
                            await app.edit_message_caption(
                                chat_id=chat_id,
                                message_id=message.id,
                                caption=text,
                                parse_mode=ParseMode.HTML,
                                reply_markup=keyboard,
                            )
                        except Exception as e:
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
                        await message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
                except (ChatSendMediaForbidden, ChatSendPhotosForbidden, MessageIdInvalid):
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

        if not media.file_path:
            try:
                # Get current mode to decide which provider to use
                mode = get_primary()

                # Try streaming link based on current mode
                stream_link = None
                if mode in ("s", "shruti"):
                    stream_link = await _shruti_get_stream_link(media.id, video=getattr(media, "video", False), timeout=15, poll_interval=3)
                    if stream_link:
                        media.file_path = stream_link
                        logger.info("Streaming via Shruti link for %s", media.id)
                    else:
                        logger.warning("Shruti streaming failed, falling back to download for %s", media.id)
                elif mode in ("n", "nub", "nubcoders"):
                    stream_link = await _nubcoders_get_stream_link(media.id, timeout=15)
                    if stream_link:
                        media.file_path = stream_link
                        logger.info("Streaming via NubCoders stream URL for %s", media.id)
                    else:
                        logger.warning("NubCoders stream lookup failed, falling back to download for %s", media.id)
                else:
                    # Default: try NexGen first
                    stream_link = await _nexgen_get_stream_link(media.id, video=getattr(media, "video", False), timeout=15, poll_interval=3)
                    if stream_link:
                        media.file_path = stream_link
                        logger.info("Streaming via NexGen link for %s", media.id)
                    else:
                        logger.warning("NexGen streaming failed, falling back to download for %s", media.id)

                # Fallback to download if streaming failed
                if not media.file_path:
                    media.file_path = await yt.download(media.id, video=getattr(media, "video", False), title=getattr(media, "title", None))

            except Exception as e:
                logger.warning("Error getting stream link, falling back to download: %s", e)
                media.file_path = await yt.download(media.id, video=getattr(media, "video", False), title=getattr(media, "title", None))

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
