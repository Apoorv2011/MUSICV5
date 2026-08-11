import { Endpoints, ApiContextEnum } from '../common/constants.js'
import { useFetch } from '../common/fetch.js'
import { createDownloadLinks, createImageLinks } from '../common/link.js'

const createArtistMapPayload = (artist: any) => ({
  id: artist.id,
  name: artist.name,
  role: artist.role,
  type: artist.type,
  image: createImageLinks(artist.image),
  url: artist.perma_url
})

export const createSongPayload = (song: any) => ({
  id: song.id,
  name: song.title,
  type: song.type,
  year: song.year || null,
  releaseDate: song.more_info?.release_date || null,
  duration: song.more_info?.duration ? Number(song.more_info?.duration) : null,
  label: song.more_info?.label || null,
  explicitContent: song.explicit_content === '1',
  playCount: song.play_count ? Number(song.play_count) : null,
  language: song.language,
  hasLyrics: song.more_info?.has_lyrics === 'true',
  lyricsId: song.more_info?.lyrics_id || null,
  url: song.perma_url,
  copyright: song.more_info?.copyright_text || null,
  album: {
    id: song.more_info?.album_id || null,
    name: song.more_info?.album || null,
    url: song.more_info?.album_url || null
  },
  artists: {
    primary: song.more_info?.artistMap?.primary_artists?.map(createArtistMapPayload) || [],
    featured: song.more_info?.artistMap?.featured_artists?.map(createArtistMapPayload) || [],
    all: song.more_info?.artistMap?.artists?.map(createArtistMapPayload) || []
  },
  image: createImageLinks(song.image),
  downloadUrl: createDownloadLinks(song.more_info?.encrypted_media_url)
})

export const getSongsByIds = async (songIds: string) => {
  const { data } = await useFetch<{ songs: any[] }>({
    endpoint: Endpoints.songs.id,
    params: { pids: songIds }
  })
  if (!data.songs?.length) throw { status: 404, message: 'song not found' }
  return data.songs.map(createSongPayload)
}

export const getSongByLink = async (token: string) => {
  const { data } = await useFetch<{ songs: any[] }>({
    endpoint: Endpoints.songs.link,
    params: { token, type: 'song' }
  })
  if (!data.songs?.length) throw { status: 404, message: 'song not found' }
  return data.songs.map(createSongPayload)
}

export const getSongSuggestions = async (songId: string, limit: number) => {
  const encodedSongId = JSON.stringify([encodeURIComponent(songId)])
  const { data: stationData, ok: stationOk } = await useFetch<{ stationid: string }>({
    endpoint: Endpoints.songs.station,
    params: { entity_id: encodedSongId, entity_type: 'queue' },
    context: ApiContextEnum.ANDROID
  })
  if (!stationData || !stationOk || !stationData.stationid) throw { status: 500, message: 'could not create station' }

  const { data, ok } = await useFetch<any>({
    endpoint: Endpoints.songs.suggestions,
    params: { stationid: stationData.stationid, k: limit },
    context: ApiContextEnum.ANDROID
  })
  if (!data || !ok) throw { status: 404, message: 'no suggestions found for the given song' }

  const { stationid, ...suggestions } = data
  return Object.values(suggestions)
    .map((element: any) => element && createSongPayload(element.song))
    .filter(Boolean)
    .slice(0, limit)
}
