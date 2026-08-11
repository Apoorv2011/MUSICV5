import { Endpoints } from '../common/constants.js'
import { useFetch } from '../common/fetch.js'
import { createImageLinks } from '../common/link.js'
import { createSongPayload } from '../songs/songs.js'
import { createArtistMapPayload } from '../artists/artists.js'

const createSearchAlbumPayload = (album: any) => ({
  id: album.id,
  name: album.title,
  description: album.header_desc,
  url: album.perma_url,
  year: album.year ? Number(album.year) : null,
  type: album.type,
  playCount: album.play_count ? Number(album.play_count) : null,
  language: album.language,
  explicitContent: album.explicit_content === '1',
  artists: {
    primary: album.more_info?.artistMap?.primary_artists?.map(createArtistMapPayload) || [],
    featured: album.more_info?.artistMap?.featured_artists?.map(createArtistMapPayload) || [],
    all: album.more_info?.artistMap?.artists?.map(createArtistMapPayload) || []
  },
  image: createImageLinks(album.image)
})

export const searchAll = async (query: string) => {
  const { data } = await useFetch<any>({
    endpoint: Endpoints.search.all,
    params: { query }
  })
  if (!data) throw { status: 404, message: `no results found for ${query}` }

  return {
    topQuery: {
      results: data.topquery?.data.map((item: any) => ({
        id: item.id,
        title: item.title,
        image: createImageLinks(item.image),
        album: item.more_info?.album,
        url: item.perma_url,
        type: item.type,
        language: item.more_info?.language,
        description: item.description,
        primaryArtists: item.more_info?.primary_artists,
        singers: item.more_info?.singers
      })) || [],
      position: data.topquery?.position || 0
    },
    songs: {
      results: data.songs?.data.map((song: any) => ({
        id: song.id,
        title: song.title,
        image: createImageLinks(song.image),
        album: song.more_info?.album,
        url: song.perma_url,
        type: song.type,
        description: song.description,
        primaryArtists: song.more_info?.primary_artists,
        singers: song.more_info?.singers,
        language: song.more_info?.language
      })) || [],
      position: data.songs?.position || 0
    },
    albums: {
      results: data.albums?.data.map((album: any) => ({
        id: album.id,
        title: album.title,
        image: createImageLinks(album.image),
        artist: album.more_info?.music,
        url: album.perma_url,
        type: album.type,
        description: album.description,
        year: album.more_info?.year,
        songIds: album.more_info?.song_pids,
        language: album.more_info?.language
      })) || [],
      position: data.albums?.position || 0
    },
    artists: {
      results: data.artists?.data.map((artist: any) => ({
        id: artist.id,
        title: artist.title,
        image: createImageLinks(artist.image),
        type: artist.type,
        description: artist.description,
        position: artist.position
      })) || [],
      position: data.artists?.position || 0
    },
    playlists: {
      results: data.playlists?.data.map((playlist: any) => ({
        id: playlist.id,
        title: playlist.title,
        image: createImageLinks(playlist.image),
        url: playlist.perma_url,
        type: playlist.type,
        language: playlist.more_info?.language,
        description: playlist.description
      })) || [],
      position: data.playlists?.position || 0
    }
  }
}

export const searchSongs = async (args: { query: string; page: number; limit: number }) => {
  const { data } = await useFetch<any>({
    endpoint: Endpoints.search.songs,
    params: { q: args.query, p: args.page, n: args.limit }
  })
  return {
    total: data.total,
    start: data.start,
    results: data.results?.map(createSongPayload).slice(0, args.limit) || []
  }
}

export const searchAlbums = async (args: { query: string; page: number; limit: number }) => {
  const { data } = await useFetch<any>({
    endpoint: Endpoints.search.albums,
    params: { q: args.query, p: args.page, n: args.limit }
  })
  return {
    total: Number(data.total),
    start: Number(data.start),
    results: data.results?.map(createSearchAlbumPayload) || []
  }
}

export const searchArtists = async (args: { query: string; page: number; limit: number }) => {
  const { data } = await useFetch<any>({
    endpoint: Endpoints.search.artists,
    params: { q: args.query, p: args.page, n: args.limit }
  })
  if (!data) throw { status: 404, message: 'artist not found' }
  return {
    total: data.total,
    start: data.start,
    results: data.results?.map(createArtistMapPayload).slice(0, args.limit) || []
  }
}

export const searchPlaylists = async (args: { query: string; page: number; limit: number }) => {
  const { data } = await useFetch<any>({
    endpoint: Endpoints.search.playlists,
    params: { q: args.query, p: args.page, n: args.limit }
  })
  if (!data) throw { status: 404, message: 'playlist not found' }
  return {
    total: Number(data.total),
    start: Number(data.start),
    results: data.results?.map((item: any) => ({
      id: item.id,
      name: item.title,
      type: item.type,
      image: createImageLinks(item.image),
      url: item.perma_url,
      songCount: item.more_info?.song_count ? Number(item.more_info.song_count) : null,
      language: item.more_info?.language,
      explicitContent: item.explicit_content === '1'
    })) || []
  }
}
