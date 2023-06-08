# Spotify-Lyrics-to-Discord-Status
Takes current spotify song playing and display it's lyrics into User Discord account Custom Status
<br>
<br>

![its working](https://github.com/NassimMansouri/Spotify-Lyrics-to-Discord-Status/assets/123596322/8bca977e-b528-4c27-ac7f-5b52f6907d42)

<br>
<br>

# Getting your Client_ID, Client_Secret, Redirect_Uri :

<br>
1-Go to "https://developer.spotify.com/" and log-in
<br>
2-Go to the dashboard "https://developer.spotify.com/dashboard"
<br>
3-Create App and Fill the informations with what you want, For the "Redirect URI" put any link you want example "https://github.com/NassimMansouri/Spotify-Lyrics-to-Discord-Status"
<br>
4-Click Settings on the top right and it will show your client id and client secret the URI is the one you put above 
<br>

# Exporting Client_ID, Secret, URI

<br>
To set them permenantly : 
<br>
Open CMD and type : 
<br>

```

setx SPOTIPY_CLIENT_ID YourClientId /m
setx SPOTIPY_CLIENT_SECRET YourClientSecret /m
setx SPOTIPY_REDIRECT_URI YourURI /m

```

<br>
For Linux users: 

```

export SPOTIPY_CLIENT_ID='your-spotify-client-id'
export SPOTIPY_CLIENT_SECRET='your-spotify-client-secret'
export SPOTIPY_REDIRECT_URI='your-app-redirect-url'

```

# How to get your Discord Token

Watch this tutorial : 
https://youtu.be/YEgFvgg7ZPI


# Usage : 

-Set your discord token in main.py 
<br>
-Open cmd in the same directory and type

```
py main.py
```
