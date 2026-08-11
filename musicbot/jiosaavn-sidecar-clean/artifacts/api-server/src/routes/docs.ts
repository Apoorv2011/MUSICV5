import { Router } from "express";
import { apiReference } from "@scalar/express-api-reference";

const router = Router();

const openApiSpec = {
  openapi: "3.1.0",
  info: {
    version: "1.0.0",
    title: "JioSaavn API",
    description:
      "# Introduction\n\nJioSaavn API is an unofficial API that allows users to access high-quality songs from [JioSaavn](https://jiosaavn.com). It offers a fast, reliable, and easy-to-use API for developers.\n"
  },
  paths: {
    "/api/search": {
      get: {
        operationId: "searchAll",
        summary: "Search all",
        description: "Search across songs, albums, artists, and playlists",
        parameters: [
          { name: "query", in: "query", required: true, schema: { type: "string" }, description: "Search query" }
        ],
        responses: { "200": { description: "Search results" }, "400": { description: "query is required" } }
      }
    },
    "/api/search/songs": {
      get: {
        operationId: "searchSongs",
        summary: "Search songs",
        parameters: [
          { name: "query", in: "query", required: true, schema: { type: "string" } },
          { name: "page", in: "query", schema: { type: "integer", default: 0 } },
          { name: "limit", in: "query", schema: { type: "integer", default: 10 } }
        ],
        responses: { "200": { description: "Song search results" } }
      }
    },
    "/api/search/albums": {
      get: {
        operationId: "searchAlbums",
        summary: "Search albums",
        parameters: [
          { name: "query", in: "query", required: true, schema: { type: "string" } },
          { name: "page", in: "query", schema: { type: "integer", default: 0 } },
          { name: "limit", in: "query", schema: { type: "integer", default: 10 } }
        ],
        responses: { "200": { description: "Album search results" } }
      }
    },
    "/api/search/artists": {
      get: {
        operationId: "searchArtists",
        summary: "Search artists",
        parameters: [
          { name: "query", in: "query", required: true, schema: { type: "string" } },
          { name: "page", in: "query", schema: { type: "integer", default: 0 } },
          { name: "limit", in: "query", schema: { type: "integer", default: 10 } }
        ],
        responses: { "200": { description: "Artist search results" } }
      }
    },
    "/api/search/playlists": {
      get: {
        operationId: "searchPlaylists",
        summary: "Search playlists",
        parameters: [
          { name: "query", in: "query", required: true, schema: { type: "string" } },
          { name: "page", in: "query", schema: { type: "integer", default: 0 } },
          { name: "limit", in: "query", schema: { type: "integer", default: 10 } }
        ],
        responses: { "200": { description: "Playlist search results" } }
      }
    },
    "/api/songs": {
      get: {
        operationId: "getSongs",
        summary: "Get song(s) by ID or link",
        parameters: [
          { name: "ids", in: "query", schema: { type: "string" }, description: "Comma-separated song IDs" },
          { name: "link", in: "query", schema: { type: "string" }, description: "JioSaavn song URL" }
        ],
        responses: { "200": { description: "Song details" }, "400": { description: "ids or link required" } }
      }
    },
    "/api/songs/{id}": {
      get: {
        operationId: "getSongById",
        summary: "Get song by ID",
        parameters: [{ name: "id", in: "path", required: true, schema: { type: "string" } }],
        responses: { "200": { description: "Song details" } }
      }
    },
    "/api/songs/{id}/suggestions": {
      get: {
        operationId: "getSongSuggestions",
        summary: "Get song suggestions",
        parameters: [
          { name: "id", in: "path", required: true, schema: { type: "string" } },
          { name: "limit", in: "query", schema: { type: "integer", default: 10 } }
        ],
        responses: { "200": { description: "Similar songs" } }
      }
    },
    "/api/albums": {
      get: {
        operationId: "getAlbum",
        summary: "Get album by ID or link",
        parameters: [
          { name: "id", in: "query", schema: { type: "string" } },
          { name: "link", in: "query", schema: { type: "string" }, description: "JioSaavn album URL" }
        ],
        responses: { "200": { description: "Album details" }, "400": { description: "id or link required" } }
      }
    },
    "/api/albums/{id}": {
      get: {
        operationId: "getAlbumById",
        summary: "Get album by ID",
        parameters: [{ name: "id", in: "path", required: true, schema: { type: "string" } }],
        responses: { "200": { description: "Album details" } }
      }
    },
    "/api/artists": {
      get: {
        operationId: "getArtist",
        summary: "Get artist by ID or link",
        parameters: [
          { name: "id", in: "query", schema: { type: "string" } },
          { name: "link", in: "query", schema: { type: "string" }, description: "JioSaavn artist URL" },
          { name: "page", in: "query", schema: { type: "integer", default: 0 } },
          { name: "songCount", in: "query", schema: { type: "integer", default: 10 } },
          { name: "albumCount", in: "query", schema: { type: "integer", default: 10 } },
          { name: "sortBy", in: "query", schema: { type: "string", default: "popularity" } },
          { name: "sortOrder", in: "query", schema: { type: "string", default: "asc" } }
        ],
        responses: { "200": { description: "Artist details" }, "400": { description: "id or link required" } }
      }
    },
    "/api/artists/{id}": {
      get: {
        operationId: "getArtistById",
        summary: "Get artist by ID",
        parameters: [{ name: "id", in: "path", required: true, schema: { type: "string" } }],
        responses: { "200": { description: "Artist details" } }
      }
    },
    "/api/artists/{id}/songs": {
      get: {
        operationId: "getArtistSongs",
        summary: "Get artist songs",
        parameters: [
          { name: "id", in: "path", required: true, schema: { type: "string" } },
          { name: "page", in: "query", schema: { type: "integer", default: 0 } },
          { name: "sortBy", in: "query", schema: { type: "string", default: "popularity" } },
          { name: "sortOrder", in: "query", schema: { type: "string", default: "desc" } }
        ],
        responses: { "200": { description: "Artist songs" } }
      }
    },
    "/api/artists/{id}/albums": {
      get: {
        operationId: "getArtistAlbums",
        summary: "Get artist albums",
        parameters: [
          { name: "id", in: "path", required: true, schema: { type: "string" } },
          { name: "page", in: "query", schema: { type: "integer", default: 0 } },
          { name: "sortBy", in: "query", schema: { type: "string", default: "popularity" } },
          { name: "sortOrder", in: "query", schema: { type: "string", default: "desc" } }
        ],
        responses: { "200": { description: "Artist albums" } }
      }
    },
    "/api/playlists": {
      get: {
        operationId: "getPlaylist",
        summary: "Get playlist by ID or link",
        parameters: [
          { name: "id", in: "query", schema: { type: "string" } },
          { name: "link", in: "query", schema: { type: "string" }, description: "JioSaavn playlist URL" },
          { name: "page", in: "query", schema: { type: "integer", default: 0 } },
          { name: "limit", in: "query", schema: { type: "integer", default: 10 } }
        ],
        responses: { "200": { description: "Playlist details" }, "400": { description: "id or link required" } }
      }
    },
    "/api/playlists/{id}": {
      get: {
        operationId: "getPlaylistById",
        summary: "Get playlist by ID",
        parameters: [{ name: "id", in: "path", required: true, schema: { type: "string" } }],
        responses: { "200": { description: "Playlist details" } }
      }
    },
    "/api/healthz": {
      get: {
        operationId: "healthCheck",
        summary: "Health check",
        responses: { "200": { description: "Server is healthy" } }
      }
    }
  }
};

router.get("/swagger", (_req, res) => {
  res.json(openApiSpec);
});

router.use(
  "/docs",
  apiReference({
    pageTitle: "JioSaavn API Documentation",
    theme: "deepSpace",
    isEditable: false,
    layout: "modern",
    darkMode: true,
    url: "/api/swagger",
    metaData: {
      applicationName: "JioSaavn API",
      author: "Sumit Kolhe",
      creator: "Sumit Kolhe",
      publisher: "Sumit Kolhe",
      robots: "index, follow",
      description:
        "JioSaavn API is an unofficial wrapper written in TypeScript for jiosaavn.com providing programmatic access to a vast library of songs, albums, artists, playlists, and more."
    }
  })
);

export default router;
