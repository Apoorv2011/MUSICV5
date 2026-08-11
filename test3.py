from ytmusicapi import YTMusic

# Initialize the public, unauthenticated API client
ytmusic = YTMusic()

# Replace this with your target YouTube video/track ID
video_id = 'dQw4w9WgXcQ' 

print(f"Fetching recommendations for video ID: {video_id}...\n")

# get_watch_playlist acts like the YouTube Music "Up Next" queue/radio
recommendations = ytmusic.get_watch_playlist(videoId=video_id)

# Loop through and print the recommended tracks
for index, track in enumerate(recommendations['tracks'][:10], start=1):
    title = track.get('title')
    artist = track.get('artists')[0].get('name') if track.get('artists') else 'Unknown Artist'
    print(f"{index}. {title} by {artist} (ID: {track.get('videoId')})")
