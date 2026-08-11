import { Router, type IRouter } from "express";
import healthRouter from "./health.js";
import songsRouter from "./songs.js";
import albumsRouter from "./albums.js";
import artistsRouter from "./artists.js";
import playlistsRouter from "./playlists.js";
import searchRouter from "./search.js";
import docsRouter from "./docs.js";

const router: IRouter = Router();

router.use(healthRouter);
router.use(docsRouter);
router.use(songsRouter);
router.use(albumsRouter);
router.use(artistsRouter);
router.use(playlistsRouter);
router.use(searchRouter);

export default router;
