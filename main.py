import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
from requests import get
from requests import patch
import os
import emoji

# Your discord token
discord_token = ''

scope = "user-read-currently-playing"
url_discord = 'https://discordapp.com/api/v6/users/@me/settings'
headers_discord = {
'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.305 Chrome/69.0.3497.128 Electron/4.0.8 Safari/537.36',
'Authorization': f'{discord_token}',
'Content-Type': 'application/json'
}


sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

results = sp.currently_playing()
print(results['item']['name'])
curr_track_id = results['item']['id']
lyrics = get(f"https://spotify-lyric-api.herokuapp.com/?trackid={curr_track_id}").content
lyrics = json.loads(lyrics)
while lyrics['error'] :
	lyrics = get(f"https://spotify-lyric-api.herokuapp.com/?trackid={curr_track_id}").content
	lyrics = json.loads(lyrics)
print(len(lyrics['lines']))
previous_time = 0
current_top = 0 
current_bottom = 0


def get_lyrics(track_id):
	lyrics = get(f"https://spotify-lyric-api.herokuapp.com/?trackid={track_id}").content
	lyrics = json.loads(lyrics)
	while lyrics['error'] :
		lyrics = get(f"https://spotify-lyric-api.herokuapp.com/?trackid={track_id}").content
		lyrics = json.loads(lyrics)
	return lyrics


while results['is_playing']:
	results = sp.currently_playing()
	current_time = int(results['progress_ms'])
	if results['timestamp'] > 0 :
		lyrics = get_lyrics(results['item']['id'])
	for i in range(len(lyrics['lines']) - 1):
		if current_time > int(lyrics['lines'][i]['startTimeMs']) and current_time < int(lyrics['lines'][i + 1]['startTimeMs']) and current_time > previous_time :
			print(lyrics['lines'][i]['words'])
			previous_time = int(lyrics['lines'][i + 1]['startTimeMs'])
			curr_lyrics = emoji.demojize(lyrics['lines'][i]['words'])
			# with open('lyrics.txt', 'w',encoding='utf8') as f:
				# f.write(curr_lyrics)
			current_top = int(lyrics['lines'][i + 1]['startTimeMs'])
			current_bottom = int(lyrics['lines'][i]['startTimeMs'])
			patch(url_discord, json={'custom_status':{'text': f'{curr_lyrics}','expires_at': None}},headers=headers_discord)

	if current_time < current_bottom or current_time > current_top:
		previous_time = 0

