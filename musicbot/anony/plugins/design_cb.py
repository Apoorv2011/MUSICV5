
from pyrogram import enums, filters, types

from anony import app, db, lang
from anony.helpers import admin_check, buttons
from player_style import get_style, set_style


_DESIGNS = [
    (1, "🎴 Design 1 – Normal"),
    (2, "🎬 Design 2 – cinematic"),
    (3, "🎨 Design 3 – Classic"),
    (4, "⬜ Design 4 – Default"),
]


@app.on_callback_query(filters.regex(r"^design") & ~app.bl_users)
@lang.language()
@admin_check
async def _design_cb(_, query: types.CallbackQuery):
    args = query.data.split()
    action = args[1]

    if action == "pick":
        chat_id = int(args[2])
        current = get_style(chat_id)
        rows = [
            [
                buttons.ikb(
                    text=f"{'✅ ' if current == n else ''}{label}",
                    callback_data=f"design set {chat_id} {n}",
                    style=buttons._button_style(index),
                )
            ]
            for index, (n, label) in enumerate(_DESIGNS)
        ]
        rows.append(
            [
                buttons.ikb(
                    text="↩ Back",
                    callback_data=f"design back {chat_id}",
                    style=enums.ButtonStyle.PRIMARY,
                )
            ]
        )
        await query.answer()
        try:
            await query.edit_message_reply_markup(
                reply_markup=types.InlineKeyboardMarkup(rows)
            )
        except Exception:
            pass

    elif action == "set":
        chat_id, style = int(args[2]), int(args[3])
        set_style(chat_id, style)
        label = next((l for n, l in _DESIGNS if n == style), f"Design {style}")
        await query.answer(f"{label} selected!", show_alert=True)
        try:
            await query.edit_message_reply_markup(
                reply_markup=await _settings_markup(query, chat_id)
            )
        except Exception:
            pass

    elif action == "back":
        chat_id = int(args[2])
        await query.answer()
        try:
            await query.edit_message_reply_markup(
                reply_markup=await _settings_markup(query, chat_id)
            )
        except Exception:
            pass


async def _settings_markup(query: types.CallbackQuery, chat_id: int):
    return buttons.settings_markup(
        query.lang,
        await db.get_play_mode(chat_id),
        await db.get_cmd_delete(chat_id),
        await db.get_lang(chat_id),
        chat_id,
        await db.get_biolink(chat_id),
    )
