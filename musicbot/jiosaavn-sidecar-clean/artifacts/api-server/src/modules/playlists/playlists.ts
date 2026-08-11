import { Endpoints } from '../common/constants.js'
import { useFetch } from '../common/fetch.js'
import { createImageLinks } from '../common/link.js'
import { createArtistMapPayload } from '../artists/artists.js'
import { createSongPayload } from '../songs/songs.js'

const createPlaylistPayload = (playlist: any) => ({
  id: playlist.id,
  name: playlist.title,
  description: playlist.header_desc,
  type: playlist.type,
  year: playlist.year ? Number(playlist.year) : null,
  playCount: playlist.play_count ? Number(playlist.play_count) : null,
  language: playlist.language,
  explicitContent: playlist.explicit_content === '1',
  url: playlist.perma_url,
  songCount: playlist.list_count ? Number(playlist.list_count) : null,
  artists: playlist.more_info?.artists?.map(createArtistMapPayload) || null,
  image: createImageLinks(playlist.image),
  songs: (playlist.list && playlist.list.map(createSongPayload)) || null
})

export const getPlaylistById = async (args: { id: string; limit: number; page: number }) => {
  const { data } = await useFetch<any>({
    endpoint: Endpoints.playlists.id,
    params: { listid: args.id, n: args.limit, p: args.page }
  })
  if (!data) throw { status: 404, message: 'playlist not found' }
  const playlist = createPlaylistPayload(data)
  return {
    ...playlist,
    songCount: playlist.songs?.length || null,
    songs: playlist.songs?.slice(0, args.limit) || []
  }
}

export const getPlaylistByLink = async (args: { token: string; limit: number; page: number }) => {
  const { data } = await useFetch<any>({
    endpoint: Endpoints.albums.link,
    params: { token: args.token, n: args.limit, p: args.page, type: 'playlist' }
  })
  if (!data) throw { status: 404, message: 'playlist not found' }
  const playlist = createPlaylistPayload(data)
  return {
    ...playlist,
    songCount: playlist.songs?.length || null,
    songs: playlist.songs?.slice(0, args.limit) || []
  }
}
