import { Router } from "express";
import { getPlaylistById, getPlaylistByLink } from "../modules/playlists/playlists.js";

const router = Router();

const handleError = (err: any, res: any) => {
  if (err?.status) return res.status(err.status).json({ success: false, message: err.message });
  res.status(500).json({ success: false, message: err?.message || "internal server error" });
};

router.get("/playlists", async (req, res) => {
  const { id, link, page = "0", limit = "10" } = req.query as Record<string, string>;
  if (!id && !link) return res.status(400).json({ success: false, message: "Either playlist ID or link is required" });
  try {
    const matches = link?.match(/(?:jiosaavn\.com|saavn\.com)\/(?:featured|s\/playlist)\/[^/]+\/([^/]+)$|\/([^/]+)$/);
    const filtered = matches?.filter(Boolean);
    const token = filtered && filtered.length > 1 ? filtered[filtered.length - 1] : undefined;
    const args = { page: Number(page), limit: Number(limit) };
    const data = token ? await getPlaylistByLink({ token, ...args }) : await getPlaylistById({ id: id!, ...args });
    res.json({ success: true, data });
  } catch (err) { handleError(err, res); }
});

export default router;
