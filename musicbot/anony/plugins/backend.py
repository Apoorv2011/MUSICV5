from pyrogram import filters, types

from anony import app, config
from backend_prefs import get_primary, set_primary

_OWNER = filters.user(config.OWNER_ID)


@app.on_message(filters.command("yt") & _OWNER)
async def toggle_yt(_, message: types.Message):
    set_primary("arc")
    await message.reply_text("🎵 Backend: **YouTube/Arc** (primary)")


@app.on_message(filters.command("j") & _OWNER)
async def toggle_jio_short(_, message: types.Message):
    set_primary("jio")
    await message.reply_text("🎵 Backend: **JioSaavn** (primary)")


@app.on_message(filters.command("jio") & _OWNER)
async def toggle_jio(_, message: types.Message):
    set_primary("jio")
    await message.reply_text("🎵 Backend: **JioSaavn** (primary)")


@app.on_message(filters.command("auto") & _OWNER)
async def toggle_auto(_, message: types.Message):
    set_primary("auto")
    await message.reply_text("🎵 Backend: **Auto** (smart fallback)")


@app.on_message(filters.command("s") & _OWNER)
async def toggle_shruti(_, message: types.Message):
    set_primary("s")
    await message.reply_text("🎵 Backend: **Shruti API** (primary)")


@app.on_message(filters.command("shruti") & _OWNER)
async def toggle_shruti_full(_, message: types.Message):
    set_primary("shruti")
    await message.reply_text("🎵 Backend: **Shruti API** (primary)")


@app.on_message(filters.command("y") & _OWNER)
async def toggle_youtube_nexgen(_, message: types.Message):
    set_primary("yt")
    await message.reply_text("🎵 Backend: **YouTube/Arc (NexGen)** (primary)")


@app.on_message(filters.command("n") & _OWNER)
async def toggle_nubcoders(_, message: types.Message):
    set_primary("nub")
    await message.reply_text("🎵 Backend: **NubCoders** (primary)")


@app.on_message(filters.command("backend") & _OWNER)
async def backend_status(_, message: types.Message):
    current = get_primary()
    labels = {
        "arc": "YouTube/Arc (NexGen)",
        "yt": "YouTube/Arc (NexGen)",
        "jio": "JioSaavn",
        "auto": "Auto (smart fallback)",
        "s": "Shruti API",
        "shruti": "Shruti API",
        "nub": "NubCoders",
        "n": "NubCoders",
    }
    await message.reply_text(f"🎵 Current backend: **{labels.get(current, current)}**")
