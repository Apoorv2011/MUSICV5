import { Endpoints } from '../common/constants.js'
import { useFetch } from '../common/fetch.js'
import { createImageLinks } from '../common/link.js'
import { createSongPayload } from '../songs/songs.js'

const createArtistMapPayload = (artist: any) => ({
  id: artist.id,
  name: artist.name,
  role: artist.role,
  type: artist.type,
  image: createImageLinks(artist.image),
  url: artist.perma_url
})

export const createAlbumPayload = (album: any) => ({
  id: album.id,
  name: album.title,
  description: album.header_desc,
  type: album.type,
  year: album.year ? Number(album.year) : null,
  playCount: album.play_count ? Number(album.play_count) : null,
  language: album.language,
  explicitContent: album.explicit_content === '1',
  url: album.perma_url,
  songCount: album.more_info?.song_count ? Number(album.more_info.song_count) : null,
  artists: {
    primary: album.more_info?.artistMap?.primary_artists?.map(createArtistMapPayload) || [],
    featured: album.more_info?.artistMap?.featured_artists?.map(createArtistMapPayload) || [],
    all: album.more_info?.artistMap?.artists?.map(createArtistMapPayload) || []
  },
  image: createImageLinks(album.image),
  songs: (album.list && album.list.map(createSongPayload)) || null
})

export const getAlbumById = async (id: string) => {
  const { data } = await useFetch<any>({
    endpoint: Endpoints.albums.id,
    params: { albumid: id }
  })
  if (!data) throw { status: 404, message: 'album not found' }
  return createAlbumPayload(data)
}

export const getAlbumByLink = async (token: string) => {
  const { data } = await useFetch<any>({
    endpoint: Endpoints.albums.link,
    params: { token, type: 'album' }
  })
  if (!data) throw { status: 404, message: 'album not found' }
  return createAlbumPayload(data)
}
