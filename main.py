# -*- coding: utf-8 -*-
import syncedlyrics
import json
import os
import emoji
import time
import random
import re
import bisect
import threading
from dataclasses import dataclass
from requests import patch
from dotenv import load_dotenv

load_dotenv(override=True)

try:
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    SPOTIPY_AVAILABLE = True
except ImportError:
    SPOTIPY_AVAILABLE = False

# ── Config (all editable in .env) ────────────────────────────────────────────
DISCORD_TOKEN         = os.getenv('DISCORD_TOKEN', '')
MOCK_SPOTIFY          = os.getenv('MOCK_SPOTIFY', 'false').lower() == 'true'
CACHING               = True
CACHE_DIR             = os.getenv('LYRICS_CACHE_DIR', 'Caching')
os.makedirs(CACHE_DIR, exist_ok=True)
LYRICS_FILE           = 'lyrics.txt'
PROVIDERS             = ['NetEase', 'Lrclib', 'Musixmatch']
SPOTIFY_POLL_INTERVAL = 2.0
SEEK_THRESHOLD_MS     = 1500
LYRIC_OFFSET_MS       = int(os.getenv('LYRIC_OFFSET_MS', '0'))
ENABLE_DISCORD        = os.getenv('ENABLE_DISCORD', 'true').lower() == 'true'
ENABLE_OVERLAY        = os.getenv('ENABLE_OVERLAY', 'true').lower() == 'true'
ENABLE_EMOJIS         = os.getenv('ENABLE_EMOJIS', 'true').lower() == 'true'
ENABLE_CENSOR         = os.getenv('ENABLE_CENSOR', 'false').lower() == 'true'
RESYNC_AFTER_MS       = int(os.getenv('RESYNC_AFTER_MS', '4000'))
# How many ms to fire Discord BEFORE the overlay (compensates for Discord network latency).
# Increase if Discord always appears after the subtitle. Start at 300 and tune.
DISCORD_LEAD_MS       = int(os.getenv('DISCORD_LEAD_MS', '300'))

DISCORD_EMOJIS = ['🤩','🎵','🔥','🥰','😇','💀','☠️','👻','💪','💅','💋','👑',
                  '💍','💄','🤰🏻','💥','☄️','⚡️','✨','🌟','⭐️','💫','🪐','🌪',
                  '☀️','🌩','❤️','💔','💞']

MOCK_TRACK = {
    'id': 'mock_blinding_lights',
    'name': 'Blinding Lights',
    'artists': [{'name': 'The Weeknd'}],
    'duration_ms': 200000,
}
_mock_start = time.time()

try:
    CENSORED_WORDS = open('censored_words.txt').read().split(',')
except FileNotFoundError:
    CENSORED_WORDS = []

# ── Startup banner ────────────────────────────────────────────────────────────
print('─' * 40)
print('  Spotify Lyrics')
print(f'  Discord status : {"on" if ENABLE_DISCORD else "off"}')
print(f'  Subtitle overlay: {"on" if ENABLE_OVERLAY else "off"}')
print(f'  Emojis          : {"on" if ENABLE_EMOJIS else "off"}')
print(f'  Censor          : {"on" if ENABLE_CENSOR else "off"}')
print(f'  Lyric offset    : {LYRIC_OFFSET_MS:+d}ms')
print(f'  Discord lead    : {DISCORD_LEAD_MS}ms before overlay')
print('─' * 40)

# ── Playback clock ────────────────────────────────────────────────────────────
@dataclass
class PlaybackClock:
    _progress_ms: int   = 0
    _fetched_at:  float = 0.0
    is_playing:   bool  = False

    def update(self, progress_ms: int, is_playing: bool) -> None:
        self._progress_ms = progress_ms
        self._fetched_at  = time.time()
        self.is_playing   = is_playing

    @property
    def current_ms(self) -> int:
        if not self.is_playing:
            return self._progress_ms
        return int(self._progress_ms + (time.time() - self._fetched_at) * 1000)

# ── Track state ───────────────────────────────────────────────────────────────
@dataclass
class TrackState:
    track_id:      str        = ''
    lyrics:        dict | None = None
    last_line_idx: int        = -1
    last_sent_at:  float      = 0.0
    retry_after:   float      = 0.0

    def reset(self):
        self.last_line_idx = -1
        self.last_sent_at  = 0.0
        self.retry_after   = 0.0

# ── Helpers ───────────────────────────────────────────────────────────────────
def censor_text(text: str) -> str:
    for word in CENSORED_WORDS:
        text = re.sub(re.escape(word), '****', text, flags=re.IGNORECASE)
    return text


def _is_ascii(text: str) -> bool:
    try:
        text.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False


def parse_lrc(lrc_text: str) -> list:
    lines = []
    for line in lrc_text.splitlines():
        match = re.match(r'\[(\d+):(\d+\.\d+)\](.*)', line.strip())
        if match:
            start_ms = int((int(match.group(1)) * 60 + float(match.group(2))) * 1000)
            lines.append({'startTimeMs': start_ms, 'words': match.group(3).strip()})
    return lines


def find_line_idx(lines: list, current_ms: int) -> int:
    starts = [ln['startTimeMs'] for ln in lines]
    idx = bisect.bisect_right(starts, current_ms) - 1
    if idx < 0 or idx >= len(lines) - 1:
        return -1
    return idx

# ── Lyrics ────────────────────────────────────────────────────────────────────
RETRY_DELAYS = [5, 15, 30]

def get_lyrics(track_id: str, track_name: str, artist_name: str) -> dict | None:
    cache_path = os.path.join(CACHE_DIR, f'{track_id}.json')
    if CACHING and os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    for attempt, delay in enumerate(RETRY_DELAYS, start=1):
        try:
            lrc_text = syncedlyrics.search(f'{track_name} {artist_name}', providers=PROVIDERS, synced_only=True)
            if not lrc_text:
                print(f'No synced lyrics: {track_name} — {artist_name}')
                return None

            lines = parse_lrc(lrc_text)
            lines = [ln for ln in lines if ln['startTimeMs'] > 3000 or _is_ascii(ln['words'])]
            data  = {'lines': lines}

            if CACHING:
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print('Cached.')

            return data
        except Exception as e:
            print(f'Lyrics error (attempt {attempt}/{len(RETRY_DELAYS)}): {e}')
            if attempt < len(RETRY_DELAYS):
                print(f'Retrying in {delay}s...')
                time.sleep(delay)

    return None

# ── Spotify ───────────────────────────────────────────────────────────────────
def fetch_currently_playing() -> dict | None:
    if MOCK_SPOTIFY:
        elapsed_ms = int((time.time() - _mock_start) * 1000)
        return {
            'is_playing':  True,
            'progress_ms': elapsed_ms % MOCK_TRACK['duration_ms'],
            'item':        MOCK_TRACK,
        }
    return sp.currently_playing()


def extract_track_info(results: dict) -> tuple:
    item = results['item']
    return item['id'], item['name'], item['artists'][0]['name']

# ── Discord ───────────────────────────────────────────────────────────────────
_discord_headers = {
    'User-Agent':    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.305 Chrome/69.0.3497.128 Electron/4.0.8 Safari/537.36',
    'Authorization': DISCORD_TOKEN,
    'Content-Type':  'application/json',
}
_discord_seq = 0  # incremented on every update; threads check this to avoid sending stale updates

def set_discord_status(text: str) -> None:
    global _discord_seq
    _discord_seq += 1
    seq = _discord_seq
    e   = random.choice(DISCORD_EMOJIS) if ENABLE_EMOJIS else ''
    status_text = f'{e} {text} {e}'.strip() if e.strip() else text

    def _send():
        if seq != _discord_seq:
            return  # a newer update was queued — drop this one
        try:
            patch(
                'https://discordapp.com/api/v6/users/@me/settings',
                json={'custom_status': {'text': status_text, 'expires_at': None}},
                headers=_discord_headers,
                timeout=5,
            )
        except Exception as ex:
            print(f'Discord error: {ex}')

    threading.Thread(target=_send, daemon=True).start()

# ── Overlay ───────────────────────────────────────────────────────────────────
def write_lyrics(text: str) -> None:
    with open(LYRICS_FILE, 'w', encoding='utf-8') as f:
        f.write(text)

# ── Output (fires both Discord + overlay) ─────────────────────────────────────
def push_line(line_text: str, now: float) -> None:
    if not line_text:
        if ENABLE_OVERLAY:
            write_lyrics('')
        return

    print(line_text)
    text = emoji.demojize(line_text)
    if ENABLE_CENSOR:
        text = censor_text(text)

    # Discord fires first (it has network latency), overlay fires DISCORD_LEAD_MS
    # later so both appear on screen at the same time.
    if ENABLE_DISCORD:
        set_discord_status(text)

    if ENABLE_OVERLAY:
        delay = DISCORD_LEAD_MS / 1000
        if delay > 0:
            def _delayed_overlay():
                time.sleep(delay)
                write_lyrics(line_text)
            threading.Thread(target=_delayed_overlay, daemon=True).start()
        else:
            write_lyrics(line_text)

    state.last_sent_at = now

# ── Init ──────────────────────────────────────────────────────────────────────
if not MOCK_SPOTIFY:
    if not SPOTIPY_AVAILABLE:
        raise RuntimeError('spotipy is not installed — run: pip install spotipy')
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope='user-read-currently-playing'))

if ENABLE_OVERLAY:
    write_lyrics('')

clock              = PlaybackClock()
state              = TrackState()
last_spotify_fetch = 0.0
track_name         = ''
artist_name        = ''

# ── Main loop ─────────────────────────────────────────────────────────────────
while True:
    try:
        now = time.time()

        if now - last_spotify_fetch >= SPOTIFY_POLL_INTERVAL:
            results = fetch_currently_playing()
            last_spotify_fetch = now

            if not results or not results.get('item'):
                clock.update(0, False)
                if ENABLE_OVERLAY:
                    write_lyrics('')
                time.sleep(2)
                continue

            new_progress = results['progress_ms']

            # Detect seek — reset so the correct line fires immediately
            if abs(new_progress - clock.current_ms) > SEEK_THRESHOLD_MS:
                state.last_line_idx = -1
                state.last_sent_at  = 0.0

            clock.update(new_progress, results['is_playing'])

            track_id, track_name, artist_name = extract_track_info(results)
            if track_id != state.track_id:
                print(f'\nNow playing: {track_name} — {artist_name}')
                state.track_id = track_id
                state.lyrics   = get_lyrics(track_id, track_name, artist_name)
                state.reset()
                if ENABLE_OVERLAY:
                    write_lyrics('')

        if not clock.is_playing:
            time.sleep(1)
            continue

        if state.lyrics is None and now >= state.retry_after:
            state.lyrics      = get_lyrics(state.track_id, track_name, artist_name)
            state.retry_after = now + 30

        if state.lyrics is None:
            time.sleep(0.1)
            continue

        current_ms = clock.current_ms + LYRIC_OFFSET_MS
        lines      = state.lyrics['lines']
        idx        = find_line_idx(lines, current_ms)

        if idx >= 0:
            line_changed = idx != state.last_line_idx
            # Resync if Discord hasn't been updated in a while (handles lag recovery)
            timed_out    = (now - state.last_sent_at) * 1000 > RESYNC_AFTER_MS

            if line_changed or timed_out:
                push_line(lines[idx]['words'], now)
                state.last_line_idx = idx

    except Exception as e:
        print(f'Error: {e}')

    time.sleep(0.1)
