import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
from requests import get
from requests import patch
import os
import emoji
import time
import random
# Your discord token
discord_token = 'MzgzNzM1NDkxMDc1NTA2MTc4.GgaygM.ZOup_LQevncn1TN4_QXUNlClx4-GETwgKQ7ZPE'

#Censored words
censored_words = (open('censored_words.txt').read()).split(',')
censor = False











answer = str(input('Would you like emojis to be displayed in your Status Y/n : '))
if answer.upper() == 'Y' : 
	discord_emojis = ['🤩','🎵', '🔥','🥰', '😇', '💀','☠️', '👻', '💪', '💅', '💋', '👑', '💍', '💄', '🤰🏻', '💥', '☄️', '⚡️', '✨', '🌟', '⭐️', '💫', '🪐', '🔥', '🌪', '☀️','🌩', '❤️', '💔', '💞']
else : 
	discord_emojis = [' ']


answer = str(input('Would you like to enable censorship of bad words ? Y/n : '))
if answer.upper() == 'Y':
	print('Note : Censored words are added manually by you within the censored_words.txt file')
	censor = True


def check_for_censorship(lyrics):
	for word in censored_words : 
		if word.upper() in lyrics.upper():
			word = word.lower()
			lyrics = lyrics.lower()
			lyrics = lyrics.replace(word,'****')
	return lyrics


error_message = '{"error":true,"message":"lyrics for this track is not available on spotify!"}'
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
def get_lyrics(track_id):
	try : 
		lyrics = get(f"https://spotify-lyric-api.herokuapp.com/?trackid={track_id}").content
		if lyrics.decode() != error_message : 
			lyrics = json.loads(lyrics)
			while lyrics['error'] :
				lyrics = get(f"https://spotify-lyric-api.herokuapp.com/?trackid={track_id}").content
				lyrics = json.loads(lyrics)
			return lyrics
	except : 
		print('connection lost ')
		return ' '
lyrics = get_lyrics(curr_track_id)
previous_time = 0
current_top = 0 
current_bottom = 0


while True : 
	while results['is_playing'] and lyrics != ' ':
		try :
			results = sp.currently_playing()
			current_time = int(results['progress_ms'])
			if results['timestamp'] > 0 :
				lyrics = get_lyrics(results['item']['id'])

			if lyrics != ' ' : 
				for i in range(len(lyrics['lines']) - 1):
					if current_time > int(lyrics['lines'][i]['startTimeMs']) and current_time < int(lyrics['lines'][i + 1]['startTimeMs']) and current_time > previous_time :
						print(lyrics['lines'][i]['words'])
						previous_time = int(lyrics['lines'][i + 1]['startTimeMs'])
						curr_lyrics = emoji.demojize(lyrics['lines'][i]['words'])
						if censor : 
							curr_lyrics = check_for_censorship(curr_lyrics)
							print(curr_lyrics)

						current_top = int(lyrics['lines'][i + 1]['startTimeMs'])
						current_bottom = int(lyrics['lines'][i]['startTimeMs'])

						# patch(url_discord, json={'custom_status':{'text': f'{random.choice(discord_emojis)} {curr_lyrics} {random.choice(discord_emojis)}','expires_at': None}},headers=headers_discord)

			if current_time < current_bottom or current_time > current_top:
				previous_time = 0
		except : 
			print('connection lost')


	time.sleep(1)
	try :
		results = sp.currently_playing()
		if results['timestamp'] > 0 :
			lyrics = get_lyrics(results['item']['id'])
			if censor : 
				lyrics = check_for_censorship(lyrics)
	except : 
		print('Connection lost')

