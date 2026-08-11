# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.

from html import escape
from io import BytesIO
import json
import aiohttp
import urllib.parse
from PIL import Image
from pyrogram import filters, types
from anony import app

# Image generation API
_IMAGE_API = "https://v1-img-gen.prathmeshapis.workers.dev/generate"
_MAX_RESPONSE_BYTES = 15 * 1024 * 1024

# Number info API
_NUM_API_URL = "https://apurv-num-info-api.prathmeshapis.workers.dev/"

# Claude AI API
_CLAUDE_API_URL = "http://de3.bot-hosting.net:21007/kilwa-claude"


async def _fetch_generated_image(prompt: str) -> BytesIO:
    """Fetch an image from the generator and return a Telegram-ready PNG."""
    timeout = aiohttp.ClientTimeout(total=90)
    headers = {"User-Agent": "Mozilla/5.0"}

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(_IMAGE_API, params={"prompt": prompt}) as response:
            if response.status != 200:
                raise RuntimeError(f"image API returned HTTP {response.status}")

            content_length = response.content_length
            if content_length and content_length > _MAX_RESPONSE_BYTES:
                raise RuntimeError("image response is too large")

            image_data = await response.read()

    if not image_data or len(image_data) > _MAX_RESPONSE_BYTES:
        raise RuntimeError("image response is empty or too large")

    # The endpoint returns WebP. Convert it to PNG for a reliable Telegram
    # photo upload while keeping the image entirely in memory.
    with Image.open(BytesIO(image_data)) as image:
        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA")

        output = BytesIO()
        image.save(output, format="PNG", optimize=True)
        output.seek(0)
        output.name = "generated.png"
        return output


@app.on_message(filters.command("img") & ~app.bl_users)
async def image_generation(_, m: types.Message) -> None:
    """Generate an image from a text prompt."""
    if len(m.command) < 2:
        await m.reply_text(
            "🎨 <b>Usage:</b> <code>/img your image prompt</code>",
            quote=True,
        )
        return

    prompt = " ".join(m.command[1:]).strip()
    status = await m.reply_text(
        "🎨 <b>Generating your image...</b>",
        quote=True,
    )

    try:
        image = await _fetch_generated_image(prompt)
        caption = f"🎨 <b>Prompt:</b> {escape(prompt)}"
        await m.reply_photo(photo=image, caption=caption, quote=True)
        await status.delete()
    except Exception as e:
        try:
            await status.edit_text(
                f"❌ <b>Image generation failed.</b>\n"
                f"Error: {str(e)[:100]}\n"
                "Please try a different prompt in a moment.",
            )
        except Exception:
            pass


@app.on_message(filters.command("num") & ~app.bl_users)
async def number_search(_, m: types.Message) -> None:
    """Search for mobile number information."""
    if len(m.command) < 2:
        await m.reply_text(
            "🔍 <b>Usage:</b> <code>/num mobile_number</code>\n"
            "Example: <code>/num 9876543210</code>",
            quote=True,
        )
        return

    mobile_number = m.command[1].strip()

    # Basic validation
    if not mobile_number.isdigit() or len(mobile_number) < 10:
        await m.reply_text(
            "❌ <b>Invalid mobile number.</b>\n"
            "Please provide a valid 10-digit number.",
            quote=True,
        )
        return

    status = await m.reply_text(
        f"🔍 <b>Searching for {mobile_number}...</b>",
        quote=True,
    )

    try:
        # Call the API
        full_url = f"{_NUM_API_URL}?mobile={mobile_number}"

        async with aiohttp.ClientSession() as session:
            async with session.get(full_url, timeout=30) as response:
                if response.status != 200:
                    await status.edit_text(
                        f"❌ <b>API Error.</b>\n"
                        f"Status: {response.status}"
                    )
                    return

                response_text = await response.text()

        # Parse JSON
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            await status.edit_text("❌ <b>Invalid response from API.</b>")
            return

        # Extract only the 'result' field
        result = data.get("result")

        if result is None:
            await status.edit_text(f"❌ <b>No result found for {mobile_number}</b>")
            return

        found = result.get("found", 0)
        data_list = result.get("data", [])

        if found == 0 or not data_list:
            await status.edit_text(f"📱 <b>No information found for {mobile_number}</b>")
            return

        # Format the result
        formatted_result = format_number_result(result, mobile_number)

        # Send the formatted result
        await status.edit_text(formatted_result)

    except Exception as e:
        await status.edit_text(
            f"❌ <b>An error occurred.</b>\n"
            f"Error: {str(e)[:100]}"
        )


@app.on_message(filters.command("ai") & ~app.bl_users)
async def claude_ai(_, m: types.Message) -> None:
    """Chat with Claude AI."""
    if len(m.command) < 2:
        await m.reply_text(
            "🤖 <b>Usage:</b> <code>/ai your question here</code>\n"
            "Example: <code>/ai What is the meaning of life?</code>",
            quote=True,
        )
        return

    query = " ".join(m.command[1:]).strip()

    status = await m.reply_text(
        "🤖 <b>Thinking...</b>",
        quote=True,
    )

    try:
        # URL encode the query
        encoded_query = urllib.parse.quote(query)
        full_url = f"{_CLAUDE_API_URL}?text={encoded_query}"

        async with aiohttp.ClientSession() as session:
            async with session.get(full_url, timeout=60) as response:
                if response.status != 200:
                    await status.edit_text(
                        f"❌ <b>API Error.</b>\n"
                        f"Status: {response.status}"
                    )
                    return

                response_text = await response.text()

        # Try to parse JSON response
        try:
            data = json.loads(response_text)

            # Extract only the reply field
            reply = data.get("reply", "")

            if not reply:
                await status.edit_text("❌ <b>No response received from AI.</b>")
                return

            # Format the response - ONLY THE REPLY, NO MODEL INFO
            formatted_response = f"🤖 <b>Response:</b>\n\n{escape(reply)}"

            # Split long messages if needed (Telegram has 4096 char limit)
            if len(formatted_response) > 4096:
                # Send in parts
                await status.edit_text(formatted_response[:4096])
                remaining = formatted_response[4096:]
                while remaining:
                    await m.reply_text(remaining[:4096], quote=True)
                    remaining = remaining[4096:]
            else:
                await status.edit_text(formatted_response)

        except json.JSONDecodeError:
            # If not JSON, try to extract just the reply from plain text
            if "reply" in response_text:
                try:
                    start_idx = response_text.find('"reply":') + 9
                    end_idx = response_text.find('"', start_idx)
                    if start_idx > 8 and end_idx > start_idx:
                        reply = response_text[start_idx:end_idx]
                        await status.edit_text(f"🤖 <b>Response:</b>\n\n{escape(reply)}")
                        return
                except:
                    pass

            # If it's plain text response
            if len(response_text) > 4000:
                await status.edit_text(response_text[:4000] + "...\n\n<i>(Response truncated)</i>")
            else:
                await status.edit_text(f"🤖 <b>Response:</b>\n\n{escape(response_text)}")

    except Exception as e:
        await status.edit_text(
            f"❌ <b>An error occurred.</b>\n"
            f"Error: {str(e)[:100]}"
        )


def format_number_result(result, mobile_number):
    """Format the result data for display."""
    found = result.get("found", 0)
    data_list = result.get("data", [])

    if found == 0 or not data_list:
        return f"📱 <b>No information found for {mobile_number}</b>"

    first_entry = data_list[0]

    response = f"📱 <b>Mobile Number:</b> <code>{mobile_number}</code>\n"
    response += f"📊 <b>Records Found:</b> {found}\n\n"

    if first_entry.get("name"):
        response += f"👤 <b>Name:</b> {escape(first_entry.get('name'))}\n"

    if first_entry.get("fname"):
        response += f"👨 <b>Father's Name:</b> {escape(first_entry.get('fname'))}\n"

    if first_entry.get("address"):
        response += f"📍 <b>Address:</b> {escape(first_entry.get('address'))}\n"

    if first_entry.get("email"):
        response += f"📧 <b>Email:</b> {escape(first_entry.get('email'))}\n"

    if first_entry.get("id"):
        response += f"🆔 <b>ID:</b> {escape(first_entry.get('id'))}\n"

    if found > 1:
        response += f"\n⚠️ <b>Note:</b> {found} entries found for this number."

    return response