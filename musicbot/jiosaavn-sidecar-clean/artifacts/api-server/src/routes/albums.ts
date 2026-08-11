import { Router } from "express";
import { getAlbumById, getAlbumByLink } from "../modules/albums/albums.js";

const router = Router();

const handleError = (err: any, res: any) => {
  if (err?.status) return res.status(err.status).json({ success: false, message: err.message });
  res.status(500).json({ success: false, message: err?.message || "internal server error" });
};

router.get("/albums", async (req, res) => {
  const { id, link } = req.query as { id?: string; link?: string };
  if (!id && !link) return res.status(400).json({ success: false, message: "Either album ID or link is required" });
  try {
    const token = link?.match(/jiosaavn\.com\/album\/[^/]+\/([^/]+)$/)?.[1];
    const data = token ? await getAlbumByLink(token) : await getAlbumById(id!);
    res.json({ success: true, data });
  } catch (err) { handleError(err, res); }
});

export default router;
