import os
import random
import aiohttp
from PIL import (Image, ImageDraw, ImageEnhance,
                 ImageFilter, ImageFont, ImageOps)

from anony import config, logger
from anony.helpers._dataclass import Track


class Thumbnail:
    def __init__(self):
        self.rect = (914, 514)
        self.fill = (255, 255, 255)
        self.mask = Image.new("L", self.rect, 0)
        self.font1 = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 30)
        self.font2 = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 30)
        self.session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        self.session = aiohttp.ClientSession()

    async def close(self) -> None:
        await self.session.close()

    async def save_thumb(self, output_path: str, url: str) -> str:
        async with self.session.get(url) as resp:
            with open(output_path, "wb") as f:
                f.write(await resp.read())
        return output_path

    # ── router ────────────────────────────────────────────────────────────────

    async def get(self, song: Track, chat_id: int = 0) -> str:
        from player_style import get_style
        style = get_style(chat_id)

        if style == 1:
            return await self.generate_design1(song)
        elif style == 2:
            return await self.generate_design2(song)
        elif style == 3:
            return await self.generate(song)
        else:
            # Design 4 – raw thumbnail from API, no processing
            return song.thumbnail or config.DEFAULT_THUMB

    # ── Design 1 – Alexa Style ────────────────────────────────────────────────

    async def generate_design1(self, song: Track) -> str:
        """Dark glass card: left cover, right info, top-right bot logo."""
        try:
            output = f"cache/thumbs/d1_{song.id}.png"
            if os.path.exists(output):
                return output

            W, H = 950, 500

            font_title  = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 32)
            font_artist = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 24)
            font_time   = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 20)

            # Background
            img = Image.new("RGBA", (W, H), (11, 11, 30, 255))
            draw = ImageDraw.Draw(img)

            # Card
            draw.rounded_rectangle((15, 15, W - 15, H - 15), radius=28, fill=(22, 22, 44))
            draw.rounded_rectangle((15, 15, W - 15, H - 15), radius=28,
                                   outline=(70, 45, 130), width=2)

            # Song cover (left)
            cover_sz = 320
            cx, cy = 45, (H - cover_sz) // 2
            temp = f"cache/thumbs/tmp_d1_{song.id}.jpg"
            if song.thumbnail:
                try:
                    await self.save_thumb(temp, song.thumbnail)
                    cover = Image.open(temp).convert("RGBA").resize(
                        (cover_sz, cover_sz), Image.Resampling.LANCZOS)
                    cmask = Image.new("L", (cover_sz, cover_sz), 0)
                    ImageDraw.Draw(cmask).rounded_rectangle(
                        (0, 0, cover_sz, cover_sz), radius=16, fill=255)
                    cover.putalpha(cmask)
                    img.paste(cover, (cx, cy), cover)
                    try:
                        os.remove(temp)
                    except Exception:
                        pass
                except Exception:
                    pass

            # Info panel
            ix = cx + cover_sz + 40
            iy = cy + 20

            title = (song.title or "Unknown")[:30]
            draw.text((ix, iy), title, font=font_title, fill=(255, 255, 255))

            artist = (song.channel_name or "")[:32]
            draw.text((ix, iy + 52), artist, font=font_artist, fill=(180, 180, 200))

            # Progress bar
            bar_y  = iy + 130
            bar_w  = W - ix - 55
            draw.rounded_rectangle((ix, bar_y, ix + bar_w, bar_y + 6),
                                   radius=3, fill=(55, 35, 85))
            fill_w = max(20, bar_w // 7)
            draw.rounded_rectangle((ix, bar_y, ix + fill_w, bar_y + 6),
                                   radius=3, fill=(130, 80, 220))
            dr = 8
            draw.ellipse((ix + fill_w - dr, bar_y - dr + 3,
                          ix + fill_w + dr, bar_y + dr + 3),
                         fill=(160, 100, 255))

            # Time labels
            draw.text((ix, bar_y + 16), "0:00", font=font_time, fill=(140, 140, 160))
            dur = song.duration or "0:00"
            dbb = font_time.getbbox(dur)
            draw.text((ix + bar_w - (dbb[2] - dbb[0]), bar_y + 16),
                      dur, font=font_time, fill=(140, 140, 160))

            # Bot logo (top right, circular)
            logo_sz = 90
            lx, ly = W - logo_sz - 28, 22
            logo_path = "anony/assets/bot_logo.png"
            if os.path.exists(logo_path):
                try:
                    logo = Image.open(logo_path).convert("RGBA").resize(
                        (logo_sz, logo_sz), Image.Resampling.LANCZOS)
                    lm = Image.new("L", (logo_sz, logo_sz), 0)
                    ImageDraw.Draw(lm).ellipse((0, 0, logo_sz, logo_sz), fill=255)
                    logo.putalpha(lm)
                    img.paste(logo, (lx, ly), logo)
                except Exception:
                    pass
            else:
                draw.ellipse((lx, ly, lx + logo_sz, ly + logo_sz), fill=(80, 40, 140))
                fn = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 38)
                draw.text((lx + 22, ly + 22), "♪", font=fn, fill=(255, 255, 255))

            os.makedirs("cache/thumbs", exist_ok=True)
            img.save(output)
            return output
        except Exception as e:
            logger.warning("Design 1 thumb error: %s", e)
            return config.DEFAULT_THUMB

    # ── Design 2 – Cinematic ─────────────────────────────────────────────────

    async def generate_design2(self, song: Track) -> str:
        """Blurred bg, info on left, cover card + requester DP on right, waveform bottom."""
        try:
            output = f"cache/thumbs/d2_{song.id}.png"
            if os.path.exists(output):
                return output

            W, H = 1280, 640

            font_title  = ImageFont.truetype("anony/helpers/Raleway-Bold.ttf", 50)
            font_sub    = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 26)
            font_small  = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 20)
            font_badge  = ImageFont.truetype("anony/helpers/Inter-Light.ttf", 18)

            # Background: blurred + darkened song thumbnail
            temp_bg = f"cache/thumbs/tmp_d2bg_{song.id}.jpg"
            if song.thumbnail:
                try:
                    await self.save_thumb(temp_bg, song.thumbnail)
                    bg = Image.open(temp_bg).convert("RGBA").resize(
                        (W, H), Image.Resampling.LANCZOS)
                    bg = bg.filter(ImageFilter.GaussianBlur(30))
                    bg = ImageEnhance.Brightness(bg).enhance(0.35)
                except Exception:
                    bg = Image.new("RGBA", (W, H), (20, 10, 30, 255))
            else:
                bg = Image.new("RGBA", (W, H), (20, 10, 30, 255))

            img = bg.copy()

            # Dark fade overlay (left 65%)
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ov = ImageDraw.Draw(overlay)
            fade_end = int(W * 0.68)
            for x in range(fade_end):
                alpha = int(185 * (1 - x / fade_end))
                ov.line([(x, 0), (x, H)], fill=(0, 0, 0, alpha))
            img = Image.alpha_composite(img, overlay)
            draw = ImageDraw.Draw(img)

            # "NOW PLAYING" badge
            draw.rounded_rectangle((38, 38, 210, 70), radius=16,
                                   fill=(255, 255, 255, 45))
            draw.text((56, 46), "NOW PLAYING", font=font_badge, fill=(255, 255, 255))

            # "Music Bot" badge (top right)
            bot_text = "Music Bot"
            bbb = font_badge.getbbox(bot_text)
            bbw = bbb[2] - bbb[0] + 44
            draw.rounded_rectangle((W - bbw - 18, 34, W - 18, 74),
                                   radius=18, fill=(20, 20, 40, 200))
            draw.text((W - bbw - 2, 46), bot_text, font=font_badge, fill=(255, 255, 255))

            # Title (up to 2 lines)
            title = song.title or "Unknown"
            max_c = 22
            lines = ([title[:max_c], title[max_c:max_c * 2] + "..."]
                     if len(title) > max_c else [title])
            ty = 100
            for line in lines[:2]:
                draw.text((40, ty), line, font=font_title, fill=(255, 255, 255))
                ty += 62

            # Artist
            artist = (song.channel_name or "")[:36]
            draw.text((40, ty + 10), artist, font=font_sub, fill=(210, 210, 220))

            # Stats
            parts = []
            if song.duration:
                parts.append(song.duration)
            if song.view_count:
                parts.append(f"{song.view_count} views")
            parts.append("YouTube")
            draw.text((40, ty + 50), "  •  ".join(parts), font=font_small, fill=(175, 175, 185))

            # Accent bar
            draw.rounded_rectangle((40, ty + 90, 185, ty + 95),
                                   radius=2, fill=(200, 50, 50))

            # Cover card (right)
            cx, cy2 = 800, 55
            cw, ch = 330, 380
            temp_cover = f"cache/thumbs/tmp_d2cv_{song.id}.jpg"
            if song.thumbnail:
                try:
                    await self.save_thumb(temp_cover, song.thumbnail)
                    cover = Image.open(temp_cover).convert("RGBA").resize(
                        (cw, ch), Image.Resampling.LANCZOS)
                    cm = Image.new("L", (cw, ch), 0)
                    ImageDraw.Draw(cm).rounded_rectangle((0, 0, cw, ch), radius=22, fill=255)
                    cover.putalpha(cm)
                    img.paste(cover, (cx, cy2), cover)
                    try:
                        os.remove(temp_cover)
                    except Exception:
                        pass
                except Exception:
                    pass

            # Requester DP (overlapping bottom-right of card)
            dp_sz = 78
            dp_cx = cx + cw - dp_sz // 2 + 10
            dp_cy = cy2 + ch - dp_sz // 2 + 10
            dp_drawn = False

            if getattr(song, "user_id", None):
                try:
                    from anony import app
                    dp_file = f"cache/thumbs/dp_{song.user_id}.jpg"
                    if not os.path.exists(dp_file):
                        async for photo in app.get_chat_photos(song.user_id, limit=1):
                            await app.download_media(photo, file_name=dp_file)
                            break
                    if os.path.exists(dp_file):
                        dp = Image.open(dp_file).convert("RGBA").resize(
                            (dp_sz, dp_sz), Image.Resampling.LANCZOS)
                        dm = Image.new("L", (dp_sz, dp_sz), 0)
                        ImageDraw.Draw(dm).ellipse((0, 0, dp_sz, dp_sz), fill=255)
                        dp.putalpha(dm)
                        border = dp_sz + 6
                        draw.ellipse((dp_cx - border // 2, dp_cy - border // 2,
                                      dp_cx + border // 2, dp_cy + border // 2),
                                     fill=(255, 255, 255))
                        img.paste(dp, (dp_cx - dp_sz // 2, dp_cy - dp_sz // 2), dp)
                        dp_drawn = True
                except Exception:
                    pass

            if not dp_drawn:
                border = dp_sz + 6
                draw.ellipse((dp_cx - border // 2, dp_cy - border // 2,
                              dp_cx + border // 2, dp_cy + border // 2),
                             fill=(255, 255, 255))
                draw.ellipse((dp_cx - dp_sz // 2, dp_cy - dp_sz // 2,
                              dp_cx + dp_sz // 2, dp_cy + dp_sz // 2),
                             fill=(55, 55, 75))
                draw.text((dp_cx - 14, dp_cy - 16), "♪", font=font_sub, fill=(200, 200, 210))

            # Waveform bars (bottom, decorative)
            rng = random.Random(hash(song.id) if song.id else 42)
            bar_count = 68
            bx_start, by_base = 40, H - 55
            bx_end = 750
            step = (bx_end - bx_start) // bar_count
            max_bh = 32
            for i in range(bar_count):
                bh = rng.randint(5, max_bh)
                bx0 = bx_start + i * step
                fade = 1 - abs(i - bar_count / 2) / (bar_count / 2)
                r = int(170 + 60 * fade)
                g = int(35 + 15 * fade)
                draw.rounded_rectangle((bx0, by_base - bh, bx0 + step - 2, by_base),
                                       radius=2, fill=(r, g, 40, 210))

            os.makedirs("cache/thumbs", exist_ok=True)
            img.save(output)
            try:
                os.remove(temp_bg)
            except Exception:
                pass
            return output
        except Exception as e:
            logger.warning("Design 2 thumb error: %s", e)
            return config.DEFAULT_THUMB

    # ── Design 3 – Classic (original generator) ───────────────────────────────

    async def generate(self, song: Track, size=(1280, 720)) -> str:
        try:
            temp   = f"cache/temp_{song.id}.jpg"
            output = f"cache/{song.id}.png"
            if os.path.exists(output):
                return output

            await self.save_thumb(temp, song.thumbnail)
            thumb = Image.open(temp).convert("RGBA").resize(
                size, Image.Resampling.LANCZOS)
            blur  = thumb.filter(ImageFilter.GaussianBlur(25))
            image = ImageEnhance.Brightness(blur).enhance(.40)

            _rect = ImageOps.fit(
                thumb, self.rect,
                method=Image.LANCZOS, centering=(0.5, 0.5))
            ImageDraw.Draw(self.mask).rounded_rectangle(
                (0, 0, self.rect[0], self.rect[1]), radius=15, fill=255)
            _rect.putalpha(self.mask)
            image.paste(_rect, (183, 30), _rect)

            draw = ImageDraw.Draw(image)
            draw.text(
                xy=(50, 560),
                text=f"{song.channel_name[:25]} | {song.view_count}",
                font=self.font2, fill=self.fill)
            draw.text((50, 600),  song.title[:50],  font=self.font1, fill=self.fill)
            draw.text((40, 650),  "0:01",            font=self.font1)
            draw.line([(140, 670), (1160, 670)], fill=self.fill, width=5, joint="curve")
            draw.text((1185, 650), song.duration,    font=self.font1, fill=self.fill)

            image.save(output)
            try:
                os.remove(temp)
            except Exception:
                pass
            return output
        except Exception:
            return config.DEFAULT_THUMB
