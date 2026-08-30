import html
import re
import time

from pyrogram import Client, filters, types
from pyrogram.types import ChatMemberUpdated, ChatPermissions

from anony import app, db, lang
from anony.helpers import admin_check, utils


_auth_db = db.db.bio_auth
_URL_RE = re.compile(r"(https?://|www\.|t\.me/|\.com|\.net|\.org|\.io)\S*", re.I)


def _mention(user_id: int, name: str) -> str:
    return f'<a href="tg://user?id={user_id}">{html.escape(name)}</a>'


async def _is_authorized(user_id: int) -> bool:
    return bool(await _auth_db.find_one({"_id": user_id}))


async def _authorize(user_id: int, name: str = "") -> None:
    await _auth_db.update_one(
        {"_id": user_id},
        {"$set": {"name": name, "at": time.time()}},
        upsert=True,
    )


async def _unauthorize(user_id: int) -> None:
    await _auth_db.delete_one({"_id": user_id})


@app.on_message(filters.command("biolink") & filters.group & ~app.bl_users)
@lang.language()
@admin_check
async def biolink_toggle(_, message: types.Message):
    args = message.command[1:] if len(message.command) > 1 else []
    value = (args[0] if args else "").lower()

    if value in {"on", "enable", "yes"}:
        enabled = True
    elif value in {"off", "disable", "no"}:
        enabled = False
    elif not value:
        enabled = await db.get_biolink(message.chat.id)
        return await message.reply_text(
            f"Bio link filter: <b>{'Enabled' if enabled else 'Disabled'}</b>\n"
            "Usage: <code>/biolink on</code> or <code>/biolink off</code>"
        )
    else:
        return await message.reply_text(
            "Usage: <code>/biolink on</code> or <code>/biolink off</code>"
        )

    await db.set_biolink(message.chat.id, enabled)
    status = "enabled" if enabled else "disabled"
    await message.reply_text(f"Bio link filter <b>{status}</b> in this chat.")


@app.on_message(filters.command("bauth") & filters.group & ~app.bl_users)
@lang.language()
@admin_check
async def bauth_cmd(_, message: types.Message):
    user = await utils.extract_user(message)
    if not user:
        return await message.reply_text(message.lang["user_not_found"])

    await _authorize(user.id, user.first_name or str(user.id))
    await message.reply_text(
        f'Authorized {_mention(user.id, user.first_name or "user")}.'
    )


@app.on_message(filters.command(["bauthlist", "bauths"]) & filters.group & ~app.bl_users)
@lang.language()
@admin_check
async def bauthlist_cmd(_, message: types.Message):
    docs = [doc async for doc in _auth_db.find()]
    if not docs:
        return await message.reply_text("No authorized users yet.")

    lines = ["<b>Authorized users:</b>", ""]
    for doc in docs:
        user_id = doc["_id"]
        name = doc.get("name") or str(user_id)
        lines.append(f"• <code>{user_id}</code> — {_mention(user_id, name)}")
    await message.reply_text("\n".join(lines))


@app.on_message(filters.command("unbauth") & filters.group & ~app.bl_users)
@lang.language()
@admin_check
async def unbauth_cmd(_, message: types.Message):
    user = await utils.extract_user(message)
    if not user:
        return await message.reply_text(message.lang["user_not_found"])

    await _unauthorize(user.id)
    await message.reply_text(
        f'Removed authorization for {_mention(user.id, user.first_name or "user")}.'
    )


@app.on_chat_member_updated(filters.group & ~filters.bot)
async def bio_filter_member(client: Client, update: ChatMemberUpdated):
    if update.new_chat_member is None:
        return

    user = update.new_chat_member.user
    if user is None or await _is_authorized(user.id):
        return
    if not await db.get_biolink(update.chat.id):
        return
    if user.id in app.sudoers:
        return

    try:
        profile = await client.get_users(user.id)
    except Exception:
        return


    bio = getattr(profile, "bio", "") or ""
    if not bio or not _URL_RE.search(bio):
        return

    try:
        await client.restrict_chat_member(
            update.chat.id,
            profile.id,
            ChatPermissions(can_send_messages=False),
        )
        await app.send_message(
            update.chat.id,
            f"Bio link detected — {_mention(profile.id, profile.first_name or 'user')} "
            "has been restricted.\nAn admin can use <code>/bauth</code> to allow them.",
        )
    except Exception:
        return
