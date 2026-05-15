# LyricSync

Syncs your currently playing Spotify song — line by line — to your Discord custom status and an on-screen subtitle overlay, in real time.

<video src="https://github.com/user-attachments/assets/20ee87ec-f48d-4a37-b569-ac9a8b2d8f7a" autoplay loop muted playsinline></video>

---

## Features

- **Discord Status** — current lyric line pushed to your Discord custom status as you listen
- **Subtitle Overlay** — always-on-top subtitle bar anywhere on your screen
- **GUI** — modern settings panel with feature toggles, timing sliders, and on-screen position picker
- **Emoji support** — optionally strips or keeps emojis from lyrics
- **Word censor** — optional profanity filter via `censored_words.txt`
- **Lyrics cache** — lyrics are cached locally so repeat plays are instant
- **Self-correcting sync** — automatically resyncs Discord if it falls behind

> **Requires Spotify Premium** — the Spotify API only exposes real-time playback data to Premium accounts.

---

## Setup

### 1. Clone & install dependencies

```bash
git clone https://github.com/Graychii/Spotify-Lyrics-to-Discord-Status
cd Spotify-Lyrics-to-Discord-Status
pip install -r requirements.txt
```

### 2. Create your `.env` file

Copy the example and fill in your credentials:

```bash
cp .env.example .env
```

Then edit `.env` with your values (see sections below for how to get each one).

---

### Getting your Spotify credentials

1. Go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard) and log in
2. Click **Create App** — fill in any name/description
3. For **Redirect URI**, use any URL you own, e.g. `https://github.com/yourusername`
4. Click **Settings** → copy your **Client ID** and **Client Secret**

Paste them into `.env`:

```
SPOTIPY_CLIENT_ID=your_client_id
SPOTIPY_CLIENT_SECRET=your_client_secret
SPOTIPY_REDIRECT_URI=https://github.com/yourusername
```

**First run:** your browser will open for Spotify OAuth. Log in and paste the redirect URL back into the terminal when prompted. This only happens once — credentials are cached in `.cache`.

---

### Getting your Discord token

Watch this tutorial: https://youtu.be/YEgFvgg7ZPI

Paste it into `.env`:

```
DISCORD_TOKEN=your_discord_token
```

> **Note:** This uses your personal user token (not a bot token) to update your custom status. Self-bots and user token automation are against [Discord's Terms of Service](https://discord.com/terms). Use at your own risk — your account could be flagged or banned.

---

## Usage

Double-click `run.bat` or run:

```bash
py gui.py
```

The GUI lets you:
- Toggle Discord status / subtitle overlay / emojis / censor on or off
- Adjust lyric timing offset and Discord lead time
- Drag the subtitle bar to any position on screen using **Pick on Screen**
- Hit **Start** — everything launches automatically

---

## Configuration reference

All settings live in `.env` and are editable live from the GUI:

| Key | Default | Description |
|-----|---------|-------------|
| `ENABLE_DISCORD` | `true` | Push lyrics to Discord custom status |
| `ENABLE_OVERLAY` | `true` | Show subtitle overlay on screen |
| `ENABLE_EMOJIS` | `true` | Keep emojis in lyrics |
| `ENABLE_CENSOR` | `false` | Replace words in `censored_words.txt` with `***` |
| `LYRIC_OFFSET_MS` | `0` | Shift lyrics earlier (negative) or later (positive) |
| `DISCORD_LEAD_MS` | `300` | Fire Discord N ms before the overlay to compensate for network lag |
| `RESYNC_AFTER_MS` | `4000` | Force-resend Discord status after N ms of silence |
| `OVERLAY_Y` | auto | Y position of subtitle bar on screen (set via GUI) |

---

## Project structure

```
├── gui.py              # Settings GUI — launches and controls everything
├── main.py             # Core loop: Spotify polling, lyrics sync, Discord updates
├── display.py          # Subtitle overlay window
├── censored_words.txt  # One word per line to censor
├── requirements.txt
├── run.bat             # Windows launcher
├── .env                # Your credentials (not committed)
├── .env.example        # Template — copy to .env
└── Caching/            # Cached lyrics JSON files (not committed)
```
