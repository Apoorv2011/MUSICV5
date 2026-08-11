import { Router } from "express";
import { searchAll, searchSongs, searchAlbums, searchArtists, searchPlaylists } from "../modules/search/search.js";

const router = Router();

const handleError = (err: any, res: any) => {
  if (err?.status) return res.status(err.status).json({ success: false, message: err.message });
  res.status(500).json({ success: false, message: err?.message || "internal server error" });
};

router.get("/search", async (req, res) => {
  const { query } = req.query as { query: string };
  if (!query) return res.status(400).json({ success: false, message: "query is required" });
  try {
    const data = await searchAll(query);
    res.json({ success: true, data });
  } catch (err) { handleError(err, res); }
});

router.get("/search/songs", async (req, res) => {
  const { query, page = "0", limit = "10" } = req.query as Record<string, string>;
  try {
    const data = await searchSongs({ query, page: Number(page), limit: Number(limit) });
    res.json({ success: true, data });
  } catch (err) { handleError(err, res); }
});

router.get("/search/albums", async (req, res) => {
  const { query, page = "0", limit = "10" } = req.query as Record<string, string>;
  try {
    const data = await searchAlbums({ query, page: Number(page), limit: Number(limit) });
    res.json({ success: true, data });
  } catch (err) { handleError(err, res); }
});

router.get("/search/artists", async (req, res) => {
  const { query, page = "0", limit = "10" } = req.query as Record<string, string>;
  try {
    const data = await searchArtists({ query, page: Number(page), limit: Number(limit) });
    res.json({ success: true, data });
  } catch (err) { handleError(err, res); }
});

router.get("/search/playlists", async (req, res) => {
  const { query, page = "0", limit = "10" } = req.query as Record<string, string>;
  try {
    const data = await searchPlaylists({ query, page: Number(page), limit: Number(limit) });
    res.json({ success: true, data });
  } catch (err) { handleError(err, res); }
});

export default router;
