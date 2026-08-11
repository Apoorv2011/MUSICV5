import { Router } from "express";
import { getSongsByIds, getSongByLink, getSongSuggestions } from "../modules/songs/songs.js";

const router = Router();

const handleError = (err: any, res: any) => {
  if (err?.status) return res.status(err.status).json({ success: false, message: err.message });
  res.status(500).json({ success: false, message: err?.message || "internal server error" });
};

router.get("/songs", async (req, res) => {
  const { ids, link } = req.query as { ids?: string; link?: string };
  if (!ids && !link) return res.status(400).json({ success: false, message: "Either song IDs or link is required" });
  try {
    const token = link?.match(/jiosaavn\.com\/song\/[^/]+\/([^/]+)$/)?.[1];
    const data = token ? await getSongByLink(token) : await getSongsByIds(ids!);
    res.json({ success: true, data });
  } catch (err) { handleError(err, res); }
});

router.get("/songs/:id", async (req, res) => {
  try {
    const data = await getSongsByIds(req.params.id);
    res.json({ success: true, data });
  } catch (err) { handleError(err, res); }
});

router.get("/songs/:id/suggestions", async (req, res) => {
  const limit = Number(req.query.limit) || 10;
  try {
    const data = await getSongSuggestions(req.params.id, limit);
    res.json({ success: true, data });
  } catch (err) { handleError(err, res); }
});

export default router;
