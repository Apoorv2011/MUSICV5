import express, { type Express, Request, Response } from "express";
import cors from "cors";
import pinoHttp from "pino-http";
import router from "./routes";
import { logger } from "./lib/logger";
import { searchSongs } from "./modules/search/search.js";
import { getSongsByIds } from "./modules/songs/songs.js";

const app: Express = express();

app.use(
  pinoHttp({
    logger,
    serializers: {
      req(req) {
        return {
          id: req.id,
          method: req.method,
          url: req.url?.split("?")[0],
        };
      },
      res(res) {
        return {
          statusCode: res.statusCode,
        };
      },
    },
  }),
);
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Sidecar: root-level /search and /download endpoints
app.get("/search", async (req: Request, res: Response) => {
  const q = req.query.q as string;
  if (!q) {
    return res.status(400).json({ error: "missing query" });
  }
  try {
    const data = await searchSongs({ query: q, page: 0, limit: 10 });
    const tracks = data.results.map((song: any) => ({
      id: song.id,
      title: song.name,
      artists: song.artists?.all?.map((a: any) => a.name).join(", ") || "",
      duration: song.duration || 0,
      thumbnail: song.image?.find((i: any) => i.quality === "500x500")?.url || song.image?.[0]?.url || "",
      url: song.url || "",
    }));
    return res.json({ tracks });
  } catch (err: any) {
    return res.status(500).json({ error: err.message || "internal error" });
  }
});

app.get("/download", async (req: Request, res: Response) => {
  const id = req.query.id as string;
  const q = req.query.q as string;
  if (!id && !q) {
    return res.status(400).json({ error: "missing id or q" });
  }
  try {
    let songId = id;
    if (!songId && q) {
      const searchData = await searchSongs({ query: q, page: 0, limit: 1 });
      if (!searchData.results?.length) {
        return res.status(404).json({ error: "no results found" });
      }
      songId = searchData.results[0].id;
    }
    const songs = await getSongsByIds(songId!);
    const song = songs[0];
    const bestUrl = song.downloadUrl?.find((d: any) => d.quality === "320kbps")?.url
      || song.downloadUrl?.find((d: any) => d.quality === "160kbps")?.url
      || song.downloadUrl?.[song.downloadUrl.length - 1]?.url;
    return res.json({
      id: song.id,
      title: song.name,
      url: bestUrl || "",
    });
  } catch (err: any) {
    return res.status(500).json({ error: err.message || "internal error" });
  }
});

app.use("/api", router);

export default app;
