import { Router } from "express";
import { getArtistById, getArtistByLink, getArtistSongs, getArtistAlbums } from "../modules/artists/artists.js";

const router = Router();

const handleError = (err: any, res: any) => {
  if (err?.status) return res.status(err.status).json({ success: false, message: err.message });
  res.status(500).json({ success: false, message: err?.message || "internal server error" });
};

router.get("/artists", async (req, res) => {
  const { id, link, page = "0", songCount = "10", albumCount = "10", sortBy = "popularity", sortOrder = "asc" } = req.query as Record<string, string>;
  if (!id && !link) return res.status(400).json({ success: false, message: "Either artist id or link is required" });
  try {
    const token = link?.match(/jiosaavn\.com\/artist\/[^/]+\/([^/]+)$/)?.[1];
    const args = { page: Number(page), songCount: Number(songCount), albumCount: Number(albumCount), sortBy: sortBy || "popularity", sortOrder: sortOrder || "asc" };
    const data = token ? await getArtistByLink({ token, ...args }) : await getArtistById({ artistId: id!, ...args });
    res.json({ success: true, data });
  } catch (err) { handleError(err, res); }
});

router.get("/artists/:id", async (req, res) => {
  const { page = "0", songCount = "10", albumCount = "10", sortBy = "popularity", sortOrder = "asc" } = req.query as Record<string, string>;
  try {
    const data = await getArtistById({
      artistId: req.params.id,
      page: Number(page),
      songCount: Number(songCount),
      albumCount: Number(albumCount),
      sortBy,
      sortOrder
    });
    res.json({ success: true, data });
  } catch (err) { handleError(err, res); }
});

router.get("/artists/:id/songs", async (req, res) => {
  const { page = "0", sortBy = "popularity", sortOrder = "desc" } = req.query as Record<string, string>;
  try {
    const data = await getArtistSongs({ artistId: req.params.id, page: Number(page), sortBy, sortOrder });
    res.json({ success: true, data });
  } catch (err) { handleError(err, res); }
});

router.get("/artists/:id/albums", async (req, res) => {
  const { page = "0", sortBy = "popularity", sortOrder = "desc" } = req.query as Record<string, string>;
  try {
    const data = await getArtistAlbums({ artistId: req.params.id, page: Number(page), sortBy, sortOrder });
    res.json({ success: true, data });
  } catch (err) { handleError(err, res); }
});

export default router;
