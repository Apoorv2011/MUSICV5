import { Endpoints } from '../common/constants.js'
import { useFetch } from '../common/fetch.js'
import { createImageLinks } from '../common/link.js'
import { createSongPayload } from '../songs/songs.js'
import { createAlbumPayload } from '../albums/albums.js'

export const createArtistMapPayload = (artist: any) => ({
  id: artist.id,
  name: artist.name,
  role: artist.role,
  type: artist.type,
  image: createImageLinks(artist.image),
  url: artist.perma_url
})

const createArtistPayload = (artist: any) => ({
  id: artist.artistId || artist.id,
  name: artist.name,
  url: artist.urls?.overview || artist.perma_url,
  type: artist.type,
  followerCount: artist.follower_count ? Number(artist.follower_count) : null,
  fanCount: artist.fan_count || null,
  isVerified: artist.isVerified || null,
  dominantLanguage: artist.dominantLanguage || null,
  dominantType: artist.dominantType || null,
  bio: artist.bio ? JSON.parse(artist.bio) : null,
  dob: artist.dob || null,
  fb: artist.fb || null,
  twitter: artist.twitter || null,
  wiki: artist.wiki || null,
  availableLanguages: artist.availableLanguages || null,
  isRadioPresent: artist.isRadioPresent || null,
  image: createImageLinks(artist.image),
  topSongs: artist.topSongs?.map(createSongPayload) || null,
  topAlbums: artist.topAlbums?.map(createAlbumPayload) || null,
  singles: artist.singles?.map(createSongPayload) || null,
  similarArtists: artist.similarArtists?.map((a: any) => ({
    id: a.id,
    name: a.name,
    url: a.perma_url,
    image: createImageLinks(a.image_url),
    languages: a.languages ? JSON.parse(a.languages) : null,
    wiki: a.wiki,
    dob: a.dob,
    fb: a.fb,
    twitter: a.twitter,
    isRadioPresent: a.isRadioPresent,
    type: a.type,
    dominantType: a.dominantType,
    aka: a.aka,
    bio: a.bio ? JSON.parse(a.bio) : null,
    similarArtists: a.similar ? JSON.parse(a.similar) : null
  })) || null
})

export const getArtistById = async (args: {
  artistId: string; page: number; songCount: number; albumCount: number
  sortBy: string; sortOrder: string
}) => {
  const { data } = await useFetch<any>({
    endpoint: Endpoints.artists.id,
    params: {
      artistId: args.artistId,
      n_song: args.songCount,
      n_album: args.albumCount,
      page: args.page,
      sort_order: args.sortOrder,
      category: args.sortBy
    }
  })
  if (!data) throw { status: 404, message: 'artist not found' }
  return createArtistPayload(data)
}

export const getArtistByLink = async (args: {
  token: string; page: number; songCount: number; albumCount: number
  sortBy: string; sortOrder: string
}) => {
  const { data } = await useFetch<any>({
    endpoint: Endpoints.artists.link,
    params: {
      token: args.token,
      n_song: args.songCount,
      n_album: args.albumCount,
      page: args.page,
      sort_order: args.sortOrder,
      category: args.sortBy,
      type: 'artist'
    }
  })
  if (!data) throw { status: 404, message: 'artist not found' }
  return createArtistPayload(data)
}

export const getArtistSongs = async (args: {
  artistId: string; page: number; sortBy: string; sortOrder: string
}) => {
  const { data } = await useFetch<any>({
    endpoint: Endpoints.artists.songs,
    params: { artistId: args.artistId, page: args.page, sort_order: args.sortOrder, category: args.sortBy }
  })
  if (!data) throw { status: 404, message: 'artist songs not found' }
  return {
    total: data.topSongs.total,
    songs: data.topSongs.songs.map(createSongPayload)
  }
}

export const getArtistAlbums = async (args: {
  artistId: string; page: number; sortBy: string; sortOrder: string
}) => {
  const { data } = await useFetch<any>({
    endpoint: Endpoints.artists.albums,
    params: { artistId: args.artistId, page: args.page, sort_order: args.sortOrder, category: args.sortBy }
  })
  if (!data) throw { status: 404, message: 'artist albums not found' }
  return {
    total: data.topAlbums.total,
    albums: data.topAlbums.albums.map(createAlbumPayload)
  }
}
