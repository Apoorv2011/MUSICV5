export const Endpoints = {
  search: {
    all: 'autocomplete.get',
    songs: 'search.getResults',
    albums: 'search.getAlbumResults',
    artists: 'search.getArtistResults',
    playlists: 'search.getPlaylistResults'
  },
  songs: {
    id: 'song.getDetails',
    link: 'webapi.get',
    suggestions: 'webradio.getSong',
    lyrics: 'lyrics.getLyrics',
    station: 'webradio.createEntityStation'
  },
  albums: {
    id: 'content.getAlbumDetails',
    link: 'webapi.get'
  },
  artists: {
    id: 'artist.getArtistPageDetails',
    link: 'webapi.get',
    songs: 'artist.getArtistMoreSong',
    albums: 'artist.getArtistMoreAlbum'
  },
  playlists: {
    id: 'playlist.getDetails',
    link: 'webapi.get'
  },
  modules: 'content.getBrowseModules',
  trending: 'content.getTrending'
}

export const userAgents = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0',
  'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Mobile Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:136.0) Gecko/20100101 Firefox/136.0',
  'Mozilla/5.0 (iPhone; CPU iPhone OS 18_3_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3.1 Mobile/15E148 Safari/604.1',
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'
]

export enum ApiContextEnum {
  ANDROID = 'android',
  WEB6DOT0 = 'web6dot0'
}
