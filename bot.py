"""
╔══════════════════════════════════════════════════════════════╗
║           🎵 NEO MUSIC — by Xyrons2                          ║
║  Style   : Modern dark tonal · Aurora cyan aesthetic         ║
║  Platform: YouTube · Spotify · SoundCloud · Apple Music     ║
║             Deezer · Tidal · Bandcamp                        ║
║  Audio   : Harman · Dolby · Bass · Lofi · 8D · Nightcore    ║
║  24/7    : !247 setvoicechannel · stayinchannel · autojoin   ║
║                                                              ║
║  DENGAN HYDRA PRESET ✨ (smooth warm default)               ║
╚══════════════════════════════════════════════════════════════╝
"""

import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import yt_dlp
import aiohttp
import spotipy
import shutil, subprocess, sys, json, time
from spotipy.oauth2 import SpotifyClientCredentials
from collections import deque
from urllib.parse import urlparse
import os, re, random, html, traceback
import urllib.parse
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
TOKEN          = os.getenv("DISCORD_TOKEN")
SPOTIFY_ID     = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# ── FIX #1: Validasi token agar error jelas saat startup ──
if not TOKEN:
    raise RuntimeError("❌ DISCORD_TOKEN tidak ditemukan! Set di Railway Variables.")

BOT_START_TIME = time.time()

def find_ffmpeg() -> str:
    env = os.getenv("FFMPEG_PATH")
    if env and os.path.isfile(env):
        return env
    found = shutil.which("ffmpeg")
    if found:
        return found
    for path in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
        if os.path.isfile(path):
            return path
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "imageio-ffmpeg"],
                      check=True, timeout=120)
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"

FFMPEG_PATH = find_ffmpeg()
print(f"[🎬] FFmpeg: {FFMPEG_PATH}")

def load_opus():
    if discord.opus.is_loaded():
        return True
    import ctypes.util
    paths = [
        "/usr/lib/x86_64-linux-gnu/libopus.so.0",
        "/usr/lib/aarch64-linux-gnu/libopus.so.0",
        "/usr/lib/libopus.so.0",
        "libopus.so.0",
        "libopus.so",
    ]
    for path in paths:
        try:
            discord.opus.load_opus(path)
            return True
        except Exception:
            pass
    try:
        lib = ctypes.util.find_library("opus")
        if lib:
            discord.opus.load_opus(lib)
            return True
    except Exception:
        pass
    return False

load_opus()

sp = None
if SPOTIFY_ID and SPOTIFY_SECRET:
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
            client_id=SPOTIFY_ID, client_secret=SPOTIFY_SECRET))
    except Exception as e: print(f"[Spotify] {e}")

SETTINGS_FILE = "247_settings.json"

def load_247() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE) as f: return json.load(f)
        except Exception: pass
    return {}

def save_247_all(data: dict):
    try:
        with open(SETTINGS_FILE, "w") as f: json.dump(data, f, indent=2)
    except Exception as e: print(f"[247] {e}")

settings_247 = load_247()

def get_247(guild_id: int) -> dict:
    gid = str(guild_id)
    if gid not in settings_247:
        settings_247[gid] = {"stay_in_channel": False, "auto_join": False, "voice_channel_id": None}
    return settings_247[gid]

def save_247(guild_id: int):
    settings_247[str(guild_id)] = get_247(guild_id)
    save_247_all(settings_247)

REQUEST_FILE = "request_channels.json"

def load_request() -> dict:
    if os.path.exists(REQUEST_FILE):
        try:
            with open(REQUEST_FILE) as f: return json.load(f)
        except Exception: pass
    return {}

def save_request(data: dict):
    try:
        with open(REQUEST_FILE, "w") as f: json.dump(data, f, indent=2)
    except Exception as e: print(f"[Request] {e}")

request_channels = load_request()

def get_request_ch(guild_id: int):
    return request_channels.get(str(guild_id))

VOTESKIP_RATIO = 0.5

PLATFORM_MAP = {
    "youtube":     ["youtube.com", "youtu.be", "music.youtube.com"],
    "spotify":     ["open.spotify.com"],
    "soundcloud":  ["soundcloud.com"],
    "apple_music": ["music.apple.com"],
    "deezer":      ["deezer.com", "deezer.page.link"],
    "tidal":       ["tidal.com", "listen.tidal.com"],
    "bandcamp":    ["bandcamp.com"],
    "mixcloud":    ["mixcloud.com"],
    "dailymotion": ["dailymotion.com", "dai.ly"],
    "twitch":      ["twitch.tv"],
    "direct":      [".mp3", ".mp4", ".ogg", ".flac", ".m4a", ".wav", ".opus"],
}
YTDLP_NATIVE = {"youtube", "soundcloud", "bandcamp", "mixcloud", "dailymotion", "twitch", "direct"}

PLATFORM_ICONS = {
    "youtube": "🔴", "spotify": "🟢", "soundcloud": "🟠",
    "apple_music": "⚪", "deezer": "💜", "tidal": "🔷",
    "bandcamp": "🔵", "mixcloud": "☁️", "dailymotion": "🔵",
    "twitch": "🟣", "direct": "📁", "ytdlp_fallback": "🌐", "search": "🔴",
}
PLATFORM_NAMES = {
    "youtube": "YouTube", "spotify": "Spotify", "soundcloud": "SoundCloud",
    "apple_music": "Apple Music", "deezer": "Deezer", "tidal": "Tidal",
    "bandcamp": "Bandcamp", "mixcloud": "Mixcloud", "dailymotion": "Dailymotion",
    "twitch": "Twitch", "direct": "Direct", "ytdlp_fallback": "Web", "search": "YouTube",
}
PLATFORM_COLORS = {
    "youtube": 0xEF4444, "spotify": 0x22C55E, "soundcloud": 0xF97316,
    "apple_music": 0xFC3C44, "deezer": 0xA855F7, "tidal": 0x06B6D4,
    "bandcamp": 0x1DA0C3, "search": 0xEF4444,
}

def detect_platform(url: str) -> str:
    url_lower = url.lower()
    for platform, patterns in PLATFORM_MAP.items():
        for p in patterns:
            if p in url_lower: return platform
    return "ytdlp_fallback"

def is_url(text: str) -> bool:
    try: r = urlparse(text); return r.scheme in ("http", "https")
    except Exception: return False

def is_yt_playlist(url: str) -> bool:
    return "youtube.com" in url and ("list=" in url or "/playlist" in url)

PRESETS = {
    "hydra": {
        "label": "Hydra", "icon": "🌊",
        "desc": "By Xyrons2",
        "filter": (
            "volume=1.0,"
            "highpass=f=35,"
            "lowpass=f=20000,"
            "equalizer=f=55:width_type=o:width=2:g=3.0,"
            "equalizer=f=100:width_type=o:width=2:g=2.5,"
            "equalizer=f=160:width_type=o:width=2:g=1.5,"
            "equalizer=f=300:width_type=o:width=2:g=-1.5,"
            "equalizer=f=500:width_type=o:width=2:g=-0.8,"
            "equalizer=f=1000:width_type=o:width=2:g=0.5,"
            "equalizer=f=2000:width_type=o:width=2:g=1.5,"
            "equalizer=f=3500:width_type=o:width=2:g=1.0,"
            "equalizer=f=5000:width_type=o:width=2:g=0.5,"
            "equalizer=f=8000:width_type=o:width=2:g=1.5,"
            "equalizer=f=12000:width_type=o:width=2:g=1.2,"
            "equalizer=f=16000:width_type=o:width=2:g=0.8,"
            "equalizer=f=18000:width_type=o:width=2:g=0.5,"
            "extrastereo=m=1.1,"
            "aexciter=level_in=1:level_out=1:amount=0.8:drive=2:blend=0:freq=8000:ceil=20000,"
            "acompressor=threshold=0.05:ratio=3:attack=8:release=180:makeup=3.5,"
            "dynaudnorm=p=0.90:f=500:g=31:m=1.5"
        ),
    },
    "soundcard": {
        "label": "Soundcard", "icon": "🎚️",
        "desc": "By Xyrons2",
        "filter": (
            "volume=1.0,"
            "highpass=f=30,"
            "lowpass=f=20000,"
            "equalizer=f=50:width_type=o:width=2:g=1.8,"
            "equalizer=f=80:width_type=o:width=2:g=2.0,"
            "equalizer=f=120:width_type=o:width=2:g=1.2,"
            "equalizer=f=250:width_type=o:width=2:g=-1.5,"
            "equalizer=f=400:width_type=o:width=2:g=-1.0,"
            "equalizer=f=700:width_type=o:width=2:g=0.6,"
            "equalizer=f=1500:width_type=o:width=2:g=1.0,"
            "equalizer=f=3000:width_type=o:width=2:g=1.5,"
            "equalizer=f=5000:width_type=o:width=2:g=1.2,"
            "equalizer=f=8000:width_type=o:width=2:g=1.8,"
            "equalizer=f=12000:width_type=o:width=2:g=1.5,"
            "equalizer=f=16000:width_type=o:width=2:g=1.0,"
            "equalizer=f=18000:width_type=o:width=2:g=0.6,"
            "extrastereo=m=1.2,"
            "aexciter=level_in=1:level_out=1:amount=0.8:drive=3:blend=0:freq=6000:ceil=20000,"
            "acompressor=threshold=0.06:ratio=2.5:attack=5:release=150:makeup=3.5,"
            "dynaudnorm=p=0.91:f=500:g=31:m=1.5"
        ),
    },
    "normal": {
        "label": "Normal", "icon": "🎵",
        "desc": "By Xyrons2",
        "filter": (
            "volume=1.0,"
            "highpass=f=40,"
            "lowpass=f=18000,"
            "equalizer=f=80:width_type=o:width=2:g=1.2,"
            "equalizer=f=150:width_type=o:width=2:g=0.8,"
            "equalizer=f=400:width_type=o:width=2:g=-0.5,"
            "equalizer=f=2500:width_type=o:width=2:g=0.8,"
            "equalizer=f=8000:width_type=o:width=2:g=1.0,"
            "equalizer=f=12000:width_type=o:width=2:g=0.6,"
            "extrastereo=m=1.0,"
            "aexciter=level_in=1:level_out=1:amount=0.6:drive=1.5:blend=0:freq=8000:ceil=20000,"
            "acompressor=threshold=0.05:ratio=2.5:attack=10:release=220:makeup=2.5,"
            "dynaudnorm=p=0.90:f=500:g=31:m=1.5"
        ),
    },
    "harman": {
        "label": "Harman", "icon": "🎧",
        "desc": "By Xyrons2",
        "filter": (
            "volume=1.0,"
            "highpass=f=30,"
            "lowpass=f=20000,"
            "equalizer=f=60:width_type=o:width=2:g=2.0,"
            "equalizer=f=100:width_type=o:width=2:g=1.8,"
            "equalizer=f=300:width_type=o:width=2:g=-0.8,"
            "equalizer=f=1000:width_type=o:width=2:g=0.5,"
            "equalizer=f=3000:width_type=o:width=2:g=1.2,"
            "equalizer=f=7000:width_type=o:width=2:g=-0.3,"
            "equalizer=f=10000:width_type=o:width=2:g=0.8,"
            "equalizer=f=14000:width_type=o:width=2:g=0.6,"
            "extrastereo=m=1.1,"
            "aexciter=level_in=1:level_out=1:amount=0.7:drive=1.5:blend=0:freq=7000:ceil=20000,"
            "acompressor=threshold=0.05:ratio=2.5:attack=10:release=200:makeup=2.5,"
            "dynaudnorm=p=0.90:f=500:g=31:m=1.5"
        ),
    },
    "dolby": {
        "label": "Dolby", "icon": "🎬",
        "desc": "By Xyrons2",
        "filter": (
            "volume=1.0,"
            "highpass=f=30,"
            "lowpass=f=20000,"
            "equalizer=f=60:width_type=o:width=2:g=2.5,"
            "equalizer=f=120:width_type=o:width=2:g=1.8,"
            "equalizer=f=400:width_type=o:width=2:g=-0.8,"
            "equalizer=f=1000:width_type=o:width=2:g=0.8,"
            "equalizer=f=3000:width_type=o:width=2:g=1.2,"
            "equalizer=f=8000:width_type=o:width=2:g=1.2,"
            "equalizer=f=12000:width_type=o:width=2:g=1.0,"
            "equalizer=f=16000:width_type=o:width=2:g=0.6,"
            "extrastereo=m=1.2,"
            "aexciter=level_in=1:level_out=1:amount=0.8:drive=2:blend=0:freq=6000:ceil=20000,"
            "acompressor=threshold=0.05:ratio=3:attack=7:release=160:makeup=3,"
            "dynaudnorm=p=0.90:f=500:g=31:m=1.5"
        ),
    },
    "bassboost": {
        "label": "Bass Boost", "icon": "🔊",
        "desc": "By Xyrons2",
        "filter": (
            "volume=1.0,"
            "highpass=f=25,"
            "lowpass=f=20000,"
            "equalizer=f=40:width_type=o:width=2:g=3.5,"
            "equalizer=f=60:width_type=o:width=2:g=4.0,"
            "equalizer=f=100:width_type=o:width=2:g=3.0,"
            "equalizer=f=160:width_type=o:width=2:g=1.8,"
            "equalizer=f=300:width_type=o:width=2:g=-1.5,"
            "equalizer=f=500:width_type=o:width=2:g=-1.0,"
            "equalizer=f=2000:width_type=o:width=2:g=0.8,"
            "equalizer=f=4000:width_type=o:width=2:g=0.6,"
            "equalizer=f=8000:width_type=o:width=2:g=0.6,"
            "acompressor=threshold=0.04:ratio=3.5:attack=6:release=140:makeup=3.5,"
            "dynaudnorm=p=0.88:f=500:g=31:m=1.5"
        ),
    },
    "vocal": {
        "label": "Vocal", "icon": "🎤",
        "desc": "By Xyrons2",
        "filter": (
            "volume=1.0,"
            "highpass=f=80,"
            "lowpass=f=18000,"
            "equalizer=f=100:width_type=o:width=2:g=0.6,"
            "equalizer=f=300:width_type=o:width=2:g=-1.2,"
            "equalizer=f=1000:width_type=o:width=2:g=0.8,"
            "equalizer=f=2000:width_type=o:width=2:g=2.0,"
            "equalizer=f=3500:width_type=o:width=2:g=1.8,"
            "equalizer=f=5000:width_type=o:width=2:g=0.8,"
            "equalizer=f=8000:width_type=o:width=2:g=1.2,"
            "equalizer=f=12000:width_type=o:width=2:g=0.8,"
            "extrastereo=m=1.1,"
            "aexciter=level_in=1:level_out=1:amount=0.7:drive=1.5:blend=0:freq=3000:ceil=18000,"
            "acompressor=threshold=0.05:ratio=2.5:attack=10:release=220:makeup=2.5,"
            "dynaudnorm=p=0.90:f=500:g=31:m=1.5"
        ),
    },
    "lofi": {
        "label": "Lo-Fi", "icon": "📻",
        "desc": "By Xyrons2",
        "filter": (
            "volume=1.0,"
            "highpass=f=60,"
            "lowpass=f=9000,"
            "equalizer=f=80:width_type=o:width=2:g=1.8,"
            "equalizer=f=150:width_type=o:width=2:g=1.2,"
            "equalizer=f=500:width_type=o:width=2:g=-0.3,"
            "equalizer=f=3000:width_type=o:width=2:g=-0.8,"
            "equalizer=f=8000:width_type=o:width=2:g=-1.5,"
            "acompressor=threshold=0.06:ratio=2:attack=12:release=280:makeup=2,"
            "dynaudnorm=p=0.86:f=500:g=31:m=1.5"
        ),
    },
    "nightcore": {
        "label": "Nightcore", "icon": "⚡",
        "desc": "By Xyrons2",
        "filter": "volume=1.0,asetrate=48000*1.25,aresample=48000",
    },
    "8d": {
        "label": "8D Audio", "icon": "🌀",
        "desc": "By Xyrons2",
        "filter": "volume=1.0,apulsator=hz=0.08:width=0.7",
    },
    "vaporwave": {
        "label": "Vaporwave", "icon": "🌊",
        "desc": "By Xyrons2",
        "filter": "volume=1.0,asetrate=48000*0.82,aresample=48000,lowpass=f=8000",
    },
}
DEFAULT_PRESET = "hydra"

PRESET_CHOICES = [
    app_commands.Choice(name="🌊 Hydra (Best All-rounder)", value="hydra"),
    app_commands.Choice(name="🎚️ Soundcard (Analog Warm)",  value="soundcard"),
    app_commands.Choice(name="🎵 Normal",                   value="normal"),
    app_commands.Choice(name="🎧 Harman Target",            value="harman"),
    app_commands.Choice(name="🎬 Dolby Atmos",              value="dolby"),
    app_commands.Choice(name="🔊 Bass Boost",               value="bassboost"),
    app_commands.Choice(name="🎤 Vocal Boost",              value="vocal"),
    app_commands.Choice(name="📻 Lo-Fi",                    value="lofi"),
    app_commands.Choice(name="⚡ Nightcore",                 value="nightcore"),
    app_commands.Choice(name="🌀 8D Audio",                  value="8d"),
    app_commands.Choice(name="🌊 Vaporwave",                 value="vaporwave"),
]

EQ_GAIN = {-2: -4.0, -1: -2.0, 0: 0.0, 1: 2.5, 2: 5.0}

def build_eq_filter(state) -> str:
    parts = []
    b = EQ_GAIN[state.eq_bass]
    m = EQ_GAIN[state.eq_mid]
    t = EQ_GAIN[state.eq_treble]
    if b != 0.0:
        parts.append(f"equalizer=f=80:width_type=o:width=2:g={b}")
        parts.append(f"equalizer=f=120:width_type=o:width=2:g={round(b * 0.7, 1)}")
    if m != 0.0:
        parts.append(f"equalizer=f=1000:width_type=o:width=2:g={m}")
        parts.append(f"equalizer=f=2500:width_type=o:width=2:g={round(m * 0.8, 1)}")
    if t != 0.0:
        parts.append(f"equalizer=f=8000:width_type=o:width=2:g={t}")
        parts.append(f"equalizer=f=12000:width_type=o:width=2:g={round(t * 0.7, 1)}")
    return ",".join(parts)

def fmt_eq_bar(level: int) -> str:
    bars   = {-2: "▱▱▱▱▱", -1: "▰▱▱▱▱", 0: "▰▰▱▱▱", 1: "▰▰▰▱▱", 2: "▰▰▰▰▰"}
    labels = {-2: "-2", -1: "-1", 0: " 0", 1: "+1", 2: "+2"}
    return f"`{bars[level]}` `{labels[level]}`"

def build_ffmpeg_opts(preset_key: str, seek: float = 0.0, state=None) -> dict:
    af = PRESETS.get(preset_key, PRESETS[DEFAULT_PRESET])["filter"]
    af = re.sub(r"volume=[\d.]+", "volume=1.0", af)
    if state is not None:
        eq_extra = build_eq_filter(state)
        if eq_extra:
            if "acompressor" in af:
                af = af.replace("acompressor", eq_extra + ",acompressor", 1)
            else:
                af = af + "," + eq_extra
    before = (
        "-reconnect 1 -reconnect_streamed 1 "
        "-reconnect_delay_max 5 "
        "-probesize 32M -analyzeduration 10M"
    )
    if seek > 0:
        before += f" -ss {int(seek)}"
    
    # ── FIX #9: Ensure no duplicate -ac options ──
    if preset_key in ("nightcore", "vaporwave"):
        options = f'-vn -acodec libopus -b:a 128k -ac 2 -af "{af}"'
    else:
        options = f'-vn -acodec libopus -b:a 128k -ac 2 -ar 48000 -af "{af}"'
    return {"before_options": before, "options": options}

COOKIE_FILE = "cookies.txt"

def get_cookie_file():
    content = os.getenv("YOUTUBE_COOKIES")
    if not content:
        print("[ℹ️] YOUTUBE_COOKIES not set - using fallback")
        return None
    try:
        content = content.replace('\\n', '\n').replace('\\t', '\t')
        if ".youtube.com" not in content:
            print("[⚠️] Invalid cookies - no .youtube.com")
            return None
        if not content.startswith("#"):
            content = "# Netscape HTTP Cookie File\n" + content
        with open(COOKIE_FILE, 'w') as f:
            f.write(content)
        print("[✅] Cookies loaded from Railway env var")
        return COOKIE_FILE
    except Exception as e:
        print(f"[⚠️] Cookies error: {e}")
        return None

_cookie_file = get_cookie_file()

_BASE = {
    # ── FIX #12: Anti-bot detection + improved authentication ──
    "format": (
        "bestaudio[ext=m4a]/"
        "bestaudio[ext=webm]/"
        "bestaudio[ext=opus]/"
        "bestaudio/"
        "best[ext=mp4]/"
        "best[ext=webm]/"
        "best"
    ),
    "quiet": True,
    "no_warnings": True,
    "source_address": "0.0.0.0",
    "extractor_retries": 5,
    "socket_timeout": 30,
    "http_headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    },
    "skip_unavailable_fragments": True,
    "fragment_retries": 5,
    "file_access_retries": 3,
    "sleep_interval": 1,
    "max_sleep_interval": 5,
    "ignore_no_formats_error": False,
    "allow_unplayable_formats": True,
    "extractor_args": {
        "youtube": {
            "player_client": ["web", "tv_embedded"],  # web first untuk better auth support
            "player_skip": ["js", "configs"],
            "skip": ["hls"],
        }
    },
    **( {"cookiefile": _cookie_file} if _cookie_file else {} ),
}

YTDL_OPTS    = {**_BASE, "noplaylist": True,  "default_search": "ytsearch"}
YTDL_PL_OPTS = {**_BASE, "noplaylist": False, "default_search": "ytsearch", "extract_flat": "in_playlist", "skip_download": True}
YTDL_SC_OPTS = {**_BASE, "noplaylist": True,  "default_search": "scsearch"}

ytdl    = yt_dlp.YoutubeDL(YTDL_OPTS)
ytdl_pl = yt_dlp.YoutubeDL(YTDL_PL_OPTS)
ytdl_sc = yt_dlp.YoutubeDL(YTDL_SC_OPTS)

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states    = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)
guild_states: dict = {}

class GuildState:
    def __init__(self):
        self.eq_bass:      int        = 0
        self.eq_mid:       int        = 0
        self.eq_treble:    int        = 0
        self.queue:        deque      = deque()
        self.current:      dict|None  = None
        self.loop:         bool       = False
        self.loop_queue:   bool       = False
        self.volume:       float      = 1.0
        self.preset:       str        = DEFAULT_PRESET
        self.transformer:  discord.PCMVolumeTransformer|None = None
        self.force_replay: bool       = False
        self.autoplay:     bool       = False
        self.history:      list       = []
        self.seek_pos:     float      = 0.0
        self.play_start:   float      = 0.0
        self.vote_skip:    set        = set()
        self.np_message:   object     = None
        self.np_channel:   object     = None

def get_state(gid: int) -> GuildState:
    if gid not in guild_states:
        guild_states[gid] = GuildState()
    return guild_states[gid]

C_CYAN    = 0x22D3EE
C_CYAN2   = 0x06B6D4
C_ERROR   = 0xF87171
C_WARN    = 0xFBBF24
C_SUCCESS = 0x34D399
C_PURPLE  = 0xA78BFA

def fmt_dur(sec) -> str:
    if not sec: return "LIVE"
    m, s = divmod(int(sec), 60); h, m = divmod(m, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

def fmt_vol_bar(v: float) -> str:
    pct    = int(v * 100)
    filled = min(int(10 * v / 2), 10)
    bar    = "▰" * filled + "▱" * (10 - filled)
    return f"`{bar}` **{pct}%**"

def trunc(text: str, n: int = 45) -> str:
    return (text[:n] + "…") if len(text) > n else text

def mk_embed(title="", desc="", color=C_CYAN, thumb=None, fields=None, footer=None):
    e = discord.Embed(title=title, description=desc, color=color)
    if thumb: e.set_thumbnail(url=thumb)
    if fields:
        for n, v, i in fields: e.add_field(name=n, value=v, inline=i)
    e.set_footer(text=footer or "🎵 NEO MUSIC  ·  by Xyrons2")
    return e

def mk_now_playing(song: dict, state: GuildState, queue_len: int) -> discord.Embed:
    platform = song.get("platform", "youtube")
    p_icon   = PLATFORM_ICONS.get(platform, "🔴")
    p_name   = PLATFORM_NAMES.get(platform, "Unknown")
    preset   = PRESETS[state.preset]
    title    = trunc(song.get("title", "Unknown"), 40)
    url      = song.get("webpage_url", "")
    thumb    = song.get("thumbnail", "")
    dur      = song.get("duration", 0)
    uploader = trunc(song.get("uploader", song.get("artist", "Unknown")), 22)
    pct      = int(state.volume * 100)
    if state.loop:         loop_str = "🔂"
    elif state.loop_queue: loop_str = "🔁"
    else:                  loop_str = "➡️"
    elapsed = int(time.time() - state.play_start) if state.play_start else 0
    elapsed = max(0, min(elapsed, dur or elapsed))
    filled  = int(6 * elapsed / dur) if dur else 0
    bar     = "▰" * filled + "▱" * (6 - filled)
    e = discord.Embed(color=C_CYAN)
    e.set_author(name="◉  NOW PLAYING  ·  NEO MUSIC")
    e.description = (
        f"**[{title}]({url})**\n"
        f"-# 👤 {uploader}  ·  {p_icon} {p_name}\n"
        f"-# `{fmt_dur(elapsed)} {bar} {fmt_dur(dur)}`"
    )
    if thumb: e.set_thumbnail(url=thumb)
    ap = " `✨`" if state.autoplay else ""
    e.add_field(name="", value=f"`{preset['icon']}` `🔊{pct}%` `📋{queue_len}` `{loop_str}`{ap}", inline=False)
    e.set_footer(text=f"🎵 NEO MUSIC · Xyrons2  ·  {preset['label']} — {preset['desc']}")
    return e

class MusicView(discord.ui.View):
    def __init__(self, guild: discord.Guild, channel: discord.TextChannel):
        super().__init__(timeout=None)
        self.guild   = guild
        self.channel = channel

    def _state(self) -> GuildState:
        return get_state(self.guild.id)

    # ── FIX #2: Gunakan string emoji bukan PartialEmoji untuk unicode standard ──
    @discord.ui.button(emoji="⏸️", style=discord.ButtonStyle.primary, row=0)
    async def pause_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            button.emoji = "▶️"
            button.style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self)
        elif vc and vc.is_paused():
            vc.resume()
            button.emoji = "⏸️"
            button.style = discord.ButtonStyle.primary
            await interaction.response.edit_message(view=self)
        else:
            await interaction.response.send_message(embed=mk_embed(desc="> ❌ Tidak ada lagu.", color=C_ERROR), ephemeral=True)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary, row=0)
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
            await interaction.response.send_message(embed=mk_embed(desc="> ⏭ Diskip!", color=C_CYAN2), ephemeral=True)
        else:
            await interaction.response.send_message(embed=mk_embed(desc="> ❌ Tidak ada lagu.", color=C_ERROR), ephemeral=True)

    @discord.ui.button(emoji="⏹️", style=discord.ButtonStyle.danger, row=0)
    async def stop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self._state(); s.queue.clear(); s.current = None
        vc = self.guild.voice_client
        if vc: vc.stop()
        await interaction.response.send_message(embed=mk_embed(desc="> ⏹ Musik dihentikan.", color=C_ERROR), ephemeral=True)

    @discord.ui.button(emoji="🔁", style=discord.ButtonStyle.secondary, row=0)
    async def loop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self._state(); s.loop = not s.loop
        if s.loop: s.loop_queue = False
        button.style = discord.ButtonStyle.primary if s.loop else discord.ButtonStyle.secondary
        await interaction.response.edit_message(view=self)

    @discord.ui.button(emoji="🔉", style=discord.ButtonStyle.secondary, row=1)
    async def voldown_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self._state()
        newvol = max(0, int(s.volume * 100) - 10); s.volume = newvol / 100
        if s.transformer: s.transformer.volume = s.volume
        await interaction.response.send_message(embed=mk_embed(desc=f"> 🔉 Volume: **{newvol}%**", color=C_WARN), ephemeral=True)

    @discord.ui.button(emoji="🔊", style=discord.ButtonStyle.secondary, row=1)
    async def volup_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self._state()
        newvol = min(200, int(s.volume * 100) + 10); s.volume = newvol / 100
        if s.transformer: s.transformer.volume = s.volume
        await interaction.response.send_message(embed=mk_embed(desc=f"> 🔊 Volume: **{newvol}%**", color=C_SUCCESS), ephemeral=True)

    @discord.ui.button(emoji="🔀", style=discord.ButtonStyle.secondary, row=1)
    async def shuffle_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self._state()
        if len(s.queue) < 2:
            return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Queue terlalu sedikit.", color=C_WARN), ephemeral=True)
        q = list(s.queue); random.shuffle(q); s.queue = deque(q)
        await interaction.response.send_message(embed=mk_embed(desc=f"> 🔀 Queue diacak! **{len(q)} lagu**.", color=C_CYAN2), ephemeral=True)

    @discord.ui.button(emoji="📵", style=discord.ButtonStyle.danger, row=1)
    async def leave_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self._state(); s.queue.clear(); s.current = None
        cfg = get_247(self.guild.id); cfg["stay_in_channel"] = False; save_247(self.guild.id)
        vc = self.guild.voice_client
        if not vc:
            return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Bot tidak ada di VC.", color=C_ERROR), ephemeral=True)
        await vc.disconnect()
        await interaction.response.send_message(embed=mk_embed(desc="> 👋 Bot keluar dari VC.", color=C_PURPLE), ephemeral=True)

async def join_vc_ctx(ctx) -> bool:
    if not ctx.author.voice:
        await ctx.send(embed=mk_embed(desc="> ❌ Masuk ke voice channel dulu!", color=C_ERROR))
        return False
    ch = ctx.author.voice.channel
    if ctx.voice_client:
        if ctx.voice_client.channel != ch: await ctx.voice_client.move_to(ch)
    else:
        await ch.connect()
    return True

async def join_vc_inter(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.followup.send(embed=mk_embed(desc="> ❌ Masuk ke voice channel dulu!", color=C_ERROR), ephemeral=True)
        return None
    ch = interaction.user.voice.channel
    vc = interaction.guild.voice_client
    if vc:
        if vc.channel != ch: await vc.move_to(ch)
    else:
        vc = await ch.connect()
    return vc

async def resolve_spotify(url):
    if not sp: return []
    loop = asyncio.get_event_loop(); tracks = []
    try:
        if "/track/" in url:
            m = re.search(r"/track/([A-Za-z0-9]+)", url)
            if not m: return []
            t   = await loop.run_in_executor(None, lambda: sp.track(m.group(1)))
            art = ", ".join(a["name"] for a in t["artists"])
            thumb = t["album"]["images"][0]["url"] if t["album"]["images"] else ""
            tracks.append({"search": f"{t['name']} {art}", "title": t["name"], "artist": art,
                           "thumbnail": thumb, "duration": t["duration_ms"] // 1000, "platform": "spotify"})
        elif "/album/" in url:
            m = re.search(r"/album/([A-Za-z0-9]+)", url)
            if not m: return []
            al    = await loop.run_in_executor(None, lambda: sp.album(m.group(1)))
            thumb = al["images"][0]["url"] if al["images"] else ""
            for item in al["tracks"]["items"]:
                art = ", ".join(a["name"] for a in item["artists"])
                tracks.append({"search": f"{item['name']} {art}", "title": item["name"], "artist": art,
                               "thumbnail": thumb, "duration": item["duration_ms"] // 1000, "platform": "spotify"})
        elif "/playlist/" in url:
            m = re.search(r"/playlist/([A-Za-z0-9]+)", url)
            if not m: return []
            res   = await loop.run_in_executor(None, lambda: sp.playlist_tracks(m.group(1)))
            items = list(res["items"])
            while res["next"]:
                res = await loop.run_in_executor(None, lambda: sp.next(res))
                items.extend(res["items"])
            for item in items:
                t = item.get("track")
                if not t: continue
                art   = ", ".join(a["name"] for a in t["artists"])
                thumb = t["album"]["images"][0]["url"] if t["album"]["images"] else ""
                tracks.append({"search": f"{t['name']} {art}", "title": t["name"], "artist": art,
                               "thumbnail": thumb, "duration": t["duration_ms"] // 1000, "platform": "spotify"})
    except Exception as e: print(f"[Spotify] {e}")
    return tracks

async def resolve_apple_music(url):
    tracks = []
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=aiohttp.ClientTimeout(total=10)) as r:
                text = await r.text()
            tm = re.search(r'<meta property="og:title" content="([^"]+)"', text)
            dm = re.search(r'<meta property="og:description" content="([^"]+)"', text)
            im = re.search(r'<meta property="og:image" content="([^"]+)"', text)
            title  = html.unescape(tm.group(1)) if tm else "Unknown"
            artist = ""
            if dm:
                parts = [p.strip() for p in html.unescape(dm.group(1)).split("·")]
                if len(parts) >= 2: artist = parts[1]
            thumb = im.group(1) if im else ""
            if "/album/" in url or "/playlist/" in url:
                sq = title.split(" - ")[0] if " - " in title else title
                async with s.get(f"https://itunes.apple.com/search?term={sq}&entity=song&limit=50", timeout=aiohttp.ClientTimeout(total=8)) as r2:
                    data = await r2.json()
                for item in data.get("results", []):
                    tracks.append({"search": f"{item['trackName']} {item['artistName']}",
                                   "title": item["trackName"], "artist": item["artistName"],
                                   "thumbnail": item.get("artworkUrl100", "").replace("100x100", "500x500"),
                                   "duration": item.get("trackTimeMillis", 0) // 1000, "platform": "apple_music"})
            else:
                tracks.append({"search": f"{title} {artist}".strip(), "title": title, "artist": artist,
                               "thumbnail": thumb, "duration": 0, "platform": "apple_music"})
    except Exception as e: print(f"[Apple Music] {e}")
    return tracks

async def resolve_deezer(url):
    tracks = []
    try:
        m = re.search(r"deezer\.com/(?:[a-z]+/)?(track|album|playlist)/(\d+)", url)
        if not m: return []
        kind, did = m.group(1), m.group(2)
        async with aiohttp.ClientSession() as s:
            async with s.get(f"https://api.deezer.com/{kind}/{did}", timeout=aiohttp.ClientTimeout(total=10)) as r:
                data = await r.json()
        if kind == "track":
            art = data.get("artist", {}).get("name", "")
            tracks.append({"search": f"{data['title']} {art}", "title": data["title"], "artist": art,
                           "thumbnail": data.get("album", {}).get("cover_xl", ""),
                           "duration": data.get("duration", 0), "platform": "deezer"})
        elif kind in ("album", "playlist"):
            thumb = data.get("cover_xl", "")
            for t in data.get("tracks", {}).get("data", []):
                art = t.get("artist", {}).get("name", "")
                tracks.append({"search": f"{t['title']} {art}", "title": t["title"], "artist": art,
                               "thumbnail": t.get("album", {}).get("cover_xl", thumb),
                               "duration": t.get("duration", 0), "platform": "deezer"})
    except Exception as e: print(f"[Deezer] {e}")
    return tracks

async def resolve_yt_playlist(url: str) -> list:
    loop = asyncio.get_event_loop()
    try:
        data = await loop.run_in_executor(None, lambda: ytdl_pl.extract_info(url, download=False))
    except Exception as e:
        # ── FIX #11: Retry dengan format yang lebih permissive ──
        if "format" in str(e).lower():
            print(f"[resolve_yt_playlist] Format error, retrying with relaxed format...")
            try:
                fallback_opts = {**YTDL_PL_OPTS, "format": "best"}
                fallback_ytdl_pl = yt_dlp.YoutubeDL(fallback_opts)
                data = await loop.run_in_executor(None, lambda: fallback_ytdl_pl.extract_info(url, download=False))
            except Exception as fallback_err:
                raise RuntimeError(f"Gagal load playlist: {fallback_err}")
        else:
            raise RuntimeError(f"Gagal load playlist: {e}")
    
    songs = []
    for e in data.get("entries", []):
        if not e: continue
        wurl = e.get("url") or e.get("webpage_url") or f"https://www.youtube.com/watch?v={e.get('id','')}"
        songs.append({"_stub": True, "stub_url": wurl, "title": e.get("title", "Unknown"),
                      "duration": e.get("duration", 0), "thumbnail": e.get("thumbnail", ""),
                      "webpage_url": wurl, "platform": "youtube"})
    return songs

async def resolve_url(url: str):
    platform = detect_platform(url)
    if platform == "youtube" and is_yt_playlist(url):
        return "yt_playlist", await resolve_yt_playlist(url)
    if platform in YTDLP_NATIVE or platform == "ytdlp_fallback":
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL({**YTDL_OPTS, "noplaylist": False}).extract_info(url, download=False))
        except Exception as e:
            # ── FIX #11: Retry dengan format yang lebih permissive ──
            if "format" in str(e).lower():
                print(f"[resolve_url] Format error, retrying with relaxed format...")
                try:
                    fallback_opts = {**YTDL_OPTS, "noplaylist": False, "format": "best"}
                    data = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(fallback_opts).extract_info(url, download=False))
                except Exception as fallback_err:
                    raise RuntimeError(f"Gagal load URL (format tidak tersedia): {fallback_err}")
            else:
                raise RuntimeError(f"Gagal load URL: {e}")
        
        entries = data.get("entries", [data]); songs = []
        for e in entries:
            if not e: continue
            songs.append({"url": e.get("url", url), "title": e.get("title", "Unknown"),
                          "duration": e.get("duration", 0), "thumbnail": e.get("thumbnail", ""),
                          "webpage_url": e.get("webpage_url", url), "uploader": e.get("uploader", "Unknown"),
                          "platform": platform})
        return "direct", songs
    stubs = []
    if platform == "spotify":
        if not sp: raise RuntimeError("Spotify belum dikonfigurasi!")
        stubs = await resolve_spotify(url)
    elif platform == "apple_music": stubs = await resolve_apple_music(url)
    elif platform == "deezer":      stubs = await resolve_deezer(url)
    if not stubs: raise RuntimeError("Tidak bisa membaca konten dari URL ini.")
    return "stubs", stubs
    
async def search_youtube_v3(query: str, max_results: int = 5) -> list:
    """Cari video YouTube pakai API v3 — jauh lebih cepat dari yt-dlp ytsearch"""
    if not YOUTUBE_API_KEY:
        return []
    url = (
        f"https://www.googleapis.com/youtube/v3/search"
        f"?part=snippet&q={urllib.parse.quote(query)}"
        f"&type=video&maxResults={max_results}&key={YOUTUBE_API_KEY}"
    )
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=4)) as resp:
                data = await resp.json()
        results = []
        for item in data.get("items", []):
            vid_id  = item["id"]["videoId"]
            snippet = item["snippet"]
            results.append({
                "video_id":    vid_id,
                "title":       html.unescape(snippet["title"]),
                "uploader":    snippet["channelTitle"],
                "thumbnail":   snippet["thumbnails"].get("high", {}).get("url", ""),
                "webpage_url": f"https://www.youtube.com/watch?v={vid_id}",
                "duration":    0,  # API v3 tidak kasih durasi di search
            })
        return results
    except Exception as e:
        print(f"[API v3] {e}")
        return [] 

async def fetch_song(query: str, override: dict = None) -> dict:
    loop     = asyncio.get_event_loop()
    platform = override.get("platform", "youtube") if override else "youtube"

    # ── Gunakan YouTube API v3 untuk text search (lebih cepat) ──
    if not is_url(query) and YOUTUBE_API_KEY:
        try:
            results = await search_youtube_v3(query, max_results=1)
            if results:
                r         = results[0]
                video_url = r["webpage_url"]
                try:
                    data = await loop.run_in_executor(
                        None, lambda: ytdl.extract_info(video_url, download=False)
                    )
                except Exception as e:
                    # ── FIX #11: Retry dengan format yang lebih permissive ──
                    if "format" in str(e).lower():
                        print(f"[fetch_song API v3] Format error, retrying with relaxed format...")
                        fallback_opts = {**YTDL_OPTS, "format": "best"}
                        fallback_client = yt_dlp.YoutubeDL(fallback_opts)
                        data = await loop.run_in_executor(None, lambda: fallback_client.extract_info(video_url, download=False))
                    else:
                        raise
                
                result = {
                    "url":         data["url"],
                    "title":       override.get("title") or r["title"],
                    "duration":    data.get("duration", 0),
                    "thumbnail":   override.get("thumbnail") or r["thumbnail"],
                    "webpage_url": video_url,
                    "uploader":    override.get("artist") or r["uploader"],
                    "platform":    platform,
                }
                return result
        except Exception as e:
            print(f"[fetch_song API v3] {e} → fallback yt-dlp")

    # ── Fallback: yt-dlp search (kalau API v3 gagal / tidak ada key) ──
    last_err  = None
    searches  = (
        [(ytdl, query)] if is_url(query)
        else [(ytdl, f"ytsearch:{query}"), (ytdl_sc, f"scsearch:{query}")]
    )
    for client, search in searches:
        try:
            data = await loop.run_in_executor(
                None, lambda c=client, s=search: c.extract_info(s, download=False)
            )
            if "entries" in data: data = data["entries"][0]
            result = {
                "url":         data["url"],
                "title":       data.get("title", "Unknown"),
                "duration":    data.get("duration", 0),
                "thumbnail":   data.get("thumbnail", ""),
                "webpage_url": data.get("webpage_url", search),
                "uploader":    data.get("uploader", "Unknown"),
                "platform":    platform,
            }
            if override:
                for k in ("title", "thumbnail", "duration", "artist"):
                    if override.get(k): result[k] = override[k]
            return result
        except Exception as e:
            # ── FIX #11: Retry dengan format yang lebih permissive jika format error ──
            if "format" in str(e).lower() and is_url(query):
                try:
                    print(f"[fetch_song] Format error, retrying with relaxed format...")
                    fallback_opts = {**YTDL_OPTS, "format": "best"}
                    fallback_client = yt_dlp.YoutubeDL(fallback_opts)
                    data = await loop.run_in_executor(None, lambda: fallback_client.extract_info(query, download=False))
                    result = {
                        "url":         data["url"],
                        "title":       data.get("title", "Unknown"),
                        "duration":    data.get("duration", 0),
                        "thumbnail":   data.get("thumbnail", ""),
                        "webpage_url": data.get("webpage_url", query),
                        "uploader":    data.get("uploader", "Unknown"),
                        "platform":    platform,
                    }
                    if override:
                        for k in ("title", "thumbnail", "duration", "artist"):
                            if override.get(k): result[k] = override[k]
                    return result
                except Exception as fallback_err:
                    print(f"[fetch_song fallback] {fallback_err}")
                    last_err = fallback_err
            else:
                # ── FIX #12: Retry dengan web player client jika sign in/bot error ──
                error_str = str(e).lower()
                if ("sign in" in error_str or "bot" in error_str) and is_url(query):
                    try:
                        print(f"[fetch_song] Auth error, retrying dengan web player...")
                        auth_opts = {**YTDL_OPTS, "extractor_args": {
                            "youtube": {
                                "player_client": ["web"],
                                "player_skip": ["js", "configs"],
                                "skip": ["hls"],
                            }
                        }}
                        auth_client = yt_dlp.YoutubeDL(auth_opts)
                        data = await loop.run_in_executor(None, lambda: auth_client.extract_info(query, download=False))
                        if "entries" in data: data = data["entries"][0]
                        result = {
                            "url":         data["url"],
                            "title":       data.get("title", "Unknown"),
                            "duration":    data.get("duration", 0),
                            "thumbnail":   data.get("thumbnail", ""),
                            "webpage_url": data.get("webpage_url", query),
                            "uploader":    data.get("uploader", "Unknown"),
                            "platform":    platform,
                        }
                        if override:
                            for k in ("title", "thumbnail", "duration", "artist"):
                                if override.get(k): result[k] = override[k]
                        return result
                    except Exception as auth_fallback:
                        print(f"[fetch_song auth fallback] {auth_fallback}")
                        last_err = auth_fallback
                # ── FIX #13: Retry dengan delay jika page reload error (IP blocked) ──
                elif ("reload" in error_str or "refresh" in error_str) and is_url(query):
                    try:
                        print(f"[fetch_song] Page reload error (IP possibly blocked), waiting 10s before retry...")
                        await asyncio.sleep(10)  # Wait untuk IP reputation to cool down
                        
                        # Try dengan simpler config
                        reload_opts = {**YTDL_OPTS, "extractor_args": {
                            "youtube": {
                                "player_client": ["web"],
                                "player_skip": ["js", "configs", "get_signature_timestamp"],
                                "skip": ["hls", "dash"],
                            }
                        }}
                        reload_client = yt_dlp.YoutubeDL(reload_opts)
                        data = await loop.run_in_executor(None, lambda: reload_client.extract_info(query, download=False))
                        if "entries" in data: data = data["entries"][0]
                        result = {
                            "url":         data["url"],
                            "title":       data.get("title", "Unknown"),
                            "duration":    data.get("duration", 0),
                            "thumbnail":   data.get("thumbnail", ""),
                            "webpage_url": data.get("webpage_url", query),
                            "uploader":    data.get("uploader", "Unknown"),
                            "platform":    platform,
                        }
                        if override:
                            for k in ("title", "thumbnail", "duration", "artist"):
                                if override.get(k): result[k] = override[k]
                        return result
                    except Exception as reload_fallback:
                        print(f"[fetch_song reload fallback] IP blocked - YouTube rate limiting active. {reload_fallback}")
                        last_err = reload_fallback
                else:
                    print(f"[fetch_song] {search} → {e}")
                    last_err = e
    raise RuntimeError(f"Lagu tidak ditemukan: {last_err}")

async def play_next(channel: discord.TextChannel, guild: discord.Guild):
    state = get_state(guild.id)
    vc    = guild.voice_client

    if state.force_replay and state.current:
        song = state.current; state.force_replay = False
    elif state.loop and state.current:
        song = state.current
    elif state.queue:
        song = state.queue.popleft()
        if state.loop_queue: state.queue.append(song)
        state.current = song
    else:
        if state.autoplay and state.current:
            last = state.current
            queries = [f"{last.get('uploader', '')} mix", f"{last.get('title', '')} mix playlist"]
            try:
                song = await fetch_song(random.choice(queries))
                if song.get("webpage_url") == last.get("webpage_url"):
                    song = await fetch_song(f"{last.get('uploader', '')} top songs")
                state.queue.append(song)
                await play_next(channel, guild); return
            except Exception: pass
        state.current = None; state.transformer = None
        cfg      = get_247(guild.id)
        stay_msg = "\n> 🔴 **24/7 ON** — Bot tetap di VC." if cfg["stay_in_channel"] else ""
        await channel.send(embed=mk_embed(desc=f"> ✅ Semua lagu selesai!{stay_msg}\n> Gunakan `!play` atau `/play` untuk lanjut.", color=C_PURPLE))
        return

    if song.get("_stub"):
        try:
            song = await fetch_song(song["stub_url"]); state.current = song
        except Exception as e:
            await channel.send(embed=mk_embed(desc=f"> ⚠️ Skip — gagal load: `{e}`", color=C_WARN))
            return await play_next(channel, guild)

    state.history.append(song)
    if len(state.history) > 20: state.history.pop(0)

    opts        = build_ffmpeg_opts(state.preset, seek=state.seek_pos, state=state)
    raw_source  = discord.FFmpegPCMAudio(song["url"], executable=FFMPEG_PATH, **opts)
    transformer = discord.PCMVolumeTransformer(raw_source, volume=state.volume)
    state.transformer = transformer
    state.play_start  = time.time() - state.seek_pos
    state.seek_pos    = 0.0
    state.vote_skip   = set()

    # ── FIX #3: after() callback dengan error handling yang proper ──
    def after(err):
        if err: print(f"[Playback Error] {err}")
        asyncio.run_coroutine_threadsafe(play_next(channel, guild), bot.loop)

    vc.play(transformer, after=after)
    embed  = mk_now_playing(song, state, len(state.queue))
    view   = MusicView(guild=guild, channel=channel)
    np_msg = await channel.send(embed=embed, view=view)
    state.np_message = np_msg
    state.np_channel = channel

async def _do_play(channel, guild, vc, state, query, loading_msg=None):
    platform = detect_platform(query) if is_url(query) else "search"
    p_icon   = PLATFORM_ICONS.get(platform, "🎵")
    p_name   = PLATFORM_NAMES.get(platform, "Web")

    async def _edit(embed):
        if loading_msg:
            try: await loading_msg.edit(embed=embed)
            except Exception: await channel.send(embed=embed)
        else: await channel.send(embed=embed)

    async def _delete():
        if loading_msg:
            try: await loading_msg.delete()
            except Exception: pass

    try:
        if is_url(query):
            mode, items = await resolve_url(query)
            if mode == "yt_playlist":
                for song in items: state.queue.append(song)
                await _edit(mk_embed(title=f"📋 YouTube Playlist · {len(items)} lagu",
                    desc=f"> **{len(items)} lagu** ditambahkan ke queue!", color=C_CYAN2,
                    fields=[("🎛 Preset", f"{PRESETS[state.preset]['icon']} {PRESETS[state.preset]['label']}", True),
                            ("🔊 Volume", f"{int(state.volume * 100)}%", True)]))
            elif mode == "direct":
                for song in items: state.queue.append(song)
                if len(items) == 1:
                    s = items[0]
                    if vc.is_playing() or vc.is_paused():
                        await _edit(mk_embed(title="➕ Ditambahkan ke Queue",
                            desc=f"> **[{trunc(s['title'])}]({s['webpage_url']})**",
                            thumb=s["thumbnail"], color=C_CYAN2,
                            fields=[("⏱ Durasi", f"`{fmt_dur(s['duration'])}`", True),
                                    ("🌐 Platform", f"{p_icon} {p_name}", True),
                                    ("📊 Posisi", f"**#{len(state.queue)}**", True)]))
                    else: await _delete()
                else:
                    await _edit(mk_embed(title=f"📋 {p_icon} {p_name} · {len(items)} lagu",
                        desc=f"> **{len(items)} lagu** ditambahkan!", color=C_CYAN2))
            else:
                await _edit(mk_embed(desc=f"> {p_icon} **{len(items)} lagu** ditemukan\n> Mencari audio...", color=C_CYAN2))
                added, failed = 0, 0
                for stub in items:
                    try: song = await fetch_song(stub["search"], override=stub); state.queue.append(song); added += 1
                    except Exception: failed += 1
                note = f" `({failed} gagal)`" if failed else ""
                await _edit(mk_embed(title=f"✅ {p_icon} {p_name} · {added} lagu{note}",
                    desc=f"> **{added} lagu** siap diputar!", color=C_SUCCESS,
                    fields=[("🎛", f"{PRESETS[state.preset]['icon']} {PRESETS[state.preset]['label']}", True),
                            ("🔊", f"{int(state.volume * 100)}%", True)]))
        else:
            song = await fetch_song(query)
            state.queue.append(song)
            if vc.is_playing() or vc.is_paused():
                await _edit(mk_embed(title="➕ Ditambahkan ke Queue",
                    desc=f"> **[{trunc(song['title'])}]({song['webpage_url']})**",
                    thumb=song["thumbnail"], color=C_CYAN2,
                    fields=[("⏱ Durasi", f"`{fmt_dur(song['duration'])}`", True),
                            ("📊 Posisi", f"**#{len(state.queue)}**", True)]))
            else: await _delete()
        return True
    except Exception as e:
        print(f"[PLAY ERROR] {traceback.format_exc()}")
        await _edit(mk_embed(desc=f"> ❌ `{str(e) or type(e).__name__}`", color=C_ERROR))
        return False

# ══════════════════════════════════════════════════════════
#  PLAYLIST SYSTEM
# ══════════════════════════════════════════════════════════
PL_FILE = "playlists.json"

def load_playlists() -> dict:
    if os.path.exists(PL_FILE):
        try:
            with open(PL_FILE) as f: return json.load(f)
        except Exception: pass
    return {}

def save_playlists():
    try:
        with open(PL_FILE, "w") as f: json.dump(all_playlists, f, indent=2)
    except Exception as e: print(f"[Playlist] {e}")

all_playlists = load_playlists()

def get_guild_pl(guild_id: int) -> dict:
    gid = str(guild_id)
    if gid not in all_playlists: all_playlists[gid] = {}
    return all_playlists[gid]

# ══════════════════════════════════════════════════════════
#  PREFIX COMMANDS
# ══════════════════════════════════════════════════════════
@bot.command(name="play", aliases=["p"])
async def play(ctx, *, query: str):
    if not await join_vc_ctx(ctx): return
    state = get_state(ctx.guild.id)
    msg   = await ctx.send(embed=mk_embed(desc=f"> ⏳ Memuat **{trunc(query, 80)}**...", color=C_CYAN2))
    ok    = await _do_play(ctx.channel, ctx.guild, ctx.voice_client, state, query, msg)
    if ok and not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        await play_next(ctx.channel, ctx.guild)

@bot.command(name="search", aliases=["find"])
async def search_cmd(ctx, *, query: str):
    msg  = await ctx.send(embed=mk_embed(desc=f"> 🔍 Mencari `{query}`...", color=C_CYAN2))
    loop = asyncio.get_event_loop()
    try:
        # Coba API v3 dulu (cepat), fallback ke yt-dlp
        entries = await search_youtube_v3(query, max_results=5)
        if not entries:
            data    = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch5:{query}", download=False))
            entries = [{"title": e.get("title",""), "webpage_url": e.get("webpage_url",""),
                        "duration": e.get("duration", 0)} for e in data.get("entries", [])]
        if not entries: return await msg.edit(embed=mk_embed(desc="> ❌ Tidak ada hasil.", color=C_ERROR))
        lines = [f"`{i+1}.` [{trunc(e['title'], 50)}]({e.get('webpage_url','')}) `{fmt_dur(e.get('duration',0))}`" for i, e in enumerate(entries)]
        await msg.edit(embed=mk_embed(title=f"🔍 {query}", desc="\n".join(lines), color=C_CYAN, fields=[("💬 Pilih", "Balas angka 1–5", False)]))
        def check(m): return m.author == ctx.author and m.channel == ctx.channel and m.content.isdigit()
        try:
            reply = await bot.wait_for("message", timeout=30.0, check=check)
            idx   = int(reply.content) - 1
            if 0 <= idx < len(entries):
                e = entries[idx]
                if not await join_vc_ctx(ctx): return
                state   = get_state(ctx.guild.id)
                loading = await ctx.send(embed=mk_embed(desc="> ⏳ Memuat...", color=C_CYAN2))
                song    = await fetch_song(e.get("webpage_url", e["title"]))
                state.queue.append(song); await loading.delete()
                if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
                    await play_next(ctx.channel, ctx.guild)
                else:
                    await ctx.send(embed=mk_embed(title="➕ Ditambahkan ke Queue",
                        desc=f"> **[{trunc(song['title'])}]({song['webpage_url']})**",
                        thumb=song["thumbnail"], color=C_CYAN2))
        except asyncio.TimeoutError:
            await msg.edit(embed=mk_embed(desc="> ⏰ Timeout. Pencarian dibatalkan.", color=C_WARN))
    except Exception as ex:
        await msg.edit(embed=mk_embed(desc=f"> ❌ `{str(ex)}`", color=C_ERROR))

@bot.command(name="skip", aliases=["s"])
async def skip(ctx):
    vc = ctx.voice_client
    if not vc or (not vc.is_playing() and not vc.is_paused()):
        return await ctx.send(embed=mk_embed(desc="> ❌ Tidak ada lagu.", color=C_ERROR))
    vc.stop()
    await ctx.send(embed=mk_embed(desc="> ⏭ Diskip!", color=C_CYAN2))

@bot.command(name="pause")
async def pause(ctx):
    vc = ctx.voice_client
    if vc and vc.is_playing(): vc.pause(); await ctx.send(embed=mk_embed(desc="> ⏸ Di-pause.", color=C_WARN))
    else: await ctx.send(embed=mk_embed(desc="> ❌ Tidak ada lagu.", color=C_ERROR))

@bot.command(name="resume", aliases=["r"])
async def resume(ctx):
    vc = ctx.voice_client
    if vc and vc.is_paused(): vc.resume(); await ctx.send(embed=mk_embed(desc="> ▶️ Dilanjutkan!", color=C_SUCCESS))
    else: await ctx.send(embed=mk_embed(desc="> ❌ Tidak di-pause.", color=C_ERROR))

@bot.command(name="stop")
async def stop(ctx):
    s = get_state(ctx.guild.id); s.queue.clear(); s.current = None
    if ctx.voice_client: ctx.voice_client.stop()
    await ctx.send(embed=mk_embed(desc="> ⏹ Musik dihentikan.", color=C_ERROR))

@bot.command(name="nowplaying", aliases=["np"])
async def nowplaying(ctx):
    s = get_state(ctx.guild.id)
    if not s.current: return await ctx.send(embed=mk_embed(desc="> ❌ Tidak ada lagu.", color=C_ERROR))
    view = MusicView(guild=ctx.guild, channel=ctx.channel)
    await ctx.send(embed=mk_now_playing(s.current, s, len(s.queue)), view=view)

@bot.command(name="queue", aliases=["q"])
async def queue_cmd(ctx, page: int = 1):
    s = get_state(ctx.guild.id)
    if not s.queue and not s.current:
        return await ctx.send(embed=mk_embed(desc="> 📋 Queue kosong. Gunakan `!play` untuk mulai!", color=C_CYAN2))
    items = list(s.queue); per = 10
    total = max(1, (len(items) + per - 1) // per)
    page  = max(1, min(page, total)); st = (page - 1) * per
    lines = []
    if s.current:
        lines.append(f"**▶ Now**  [{trunc(s.current['title'], 40)}]({s.current['webpage_url']})  `{fmt_dur(s.current['duration'])}`\n")
    for i, song in enumerate(items[st:st + per], start=st + 1):
        p_dot = PLATFORM_ICONS.get(song.get("platform", "youtube"), "🔴")
        lines.append(f"`{i:02d}`  {p_dot}  [{trunc(song['title'], 40)}]({song['webpage_url']})  `{fmt_dur(song['duration'])}`")
    total_dur = sum(x.get("duration", 0) for x in items)
    await ctx.send(embed=mk_embed(title=f"📋 Queue  ·  Hal {page}/{total}", desc="\n".join(lines) or "_Kosong_", color=C_CYAN2,
        fields=[("🎵 Total", f"**{len(items)} lagu**", True), ("⏱ Durasi", f"`{fmt_dur(total_dur)}`", True),
                ("🎛 Preset", f"{PRESETS[s.preset]['icon']} {PRESETS[s.preset]['label']}", True),
                ("🔊 Volume", f"**{int(s.volume * 100)}%**", True)]))

@bot.command(name="volume", aliases=["vol", "v"])
async def volume_cmd(ctx, vol: int):
    s = get_state(ctx.guild.id)
    if not 0 <= vol <= 200: return await ctx.send(embed=mk_embed(desc="> ❌ Range: **0–200%**", color=C_ERROR))
    s.volume = vol / 100
    if s.transformer: s.transformer.volume = s.volume
    warn = "\n> ⚠️ Di atas 100% bisa distorsi!" if vol > 100 else ""
    await ctx.send(embed=mk_embed(desc=f"> 🔊 Volume: {fmt_vol_bar(s.volume)}{warn}", color=C_CYAN))

@bot.command(name="volup", aliases=["vu"])
async def volup(ctx, step: int = 10):
    s = get_state(ctx.guild.id)
    newvol = min(200, int(s.volume * 100) + step); s.volume = newvol / 100
    if s.transformer: s.transformer.volume = s.volume
    await ctx.send(embed=mk_embed(desc=f"> 🔊 Volume: {fmt_vol_bar(s.volume)}", color=C_CYAN))

@bot.command(name="voldown", aliases=["vd"])
async def voldown(ctx, step: int = 10):
    s = get_state(ctx.guild.id)
    newvol = max(0, int(s.volume * 100) - step); s.volume = newvol / 100
    if s.transformer: s.transformer.volume = s.volume
    await ctx.send(embed=mk_embed(desc=f"> 🔉 Volume: {fmt_vol_bar(s.volume)}", color=C_CYAN2))

@bot.command(name="preset", aliases=["audio"])
async def preset_cmd(ctx, name: str = None):
    state = get_state(ctx.guild.id)
    if not name or name.lower() not in PRESETS:
        lines = [f"{'▶' if k == state.preset else '◦'}  `!preset {k}`  —  **{v['icon']} {v['label']}**  {v['desc']}" for k, v in PRESETS.items()]
        return await ctx.send(embed=mk_embed(title="🎛 Audio Presets", desc="\n".join(lines), color=C_CYAN))
    state.preset = name.lower(); p = PRESETS[state.preset]
    vc = ctx.voice_client
    if vc and (vc.is_playing() or vc.is_paused()):
        state.seek_pos = time.time() - state.play_start
        state.force_replay = True; vc.stop()
        await ctx.send(embed=mk_embed(desc=f"> 🎛 **{p['icon']} {p['label']}** aktif!\n> _{p['desc']}_", color=C_CYAN))
    else:
        await ctx.send(embed=mk_embed(desc=f"> 🎛 **{p['icon']} {p['label']}**\n> {p['desc']}", color=C_CYAN))

@bot.command(name="loop", aliases=["l"])
async def loop_cmd(ctx):
    s = get_state(ctx.guild.id); s.loop = not s.loop
    if s.loop: s.loop_queue = False
    await ctx.send(embed=mk_embed(desc=f"> 🔂 Loop: **{'✅ Aktif' if s.loop else '❌ Off'}**", color=C_CYAN))

@bot.command(name="shuffle")
async def shuffle(ctx):
    s = get_state(ctx.guild.id)
    if len(s.queue) < 2: return await ctx.send(embed=mk_embed(desc="> ❌ Queue terlalu sedikit.", color=C_ERROR))
    q = list(s.queue); random.shuffle(q); s.queue = deque(q)
    await ctx.send(embed=mk_embed(desc=f"> 🔀 Queue diacak! **{len(q)} lagu**.", color=C_CYAN))

@bot.command(name="remove")
async def remove(ctx, index: int):
    s = get_state(ctx.guild.id)
    if index < 1 or index > len(s.queue): return await ctx.send(embed=mk_embed(desc="> ❌ Index tidak valid.", color=C_ERROR))
    q = list(s.queue); removed = q.pop(index - 1); s.queue = deque(q)
    await ctx.send(embed=mk_embed(desc=f"> 🗑 **{trunc(removed['title'])}** dihapus.", color=C_ERROR))

@bot.command(name="clear")
async def clear_queue(ctx):
    get_state(ctx.guild.id).queue.clear()
    await ctx.send(embed=mk_embed(desc="> 🗑 Queue dikosongkan.", color=C_ERROR))

@bot.command(name="move")
async def move(ctx, fr: int, to: int):
    s = get_state(ctx.guild.id)
    if not (1 <= fr <= len(s.queue) and 1 <= to <= len(s.queue)):
        return await ctx.send(embed=mk_embed(desc="> ❌ Index tidak valid.", color=C_ERROR))
    q = list(s.queue); song = q.pop(fr - 1); q.insert(to - 1, song); s.queue = deque(q)
    await ctx.send(embed=mk_embed(desc=f"> ↕️ **{trunc(song['title'])}** → #{to}", color=C_CYAN))

@bot.command(name="playnext")
async def playnext(ctx, *, query: str):
    if not await join_vc_ctx(ctx): return
    state = get_state(ctx.guild.id)
    msg   = await ctx.send(embed=mk_embed(desc="> ⏳ Memuat ke depan queue...", color=C_CYAN2))
    try:
        song = await fetch_song(query)
        state.queue.appendleft(song)
        e = discord.Embed(color=0xF97316)
        e.set_author(name="⏩  PLAY NEXT  ·  NEO MUSIC")
        e.description = f"**{trunc(song['title'])}**\n-# {PLATFORM_ICONS.get(song.get('platform','youtube'),'🔴')} YouTube  ·  `{fmt_dur(song['duration'])}`  ·  Disisipkan ke depan queue"
        if song.get("thumbnail"): e.set_thumbnail(url=song["thumbnail"])
        e.set_footer(text="🎵 NEO MUSIC · by Xyrons2")
        await msg.edit(embed=e)
        if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            await play_next(ctx.channel, ctx.guild)
    except Exception as e:
        await msg.edit(embed=mk_embed(desc=f"> ❌ `{str(e)}`", color=C_ERROR))

# ── FIX #4: skipto prefix — deque(q[index-1:]) bukan q[index:] ──
@bot.command(name="skipto")
async def skipto(ctx, index: int):
    s = get_state(ctx.guild.id)
    if index < 1 or index > len(s.queue):
        return await ctx.send(embed=mk_embed(desc="> ❌ Index tidak valid.", color=C_ERROR))
    q = list(s.queue)
    song = q[index - 1]
    s.queue = deque(q[index - 1:])  # FIX: include lagu yang dipilih di queue
    vc = ctx.voice_client
    if vc and (vc.is_playing() or vc.is_paused()): vc.stop()
    e = discord.Embed(color=0xF97316)
    e.set_author(name=f"⏩  SKIP TO #{index}  ·  NEO MUSIC")
    e.description = f"**{trunc(song['title'])}**\n-# {index-1} lagu di-skip  ·  Melanjutkan dari #{index}"
    if song.get("thumbnail"): e.set_thumbnail(url=song["thumbnail"])
    e.set_footer(text="🎵 NEO MUSIC · by Xyrons2")
    await ctx.send(embed=e)

@bot.command(name="history")
async def history(ctx):
    s = get_state(ctx.guild.id)
    if not s.history: return await ctx.send(embed=mk_embed(desc="> 🕐 Belum ada lagu yang diputar.", color=C_CYAN2))
    shown = s.history[-20:]; lines = []; total_dur = 0
    for i, song in enumerate(shown, 1):
        dur = song.get("duration", 0); total_dur += dur
        lines.append(f"`{i:02d}`  {PLATFORM_ICONS.get(song.get('platform','youtube'),'🔴')}  [{trunc(song['title'], 38)}]({song['webpage_url']})  `{fmt_dur(dur)}`")
    e = discord.Embed(color=C_CYAN)
    e.set_author(name=f"🕐  HISTORY — {len(shown)} LAGU TERAKHIR")
    e.description = "\n".join(lines)
    e.set_footer(text=f"🎵 NEO MUSIC · by Xyrons2  ·  Total: {fmt_dur(total_dur)}")
    await ctx.send(embed=e)

@bot.command(name="autoplay")
async def autoplay_cmd(ctx):
    s = get_state(ctx.guild.id); s.autoplay = not s.autoplay
    based_on = s.current.get("uploader", s.current.get("title", "Unknown")) if s.autoplay and s.current else None
    e = discord.Embed(color=C_SUCCESS if s.autoplay else C_WARN)
    if s.autoplay:
        e.set_author(name="✨  AUTOPLAY — ON  ·  NEO MUSIC"); e.description = "Lagu terkait otomatis saat queue habis"
        if based_on: e.add_field(name="", value=f"`🔍 Based on: {based_on}`  `✨ Aktif`", inline=False)
    else:
        e.set_author(name="✨  AUTOPLAY — OFF  ·  NEO MUSIC"); e.description = "Autoplay dimatikan."
    e.set_footer(text="🎵 NEO MUSIC · by Xyrons2")
    await ctx.send(embed=e)

@bot.command(name="ping")
async def ping(ctx):
    t0  = time.perf_counter()
    msg = await ctx.send(embed=mk_embed(desc="> 📡 Mengukur latency...", color=C_CYAN2))
    api = round((time.perf_counter() - t0) * 1000); ws = round(bot.latency * 1000)
    status_dot  = "🟢" if ws < 100 else "🟡" if ws < 200 else "🔴"
    status_text = "OPTIMAL" if ws < 100 else "NORMAL" if ws < 200 else "TINGGI"
    e = discord.Embed(color=C_CYAN); e.set_author(name="📡  LATENCY  ·  NEO MUSIC")
    e.add_field(name=f"`{ws}ms`\nWEBSOCKET", value="", inline=True)
    e.add_field(name=f"`{api}ms`\nAPI ROUND", value="", inline=True)
    e.add_field(name=f"{status_dot}\nSTATUS",  value="", inline=True)
    e.set_footer(text=f"🎵 NEO MUSIC · by Xyrons2  ·  {status_text}")
    await msg.edit(embed=e)

@bot.command(name="uptime")
async def uptime(ctx):
    elapsed = int(time.time() - BOT_START_TIME)
    days,  rem = divmod(elapsed, 86400); hours, rem = divmod(rem, 3600); minutes, _ = divmod(rem, 60)
    e = discord.Embed(color=C_CYAN); e.set_author(name="🕐  UPTIME  ·  NEO MUSIC")
    e.add_field(name=f"`{days}`\nHARI", value="", inline=True)
    e.add_field(name=f"`{hours}`\nJAM", value="", inline=True)
    e.add_field(name=f"`{minutes}`\nMENIT", value="", inline=True)
    e.set_footer(text="🎵 NEO MUSIC · by Xyrons2")
    await ctx.send(embed=e)

@bot.command(name="seek")
async def seek_cmd(ctx, pos: str):
    s = get_state(ctx.guild.id)
    if not s.current: return await ctx.send(embed=mk_embed(desc="> ❌ Tidak ada lagu.", color=C_ERROR))
    vc = ctx.voice_client
    if not vc or (not vc.is_playing() and not vc.is_paused()):
        return await ctx.send(embed=mk_embed(desc="> ❌ Bot tidak sedang memutar.", color=C_ERROR))
    try:
        if ":" in pos:
            parts = pos.split(":"); secs = int(parts[-1]) + int(parts[-2]) * 60
            if len(parts) == 3: secs += int(parts[0]) * 3600
        else: secs = int(pos)
    except ValueError:
        return await ctx.send(embed=mk_embed(desc="> ❌ Format: `!seek 1:30` atau `!seek 90`", color=C_ERROR))
    dur = s.current.get("duration", 0)
    if dur and secs >= dur: return await ctx.send(embed=mk_embed(desc=f"> ❌ Durasi lagu: `{fmt_dur(dur)}`", color=C_ERROR))
    s.seek_pos = float(secs); s.force_replay = True; vc.stop()
    await ctx.send(embed=mk_embed(desc=f"> ⏩ Loncat ke `{fmt_dur(secs)}`", color=C_CYAN))

@bot.command(name="replay", aliases=["restart"])
async def replay_cmd(ctx):
    s = get_state(ctx.guild.id)
    if not s.current: return await ctx.send(embed=mk_embed(desc="> ❌ Tidak ada lagu.", color=C_ERROR))
    vc = ctx.voice_client
    if not vc or (not vc.is_playing() and not vc.is_paused()):
        return await ctx.send(embed=mk_embed(desc="> ❌ Bot tidak sedang memutar.", color=C_ERROR))
    s.seek_pos = 0.0; s.force_replay = True; vc.stop()
    await ctx.send(embed=mk_embed(desc=f"> 🔄 Ulangi dari awal: **{trunc(s.current['title'])}**", color=C_CYAN))

@bot.command(name="voteskip", aliases=["vs"])
async def voteskip_cmd(ctx):
    s = get_state(ctx.guild.id); vc = ctx.voice_client
    if not vc or (not vc.is_playing() and not vc.is_paused()):
        return await ctx.send(embed=mk_embed(desc="> ❌ Tidak ada lagu.", color=C_ERROR))
    members = [m for m in vc.channel.members if not m.bot]
    needed  = max(1, int(len(members) * VOTESKIP_RATIO + 0.5))
    if ctx.author.id in s.vote_skip:
        return await ctx.send(embed=mk_embed(desc=f"> ℹ️ Kamu sudah vote! **{len(s.vote_skip)}/{needed}** vote.", color=C_WARN))
    s.vote_skip.add(ctx.author.id)
    if len(s.vote_skip) >= needed:
        vc.stop(); s.vote_skip.clear()
        await ctx.send(embed=mk_embed(desc=f"> ⏭ **Vote skip berhasil!** ({needed}/{needed})\n> Lagu diskip!", color=C_SUCCESS))
    else:
        await ctx.send(embed=mk_embed(desc=f"> 🗳 Vote skip: **{len(s.vote_skip)}/{needed}**\n> Butuh **{needed - len(s.vote_skip)}** vote lagi.", color=C_CYAN2))

@bot.command(name="save")
async def save_cmd(ctx, *, pl_name: str):
    s = get_state(ctx.guild.id)
    if not s.current: return await ctx.send(embed=mk_embed(desc="> ❌ Tidak ada lagu yang diputar.", color=C_ERROR))
    pls = get_guild_pl(ctx.guild.id)
    if pl_name.lower() not in pls:
        return await ctx.send(embed=mk_embed(desc=f"> ❌ Playlist **{pl_name}** tidak ditemukan.\n> Buat dulu: `!playlist create {pl_name}`", color=C_ERROR))
    songs = pls[pl_name.lower()]
    if len(songs) >= 200: return await ctx.send(embed=mk_embed(desc="> ❌ Playlist penuh (max 200).", color=C_ERROR))
    song = s.current
    if any(x.get("webpage_url") == song.get("webpage_url") for x in songs):
        return await ctx.send(embed=mk_embed(desc=f"> ℹ️ **{trunc(song['title'])}** sudah ada di **{pl_name}**.", color=C_WARN))
    songs.append({"title": song["title"], "url": song.get("webpage_url", ""), "duration": song.get("duration", 0),
                  "thumbnail": song.get("thumbnail", ""), "uploader": song.get("uploader", "Unknown"),
                  "webpage_url": song.get("webpage_url", ""), "platform": song.get("platform", "youtube")})
    save_playlists()
    e = discord.Embed(color=C_SUCCESS); e.set_author(name=f"💾  DISIMPAN  ·  {pl_name.upper()}")
    e.description = f"**[{trunc(song['title'])}]({song.get('webpage_url','')})**\n-# 📁 {pl_name}  ·  #{len(songs)}"
    if song.get("thumbnail"): e.set_thumbnail(url=song["thumbnail"])
    e.set_footer(text="🎵 NEO MUSIC · by Xyrons2")
    await ctx.send(embed=e)

@bot.command(name="request")
async def request_cmd(ctx, channel: discord.TextChannel = None):
    if channel is None:
        ch_id = get_request_ch(ctx.guild.id)
        if ch_id:
            ch = ctx.guild.get_channel(ch_id)
            return await ctx.send(embed=mk_embed(desc=f"> 📬 Request channel: {ch.mention if ch else f'<#{ch_id}>'}", color=C_CYAN))
        return await ctx.send(embed=mk_embed(desc="> ❌ Belum ada request channel.\n> Set: `!request #channel`", color=C_WARN))
    request_channels[str(ctx.guild.id)] = channel.id; save_request(request_channels)
    await ctx.send(embed=mk_embed(desc=f"> 📬 Request channel diset ke {channel.mention}!\n> Member bisa ketik nama lagu di sana untuk request.", color=C_SUCCESS))

@bot.command(name="requestoff")
async def request_off(ctx):
    if str(ctx.guild.id) in request_channels: del request_channels[str(ctx.guild.id)]; save_request(request_channels)
    await ctx.send(embed=mk_embed(desc="> 📬 Request channel dinonaktifkan.", color=C_WARN))

@bot.command(name="loopqueue", aliases=["lq"])
async def loopqueue(ctx):
    s = get_state(ctx.guild.id); s.loop_queue = not s.loop_queue
    if s.loop_queue: s.loop = False
    status = "🟢 **ON** — Semua lagu akan diulang terus." if s.loop_queue else "🔴 **OFF**"
    e = discord.Embed(color=C_CYAN if s.loop_queue else C_CYAN2)
    e.set_author(name="🔁  LOOP QUEUE  ·  NEO MUSIC"); e.description = f"> {status}"
    if s.loop_queue and s.queue: e.add_field(name="📋 Queue", value=f"`{len(s.queue)} lagu` akan diulang", inline=True)
    e.set_footer(text="🎵 NEO MUSIC · by Xyrons2  ·  !loop untuk loop 1 lagu")
    await ctx.send(embed=e)

@bot.command(name="leave", aliases=["dc", "disconnect"])
async def leave(ctx):
    s = get_state(ctx.guild.id); s.queue.clear(); s.current = None
    cfg = get_247(ctx.guild.id); cfg["stay_in_channel"] = False; save_247(ctx.guild.id)
    if ctx.voice_client: await ctx.voice_client.disconnect()
    await ctx.send(embed=mk_embed(desc="> 👋 Bot keluar dari VC. 24/7 stay dimatikan.", color=C_PURPLE))

@bot.command(name="help")
async def help_cmd(ctx):
    await ctx.send(
        "**🎵 NEO MUSIC — Command List**\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "**▶️ Playback**\n"
        "`!play <lagu/url>` — Putar lagu\n"
        "`!search <lagu>` — Cari & pilih dari 5 hasil\n"
        "`!pause` — Pause lagu\n"
        "`!resume` — Lanjutkan lagu\n"
        "`!skip` — Skip lagu\n"
        "`!stop` — Stop & kosongkan queue\n"
        "`!nowplaying` — Info lagu sekarang\n"
        "`!seek <waktu>` — Loncat ke waktu tertentu\n"
        "`!replay` — Ulangi dari awal\n"
        "`!leave` — Bot keluar VC\n\n"
        "**📋 Queue**\n"
        "`!queue` — Lihat antrian lagu\n"
        "`!playnext <lagu>` — Sisipkan ke depan queue\n"
        "`!skipto <no>` — Loncat ke nomor antrian\n"
        "`!remove <no>` — Hapus lagu dari queue\n"
        "`!move <dari> <ke>` — Pindah urutan lagu\n"
        "`!clear` — Kosongkan queue\n"
        "`!shuffle` — Acak urutan queue\n"
        "`!loop` — Loop lagu ini\n"
        "`!loopqueue` — Loop semua queue\n\n"
        "**🔊 Volume**\n"
        "`!volume <0-200>` — Set volume\n"
        "`!volup` — Naikkan volume +10%\n"
        "`!voldown` — Turunkan volume -10%\n\n"
        "**🎛 Preset EQ**\n"
        "`!preset hydra` — 🌊 Warm smooth all-rounder\n"
        "`!preset harman` — 🎧 EQ premium audiophile\n"
        "`!preset dolby` — 🎬 Cinematic surround\n"
        "`!preset bassboost` — 🔊 Sub-bass tebal\n"
        "`!preset vocal` — 🎤 Vokal jernih\n"
        "`!preset lofi` — 📻 Warm vintage chill\n"
        "`!preset nightcore` — ⚡ Pitch naik + cepat\n"
        "`!preset 8d` — 🌀 Audio 360° berputar\n"
        "`!preset vaporwave` — 🌊 Slow dreamy 80s\n"
        "`!preset normal` — 🎵 Bersih tanpa EQ\n\n"
        "**🎵 Fitur Lain**\n"
        "`!history` — 20 lagu terakhir diputar\n"
        "`!autoplay` — Auto lagu terkait saat queue habis\n"
        "`!voteskip` — Vote skip lagu\n"
        "`!eq` — Panel EQ interaktif Bass/Mid/Treble\n"
        "`!ping` — Cek latency bot\n"
        "`!uptime` — Lama bot nyala\n\n"
        "**📁 Playlist**\n"
        "`!save <nama>` — Simpan lagu sekarang ke playlist\n\n"
        "**📡 24/7**\n"
        "`!247 bind` — Set VC target\n"
        "`!247 stay` — Bot tetap di VC walau queue habis\n"
        "`!247 auto` — Auto join saat bot restart\n"
        "`!247 status` — Lihat status 24/7\n"
        "`!247 reset` — Reset semua pengaturan 24/7"
    )

# ══════════════════════════════════════════════════════════
#  AUTOCOMPLETE
# ══════════════════════════════════════════════════════════
async def play_autocomplete(interaction: discord.Interaction, current: str):
    if not current or len(current) < 2:
        return []
    try:
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            return []
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={urllib.parse.quote(current)}&type=video&maxResults=5&key={api_key}"
        async with aiohttp.ClientSession() as session:
            # ── timeout 1.5s agar tidak expired sebelum Discord menerima ──
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=1.5)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
        return [
            app_commands.Choice(
                name=trunc(item["snippet"]["title"], 100),
                value=f"https://youtube.com/watch?v={item['id']['videoId']}"
            )
            for item in data.get("items", [])
        ][:5]
    except Exception:
        return []

async def playlist_name_autocomplete(interaction: discord.Interaction, current: str):
    pls = get_guild_pl(interaction.guild.id)
    return [
        app_commands.Choice(name=name, value=name)
        for name in pls.keys()
        if current.lower() in name.lower()
    ][:25]

# ══════════════════════════════════════════════════════════
#  SLASH COMMANDS
# ══════════════════════════════════════════════════════════
@bot.tree.command(name="play", description="▶️ Putar lagu — YouTube, Spotify, SoundCloud, dll")
@app_commands.describe(query="Nama lagu atau URL")
@app_commands.autocomplete(query=play_autocomplete)
async def slash_play(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    vc = await join_vc_inter(interaction)
    if not vc: return
    state = get_state(interaction.guild.id)
    msg = await interaction.followup.send(embed=mk_embed(desc=f"> ⏳ Memuat **{trunc(query, 80)}**...", color=C_CYAN2))
    ok = await _do_play(interaction.channel, interaction.guild, vc, state, query, msg)
    if ok and not vc.is_playing() and not vc.is_paused():
        await play_next(interaction.channel, interaction.guild)

@bot.tree.command(name="search", description="🔍 Cari lagu dan pilih dari 5 hasil")
@app_commands.describe(query="Nama lagu yang dicari")
async def slash_search(interaction: discord.Interaction, query: str):
    await interaction.response.send_message(embed=mk_embed(desc=f"> 🔍 Mencari `{query}`...", color=C_CYAN2))
    msg = await interaction.original_response(); loop = asyncio.get_event_loop()
    try:
        entries = await search_youtube_v3(query, max_results=5)
        if not entries:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch5:{query}", download=False))
            entries = [{"title": e.get("title",""), "webpage_url": e.get("webpage_url",""),
                        "duration": e.get("duration", 0)} for e in data.get("entries", [])]
        if not entries: return await msg.edit(embed=mk_embed(desc="> ❌ Tidak ada hasil.", color=C_ERROR))
        lines = [f"`{i+1}.` [{trunc(e['title'], 50)}]({e.get('webpage_url','')}) `{fmt_dur(e.get('duration',0))}`" for i, e in enumerate(entries)]
        await msg.edit(embed=mk_embed(title=f"🔍 {query}", desc="\n".join(lines), color=C_CYAN, fields=[("💬 Pilih", "Balas angka 1–5 di chat", False)]))
        def check(m): return m.author == interaction.user and m.channel == interaction.channel and m.content.isdigit()
        try:
            reply = await bot.wait_for("message", timeout=30.0, check=check); idx = int(reply.content) - 1
            if 0 <= idx < len(entries):
                e = entries[idx]; vc = await join_vc_inter(interaction)
                if not vc: return
                state = get_state(interaction.guild.id)
                loading = await interaction.channel.send(embed=mk_embed(desc="> ⏳ Memuat...", color=C_CYAN2))
                song = await fetch_song(e.get("webpage_url", e["title"])); state.queue.append(song); await loading.delete()
                if not vc.is_playing() and not vc.is_paused(): await play_next(interaction.channel, interaction.guild)
                else: await interaction.channel.send(embed=mk_embed(title="➕ Ditambahkan ke Queue",
                        desc=f"> **[{trunc(song['title'])}]({song['webpage_url']})**", thumb=song["thumbnail"], color=C_CYAN2))
        except asyncio.TimeoutError: await msg.edit(embed=mk_embed(desc="> ⏰ Timeout. Dibatalkan.", color=C_WARN))
    except Exception as ex: await msg.edit(embed=mk_embed(desc=f"> ❌ `{str(ex)}`", color=C_ERROR))

@bot.tree.command(name="skip", description="⏭️ Skip lagu yang sedang diputar")
async def slash_skip(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if not vc or (not vc.is_playing() and not vc.is_paused()):
        return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Tidak ada lagu.", color=C_ERROR), ephemeral=True)
    vc.stop(); await interaction.response.send_message(embed=mk_embed(desc="> ⏭ Diskip!", color=C_CYAN2))

@bot.tree.command(name="pause", description="⏸️ Pause lagu")
async def slash_pause(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_playing(): vc.pause(); await interaction.response.send_message(embed=mk_embed(desc="> ⏸ Di-pause.", color=C_WARN))
    else: await interaction.response.send_message(embed=mk_embed(desc="> ❌ Tidak ada lagu.", color=C_ERROR), ephemeral=True)

@bot.tree.command(name="resume", description="▶️ Lanjutkan lagu yang di-pause")
async def slash_resume(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc and vc.is_paused(): vc.resume(); await interaction.response.send_message(embed=mk_embed(desc="> ▶️ Dilanjutkan!", color=C_SUCCESS))
    else: await interaction.response.send_message(embed=mk_embed(desc="> ❌ Tidak di-pause.", color=C_ERROR), ephemeral=True)

@bot.tree.command(name="stop", description="⏹️ Stop musik dan kosongkan queue")
async def slash_stop(interaction: discord.Interaction):
    s = get_state(interaction.guild.id); s.queue.clear(); s.current = None
    vc = interaction.guild.voice_client
    if vc: vc.stop()
    await interaction.response.send_message(embed=mk_embed(desc="> ⏹ Musik dihentikan.", color=C_ERROR))

@bot.tree.command(name="nowplaying", description="🎵 Info lagu yang sedang diputar")
async def slash_nowplaying(interaction: discord.Interaction):
    s = get_state(interaction.guild.id)
    if not s.current: return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Tidak ada lagu.", color=C_ERROR), ephemeral=True)
    view = MusicView(guild=interaction.guild, channel=interaction.channel)
    await interaction.response.send_message(embed=mk_now_playing(s.current, s, len(s.queue)), view=view)

@bot.tree.command(name="queue", description="📋 Lihat antrian lagu")
@app_commands.describe(page="Nomor halaman")
async def slash_queue(interaction: discord.Interaction, page: int = 1):
    s = get_state(interaction.guild.id)
    if not s.queue and not s.current:
        return await interaction.response.send_message(embed=mk_embed(desc="> 📋 Queue kosong.", color=C_CYAN2), ephemeral=True)
    items = list(s.queue); per = 10
    total = max(1, (len(items) + per - 1) // per); page = max(1, min(page, total)); st = (page - 1) * per
    lines = []
    if s.current: lines.append(f"**▶ Now**  [{trunc(s.current['title'], 40)}]({s.current['webpage_url']})  `{fmt_dur(s.current['duration'])}`\n")
    for i, song in enumerate(items[st:st + per], start=st + 1):
        lines.append(f"`{i:02d}`  {PLATFORM_ICONS.get(song.get('platform','youtube'),'🔴')}  [{trunc(song['title'], 40)}]({song['webpage_url']})  `{fmt_dur(song['duration'])}`")
    total_dur = sum(x.get("duration", 0) for x in items)
    await interaction.response.send_message(embed=mk_embed(title=f"📋 Queue  ·  Hal {page}/{total}", desc="\n".join(lines) or "_Kosong_", color=C_CYAN2,
        fields=[("🎵 Total", f"**{len(items)} lagu**", True), ("⏱", f"`{fmt_dur(total_dur)}`", True),
                ("🎛", f"{PRESETS[s.preset]['icon']} {PRESETS[s.preset]['label']}", True), ("🔊", f"**{int(s.volume * 100)}%**", True)]))

@bot.tree.command(name="volume", description="🔊 Atur volume (0–200%)")
@app_commands.describe(vol="Volume dalam persen")
async def slash_volume(interaction: discord.Interaction, vol: int):
    s = get_state(interaction.guild.id)
    if not 0 <= vol <= 200: return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Range: **0–200%**", color=C_ERROR), ephemeral=True)
    s.volume = vol / 100
    if s.transformer: s.transformer.volume = s.volume
    warn = "\n> ⚠️ Di atas 100% bisa distorsi!" if vol > 100 else ""
    await interaction.response.send_message(embed=mk_embed(desc=f"> 🔊 Volume: {fmt_vol_bar(s.volume)}{warn}", color=C_CYAN))

@bot.tree.command(name="volup", description="🔊 Naikkan volume (+10%)")
@app_commands.describe(step="Jumlah kenaikan (default 10)")
async def slash_volup(interaction: discord.Interaction, step: int = 10):
    s = get_state(interaction.guild.id)
    newvol = min(200, int(s.volume * 100) + step); s.volume = newvol / 100
    if s.transformer: s.transformer.volume = s.volume
    await interaction.response.send_message(embed=mk_embed(desc=f"> 🔊 Volume: {fmt_vol_bar(s.volume)}", color=C_CYAN))

@bot.tree.command(name="voldown", description="🔉 Turunkan volume (-10%)")
@app_commands.describe(step="Jumlah penurunan (default 10)")
async def slash_voldown(interaction: discord.Interaction, step: int = 10):
    s = get_state(interaction.guild.id)
    newvol = max(0, int(s.volume * 100) - step); s.volume = newvol / 100
    if s.transformer: s.transformer.volume = s.volume
    await interaction.response.send_message(embed=mk_embed(desc=f"> 🔉 Volume: {fmt_vol_bar(s.volume)}", color=C_CYAN2))

@bot.tree.command(name="preset", description="🎛️ Ganti preset EQ — ada dropdown pilihan!")
@app_commands.describe(name="Pilih preset audio")
@app_commands.choices(name=PRESET_CHOICES)
async def slash_preset(interaction: discord.Interaction, name: str):
    state = get_state(interaction.guild.id); state.preset = name; p = PRESETS[name]
    vc = interaction.guild.voice_client
    if vc and (vc.is_playing() or vc.is_paused()):
        state.seek_pos = time.time() - state.play_start
        state.force_replay = True; vc.stop()
        await interaction.response.send_message(embed=mk_embed(desc=f"> 🎛 **{p['icon']} {p['label']}** aktif!\n> _{p['desc']}_", color=C_CYAN))
    else:
        await interaction.response.send_message(embed=mk_embed(desc=f"> 🎛 **{p['icon']} {p['label']}**\n> {p['desc']}", color=C_CYAN))

@bot.tree.command(name="loop", description="🔂 Toggle loop lagu saat ini")
async def slash_loop(interaction: discord.Interaction):
    s = get_state(interaction.guild.id); s.loop = not s.loop
    if s.loop: s.loop_queue = False
    await interaction.response.send_message(embed=mk_embed(desc=f"> 🔂 Loop: **{'✅ Aktif' if s.loop else '❌ Off'}**", color=C_CYAN))

@bot.tree.command(name="loopqueue", description="🔁 Toggle loop seluruh queue")
async def slash_loopqueue(interaction: discord.Interaction):
    s = get_state(interaction.guild.id); s.loop_queue = not s.loop_queue
    if s.loop_queue: s.loop = False
    await interaction.response.send_message(embed=mk_embed(desc=f"> 🔁 Loop Queue: **{'✅ Aktif' if s.loop_queue else '❌ Off'}**", color=C_CYAN))

@bot.tree.command(name="shuffle", description="🔀 Acak urutan queue")
async def slash_shuffle(interaction: discord.Interaction):
    s = get_state(interaction.guild.id)
    if len(s.queue) < 2: return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Queue terlalu sedikit.", color=C_ERROR), ephemeral=True)
    q = list(s.queue); random.shuffle(q); s.queue = deque(q)
    await interaction.response.send_message(embed=mk_embed(desc=f"> 🔀 Queue diacak! **{len(q)} lagu**.", color=C_CYAN))

@bot.tree.command(name="remove", description="🗑️ Hapus lagu dari queue")
@app_commands.describe(index="Nomor urut di queue")
async def slash_remove(interaction: discord.Interaction, index: int):
    s = get_state(interaction.guild.id)
    if index < 1 or index > len(s.queue): return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Index tidak valid.", color=C_ERROR), ephemeral=True)
    q = list(s.queue); removed = q.pop(index - 1); s.queue = deque(q)
    await interaction.response.send_message(embed=mk_embed(desc=f"> 🗑 **{trunc(removed['title'])}** dihapus.", color=C_ERROR))

@bot.tree.command(name="clear", description="🗑️ Kosongkan semua queue")
async def slash_clear(interaction: discord.Interaction):
    get_state(interaction.guild.id).queue.clear()
    await interaction.response.send_message(embed=mk_embed(desc="> 🗑 Queue dikosongkan.", color=C_ERROR))

@bot.tree.command(name="move", description="↕️ Pindahkan lagu di queue")
@app_commands.describe(fr="Nomor urut asal", to="Nomor urut tujuan")
async def slash_move(interaction: discord.Interaction, fr: int, to: int):
    s = get_state(interaction.guild.id)
    if not (1 <= fr <= len(s.queue) and 1 <= to <= len(s.queue)):
        return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Index tidak valid.", color=C_ERROR), ephemeral=True)
    q = list(s.queue); song = q.pop(fr - 1); q.insert(to - 1, song); s.queue = deque(q)
    await interaction.response.send_message(embed=mk_embed(desc=f"> ↕️ **{trunc(song['title'])}** → #{to}", color=C_CYAN))

@bot.tree.command(name="playnext", description="⏩ Sisipkan lagu ke depan queue")
@app_commands.describe(query="Nama lagu atau URL")
@app_commands.autocomplete(query=play_autocomplete)
async def slash_playnext(interaction: discord.Interaction, query: str):
    await interaction.response.defer()
    vc = await join_vc_inter(interaction)
    if not vc: return
    state = get_state(interaction.guild.id)
    msg = await interaction.followup.send(embed=mk_embed(desc="> ⏳ Memuat ke depan queue...", color=C_CYAN2))
    try:
        song = await fetch_song(query); state.queue.appendleft(song)
        e = discord.Embed(color=C_CYAN); e.set_author(name="⏩  PLAY NEXT  ·  NEO MUSIC")
        e.description = f"**{trunc(song['title'])}**\n-# {PLATFORM_ICONS.get(song.get('platform','youtube'),'🔴')} YouTube  ·  `{fmt_dur(song['duration'])}`  ·  Disisipkan ke depan queue"
        if song.get("thumbnail"): e.set_thumbnail(url=song["thumbnail"])
        e.set_footer(text="🎵 NEO MUSIC · by Xyrons2")
        await msg.edit(embed=e)
        if not vc.is_playing() and not vc.is_paused(): await play_next(interaction.channel, interaction.guild)
    except Exception as ex:
        await msg.edit(embed=mk_embed(desc=f"> ❌ `{str(ex)}`", color=C_ERROR))

# ── FIX #5: skipto slash — deque(q[index-1:]) bukan q[index:] ──
@bot.tree.command(name="skipto", description="⏩ Loncat ke nomor lagu di queue")
@app_commands.describe(index="Nomor urut di queue")
async def slash_skipto(interaction: discord.Interaction, index: int):
    s = get_state(interaction.guild.id)
    if index < 1 or index > len(s.queue):
        return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Index tidak valid.", color=C_ERROR), ephemeral=True)
    q = list(s.queue)
    song = q[index - 1]
    s.queue = deque(q[index - 1:])  # FIX: include lagu yang dipilih
    vc = interaction.guild.voice_client
    if vc and (vc.is_playing() or vc.is_paused()): vc.stop()
    e = discord.Embed(color=C_CYAN); e.set_author(name=f"⏩  SKIP TO #{index}  ·  NEO MUSIC")
    e.description = f"**{trunc(song['title'])}**\n-# {index-1} lagu di-skip  ·  Melanjutkan dari #{index}"
    if song.get("thumbnail"): e.set_thumbnail(url=song["thumbnail"])
    e.set_footer(text="🎵 NEO MUSIC · by Xyrons2")
    await interaction.response.send_message(embed=e)

@bot.tree.command(name="history", description="🕐 20 lagu terakhir yang diputar")
async def slash_history(interaction: discord.Interaction):
    s = get_state(interaction.guild.id)
    if not s.history: return await interaction.response.send_message(embed=mk_embed(desc="> 🕐 Belum ada lagu yang diputar.", color=C_CYAN2), ephemeral=True)
    shown = s.history[-20:]; lines = []; total_dur = 0
    for i, song in enumerate(shown, 1):
        dur = song.get("duration", 0); total_dur += dur
        lines.append(f"`{i:02d}`  {PLATFORM_ICONS.get(song.get('platform','youtube'),'🔴')}  [{trunc(song['title'], 38)}]({song['webpage_url']})  `{fmt_dur(dur)}`")
    e = discord.Embed(color=C_CYAN); e.set_author(name=f"🕐  HISTORY — {len(shown)} LAGU TERAKHIR")
    e.description = "\n".join(lines)
    e.set_footer(text=f"🎵 NEO MUSIC · by Xyrons2  ·  Total: {fmt_dur(total_dur)}")
    await interaction.response.send_message(embed=e)

@bot.tree.command(name="autoplay", description="✨ Toggle autoplay lagu terkait saat queue habis")
async def slash_autoplay(interaction: discord.Interaction):
    s = get_state(interaction.guild.id); s.autoplay = not s.autoplay
    based_on = s.current.get("uploader", s.current.get("title", "Unknown")) if s.autoplay and s.current else None
    e = discord.Embed(color=C_SUCCESS if s.autoplay else C_WARN)
    if s.autoplay:
        e.set_author(name="✨  AUTOPLAY — ON  ·  NEO MUSIC"); e.description = "Lagu terkait otomatis saat queue habis"
        if based_on: e.add_field(name="", value=f"`🔍 Based on: {based_on}`  `✨ Aktif`", inline=False)
    else:
        e.set_author(name="✨  AUTOPLAY — OFF  ·  NEO MUSIC"); e.description = "Autoplay dimatikan."
    e.set_footer(text="🎵 NEO MUSIC · by Xyrons2")
    await interaction.response.send_message(embed=e)

# ── FIX #6: Slash commands yang ada di /help tapi belum dibuat ──
@bot.tree.command(name="seek", description="⏩ Loncat ke waktu tertentu dalam lagu")
@app_commands.describe(pos="Waktu tujuan, contoh: 1:30 atau 90 (detik)")
async def slash_seek(interaction: discord.Interaction, pos: str):
    s = get_state(interaction.guild.id)
    if not s.current:
        return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Tidak ada lagu.", color=C_ERROR), ephemeral=True)
    vc = interaction.guild.voice_client
    if not vc or (not vc.is_playing() and not vc.is_paused()):
        return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Bot tidak sedang memutar.", color=C_ERROR), ephemeral=True)
    try:
        if ":" in pos:
            parts = pos.split(":"); secs = int(parts[-1]) + int(parts[-2]) * 60
            if len(parts) == 3: secs += int(parts[0]) * 3600
        else: secs = int(pos)
    except ValueError:
        return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Format: `1:30` atau `90` (detik)", color=C_ERROR), ephemeral=True)
    dur = s.current.get("duration", 0)
    if dur and secs >= dur:
        return await interaction.response.send_message(embed=mk_embed(desc=f"> ❌ Durasi lagu: `{fmt_dur(dur)}`", color=C_ERROR), ephemeral=True)
    s.seek_pos = float(secs); s.force_replay = True; vc.stop()
    await interaction.response.send_message(embed=mk_embed(desc=f"> ⏩ Loncat ke `{fmt_dur(secs)}`", color=C_CYAN))

@bot.tree.command(name="replay", description="🔄 Ulangi lagu dari awal")
async def slash_replay(interaction: discord.Interaction):
    s = get_state(interaction.guild.id)
    if not s.current:
        return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Tidak ada lagu.", color=C_ERROR), ephemeral=True)
    vc = interaction.guild.voice_client
    if not vc or (not vc.is_playing() and not vc.is_paused()):
        return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Bot tidak sedang memutar.", color=C_ERROR), ephemeral=True)
    s.seek_pos = 0.0; s.force_replay = True; vc.stop()
    await interaction.response.send_message(embed=mk_embed(desc=f"> 🔄 Ulangi dari awal: **{trunc(s.current['title'])}**", color=C_CYAN))

@bot.tree.command(name="voteskip", description="🗳️ Vote skip lagu yang sedang diputar")
async def slash_voteskip(interaction: discord.Interaction):
    s = get_state(interaction.guild.id); vc = interaction.guild.voice_client
    if not vc or (not vc.is_playing() and not vc.is_paused()):
        return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Tidak ada lagu.", color=C_ERROR), ephemeral=True)
    members = [m for m in vc.channel.members if not m.bot]
    needed  = max(1, int(len(members) * VOTESKIP_RATIO + 0.5))
    if interaction.user.id in s.vote_skip:
        return await interaction.response.send_message(embed=mk_embed(desc=f"> ℹ️ Kamu sudah vote! **{len(s.vote_skip)}/{needed}** vote.", color=C_WARN), ephemeral=True)
    s.vote_skip.add(interaction.user.id)
    if len(s.vote_skip) >= needed:
        vc.stop(); s.vote_skip.clear()
        await interaction.response.send_message(embed=mk_embed(desc=f"> ⏭ **Vote skip berhasil!** ({needed}/{needed})\n> Lagu diskip!", color=C_SUCCESS))
    else:
        await interaction.response.send_message(embed=mk_embed(desc=f"> 🗳 Vote skip: **{len(s.vote_skip)}/{needed}**\n> Butuh **{needed - len(s.vote_skip)}** vote lagi.", color=C_CYAN2))

@bot.tree.command(name="ping", description="🏓 Cek latency bot")
async def slash_ping(interaction: discord.Interaction):
    t0 = time.perf_counter()
    await interaction.response.send_message(embed=mk_embed(desc="> 📡 Mengukur latency...", color=C_CYAN2))
    api = round((time.perf_counter() - t0) * 1000); ws = round(bot.latency * 1000)
    status_dot = "🟢" if ws < 100 else "🟡" if ws < 200 else "🔴"
    status_text = "OPTIMAL" if ws < 100 else "NORMAL" if ws < 200 else "TINGGI"
    e = discord.Embed(color=C_CYAN); e.set_author(name="📡  LATENCY  ·  NEO MUSIC")
    e.add_field(name=f"`{ws}ms`\nWEBSOCKET", value="", inline=True)
    e.add_field(name=f"`{api}ms`\nAPI ROUND", value="", inline=True)
    e.add_field(name=f"{status_dot}\nSTATUS",  value="", inline=True)
    e.set_footer(text=f"🎵 NEO MUSIC · by Xyrons2  ·  {status_text}")
    msg = await interaction.original_response(); await msg.edit(embed=e)

@bot.tree.command(name="uptime", description="⏱ Sudah berapa lama bot nyala")
async def slash_uptime(interaction: discord.Interaction):
    elapsed = int(time.time() - BOT_START_TIME)
    days, rem = divmod(elapsed, 86400); hours, rem = divmod(rem, 3600); minutes, _ = divmod(rem, 60)
    e = discord.Embed(color=C_CYAN); e.set_author(name="⏱  UPTIME  ·  NEO MUSIC")
    e.add_field(name=f"`{days}`\nHARI", value="", inline=True)
    e.add_field(name=f"`{hours}`\nJAM", value="", inline=True)
    e.add_field(name=f"`{minutes}`\nMENIT", value="", inline=True)
    e.set_footer(text="🎵 NEO MUSIC · by Xyrons2")
    await interaction.response.send_message(embed=e)

@bot.tree.command(name="leave", description="👋 Keluarkan bot dari VC")
async def slash_leave(interaction: discord.Interaction):
    s = get_state(interaction.guild.id); s.queue.clear(); s.current = None
    cfg = get_247(interaction.guild.id); cfg["stay_in_channel"] = False; save_247(interaction.guild.id)
    vc = interaction.guild.voice_client
    if vc: await vc.disconnect()
    await interaction.response.send_message(embed=mk_embed(desc="> 👋 Bot keluar dari VC.", color=C_PURPLE))

@bot.tree.command(name="disconnect", description="🔌 Disconnect bot dari voice channel")
async def slash_disconnect(interaction: discord.Interaction):
    s = get_state(interaction.guild.id); s.queue.clear(); s.current = None
    cfg = get_247(interaction.guild.id); cfg["stay_in_channel"] = False; save_247(interaction.guild.id)
    vc = interaction.guild.voice_client
    if not vc: return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Bot tidak ada di VC.", color=C_ERROR), ephemeral=True)
    ch_name = vc.channel.name; await vc.disconnect()
    await interaction.response.send_message(embed=mk_embed(desc=f"> 🔌 Disconnect dari **{ch_name}**. Queue dikosongkan.", color=C_PURPLE))

@bot.tree.command(name="help", description="❓ Lihat semua command NEO MUSIC")
async def slash_help(interaction: discord.Interaction):
    s = get_state(interaction.guild.id); p = PRESETS[s.preset]; cfg = get_247(interaction.guild.id)
    e = discord.Embed(title="🎵 NEO MUSIC — Command List", description="Prefix `!`  ·  Slash `/`  ·  by **Xyrons2**", color=C_CYAN)
    e.add_field(name="▶️ Playback", value=(
        "`/play <lagu/url>` — Putar lagu\n"
        "`/search <lagu>` — Cari & pilih dari 5 hasil\n"
        "`/pause` · `/resume` · `/skip` · `/stop`\n"
        "`/nowplaying` — Info lagu sekarang\n"
        "`/seek <waktu>` — Loncat ke waktu tertentu\n"
        "`/replay` — Ulangi dari awal\n"
        "`/leave` — Bot keluar VC"
    ), inline=False)
    e.add_field(name="📋 Queue", value=(
        "`/queue [hal]` — Lihat antrian\n"
        "`/playnext <lagu>` — Sisipkan ke depan queue\n"
        "`/skipto <no>` — Loncat ke nomor antrian\n"
        "`/remove <no>` · `/clear` · `/shuffle`\n"
        "`/move <dari> <ke>` — Pindah urutan lagu\n"
        "`/loop` — Loop lagu ini\n"
        "`/loopqueue` — Loop semua queue"
    ), inline=False)
    e.add_field(name="🔊 Volume", value=(
        "`/volume <0-200>` · `/volup` · `/voldown`\n"
        f"Sekarang: **{int(s.volume * 100)}%** {fmt_vol_bar(s.volume)}"
    ), inline=False)
    e.add_field(name="🎛 Preset & EQ", value=(
        "`/preset` — Ganti preset (dropdown!)\n"
        "`/eq` — Panel EQ Bass/Mid/Treble interaktif\n"
        "`hydra` 🌊 · `harman` 🎧 · `dolby` 🎬\n"
        "`bassboost` 🔊 · `vocal` 🎤 · `lofi` 📻\n"
        "`nightcore` ⚡ · `8d` 🌀 · `vaporwave` 🌊\n"
        f"Aktif: **{p['icon']} {p['label']}** — {p['desc']}"
    ), inline=False)
    e.add_field(name="📁 Playlist", value=(
        "`/playlist_create` · `/playlist_add`\n"
        "`/playlist_play` · `/playlist_list`\n"
        "`/playlist_delete`"
    ), inline=False)
    e.add_field(name="🎵 Fitur Lain", value=(
        "`/history` · `/autoplay` · `/voteskip`\n"
        "`/ping` · `/uptime`"
    ), inline=False)
    e.add_field(name="📡 24/7", value=(
        "`/setchannel247` · `/stay247` · `/auto247`\n"
        "`/status247`\n"
        f"Stay: {'🟢 ON' if cfg['stay_in_channel'] else '🔴 OFF'}  ·  Auto: {'🟢 ON' if cfg['auto_join'] else '🔴 OFF'}"
    ), inline=False)
    e.set_footer(text="🎵 NEO MUSIC · by Xyrons2  ·  ketik / untuk autocomplete")
    await interaction.response.send_message(embed=e)

# ══════════════════════════════════════════════════════════
#  SLASH COMMANDS — PLAYLIST
# ══════════════════════════════════════════════════════════
@bot.tree.command(name="playlist_create", description="📁 Buat playlist baru")
@app_commands.describe(name="Nama playlist baru")
async def slash_playlist_create(interaction: discord.Interaction, name: str):
    pls = get_guild_pl(interaction.guild.id)
    if name.lower() in pls:
        return await interaction.response.send_message(
            embed=mk_embed(desc=f"> ❌ Playlist **{name}** sudah ada.", color=C_ERROR), ephemeral=True)
    if len(pls) >= 20:
        return await interaction.response.send_message(
            embed=mk_embed(desc="> ❌ Maksimal 20 playlist per server.", color=C_ERROR), ephemeral=True)
    pls[name.lower()] = []
    save_playlists()
    await interaction.response.send_message(
        embed=mk_embed(desc=f"> 📁 Playlist **{name}** berhasil dibuat!\n> Tambah lagu: `/playlist_add`", color=C_SUCCESS))

@bot.tree.command(name="playlist_add", description="➕ Tambah lagu ke playlist")
@app_commands.describe(name="Nama playlist", query="Nama lagu atau URL")
@app_commands.autocomplete(name=playlist_name_autocomplete, query=play_autocomplete)
async def slash_playlist_add(interaction: discord.Interaction, name: str, query: str):
    await interaction.response.defer()
    pls = get_guild_pl(interaction.guild.id)
    if name.lower() not in pls:
        return await interaction.followup.send(
            embed=mk_embed(desc=f"> ❌ Playlist **{name}** tidak ditemukan.", color=C_ERROR), ephemeral=True)
    songs = pls[name.lower()]
    if len(songs) >= 200:
        return await interaction.followup.send(
            embed=mk_embed(desc="> ❌ Playlist penuh (max 200 lagu).", color=C_ERROR), ephemeral=True)
    try:
        song = await fetch_song(query)
        if any(x.get("webpage_url") == song.get("webpage_url") for x in songs):
            return await interaction.followup.send(
                embed=mk_embed(desc=f"> ℹ️ Lagu sudah ada di **{name}**.", color=C_WARN), ephemeral=True)
        songs.append({
            "title": song["title"], "url": song.get("webpage_url", ""),
            "duration": song.get("duration", 0), "thumbnail": song.get("thumbnail", ""),
            "uploader": song.get("uploader", "Unknown"),
            "webpage_url": song.get("webpage_url", ""), "platform": song.get("platform", "youtube")
        })
        save_playlists()
        e = discord.Embed(color=C_SUCCESS)
        e.set_author(name=f"➕  DITAMBAHKAN  ·  {name.upper()}")
        e.description = f"**[{trunc(song['title'])}]({song.get('webpage_url','')})**\n-# 📁 {name}  ·  #{len(songs)}"
        if song.get("thumbnail"): e.set_thumbnail(url=song["thumbnail"])
        e.set_footer(text="🎵 NEO MUSIC · by Xyrons2")
        await interaction.followup.send(embed=e)
    except Exception as ex:
        await interaction.followup.send(
            embed=mk_embed(desc=f"> ❌ `{str(ex)}`", color=C_ERROR), ephemeral=True)

@bot.tree.command(name="playlist_play", description="▶️ Putar semua lagu dari playlist")
@app_commands.describe(name="Nama playlist")
@app_commands.autocomplete(name=playlist_name_autocomplete)
async def slash_playlist_play(interaction: discord.Interaction, name: str):
    await interaction.response.defer()
    pls = get_guild_pl(interaction.guild.id)
    if name.lower() not in pls:
        return await interaction.followup.send(
            embed=mk_embed(desc=f"> ❌ Playlist **{name}** tidak ditemukan.", color=C_ERROR), ephemeral=True)
    songs = pls[name.lower()]
    if not songs:
        return await interaction.followup.send(
            embed=mk_embed(desc=f"> ❌ Playlist **{name}** kosong.", color=C_ERROR), ephemeral=True)
    vc = await join_vc_inter(interaction)
    if not vc: return
    state = get_state(interaction.guild.id)
    for song in songs:
        state.queue.append({
            "title": song["title"], "url": song.get("webpage_url", song.get("url", "")),
            "duration": song.get("duration", 0), "thumbnail": song.get("thumbnail", ""),
            "webpage_url": song.get("webpage_url", ""), "uploader": song.get("uploader", "Unknown"),
            "platform": song.get("platform", "youtube"), "_stub": True,
            "stub_url": song.get("webpage_url", song.get("url", ""))
        })
    await interaction.followup.send(embed=mk_embed(
        title=f"▶️ Playlist — {name}",
        desc=f"> **{len(songs)} lagu** ditambahkan ke queue!",
        color=C_SUCCESS,
        fields=[("🎛 Preset", f"{PRESETS[state.preset]['icon']} {PRESETS[state.preset]['label']}", True),
                ("🔊 Volume", f"{int(state.volume * 100)}%", True)]))
    if not vc.is_playing() and not vc.is_paused():
        await play_next(interaction.channel, interaction.guild)

@bot.tree.command(name="playlist_list", description="📋 Lihat semua playlist atau isi playlist")
@app_commands.describe(name="Nama playlist (kosongkan untuk lihat semua)")
@app_commands.autocomplete(name=playlist_name_autocomplete)
async def slash_playlist_list(interaction: discord.Interaction, name: str = None):
    pls = get_guild_pl(interaction.guild.id)
    if name is None:
        if not pls:
            return await interaction.response.send_message(
                embed=mk_embed(desc="> 📁 Belum ada playlist.\n> Buat: `/playlist_create`", color=C_CYAN2), ephemeral=True)
        lines = [f"`{i+1:02d}`  📁  **{n}**  ·  `{len(s)} lagu`" for i, (n, s) in enumerate(pls.items())]
        await interaction.response.send_message(embed=mk_embed(
            title=f"📋 Playlist — {interaction.guild.name}",
            desc="\n".join(lines), color=C_CYAN,
            fields=[("📁 Total", f"**{len(pls)} playlist**", True)]))
    else:
        if name.lower() not in pls:
            return await interaction.response.send_message(
                embed=mk_embed(desc=f"> ❌ Playlist **{name}** tidak ditemukan.", color=C_ERROR), ephemeral=True)
        songs = pls[name.lower()]
        if not songs:
            return await interaction.response.send_message(
                embed=mk_embed(desc=f"> 📁 Playlist **{name}** kosong.", color=C_CYAN2))
        lines = [f"`{i+1:02d}`  {PLATFORM_ICONS.get(s.get('platform','youtube'),'🔴')}  [{trunc(s['title'], 40)}]({s.get('webpage_url','')})  `{fmt_dur(s.get('duration',0))}`"
                 for i, s in enumerate(songs)]
        total_dur = sum(s.get("duration", 0) for s in songs)
        await interaction.response.send_message(embed=mk_embed(
            title=f"📁 {name}  ·  {len(songs)} lagu",
            desc="\n".join(lines), color=C_CYAN,
            fields=[("⏱ Total Durasi", f"`{fmt_dur(total_dur)}`", True)]))

@bot.tree.command(name="playlist_delete", description="🗑️ Hapus playlist atau lagu dari playlist")
@app_commands.describe(name="Nama playlist", index="Nomor lagu yang dihapus (kosongkan untuk hapus seluruh playlist)")
@app_commands.autocomplete(name=playlist_name_autocomplete)
async def slash_playlist_delete(interaction: discord.Interaction, name: str, index: int = None):
    pls = get_guild_pl(interaction.guild.id)
    if name.lower() not in pls:
        return await interaction.response.send_message(
            embed=mk_embed(desc=f"> ❌ Playlist **{name}** tidak ditemukan.", color=C_ERROR), ephemeral=True)
    if index is None:
        del pls[name.lower()]
        save_playlists()
        await interaction.response.send_message(
            embed=mk_embed(desc=f"> 🗑 Playlist **{name}** dihapus.", color=C_ERROR))
    else:
        songs = pls[name.lower()]
        if index < 1 or index > len(songs):
            return await interaction.response.send_message(
                embed=mk_embed(desc="> ❌ Index tidak valid.", color=C_ERROR), ephemeral=True)
        removed = songs.pop(index - 1)
        save_playlists()
        await interaction.response.send_message(
            embed=mk_embed(desc=f"> 🗑 **{trunc(removed['title'])}** dihapus dari **{name}**.", color=C_ERROR))

# ══════════════════════════════════════════════════════════
#  EQ PANEL — Interactive Buttons
# ══════════════════════════════════════════════════════════
def mk_eq_embed(state, guild) -> discord.Embed:
    p = PRESETS[state.preset]
    bars   = {-2: "🔴🔴⬛⬛⬛", -1: "🟠🟠⬛⬛⬛", 0: "🟡🟡🟡⬛⬛", 1: "🟢🟢🟢🟢⬛", 2: "🟢🟢🟢🟢🟢"}
    labels = {-2: "**-2**", -1: "**-1**", 0: "** 0**", 1: "**+1**", 2: "**+2**"}
    e = discord.Embed(color=C_CYAN)
    e.set_author(name="🎛️  EQUALIZER  ·  NEO MUSIC")
    e.description = (
        f"```\n"
        f"  Bass   {bars[state.eq_bass]}  {labels[state.eq_bass]}\n"
        f"  Mid    {bars[state.eq_mid]}  {labels[state.eq_mid]}\n"
        f"  Treble {bars[state.eq_treble]}  {labels[state.eq_treble]}\n"
        f"```\n"
        f"> Preset: **{p['icon']} {p['label']}**"
    )
    vc = guild.voice_client
    if vc and vc.is_playing():
        e.description += "  ·  🔴 Live"
    e.set_footer(text="🎵 NEO MUSIC · by Xyrons2  ·  Klik tombol untuk ubah · auto-apply")
    return e

def _apply_eq(state, guild):
    vc = guild.voice_client
    if vc and state.current and (vc.is_playing() or vc.is_paused()):
        state.seek_pos = time.time() - state.play_start
        state.force_replay = True
        vc.stop()

class EQView(discord.ui.View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=120)
        self.guild = guild

    def _state(self) -> "GuildState":
        return get_state(self.guild.id)

    async def _update(self, interaction: discord.Interaction):
        state = self._state()
        _apply_eq(state, self.guild)
        await interaction.response.edit_message(embed=mk_eq_embed(state, self.guild), view=self)

    @discord.ui.button(label="Bass  −", style=discord.ButtonStyle.secondary, row=0)
    async def bass_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self._state()
        if s.eq_bass > -2: s.eq_bass -= 1
        await self._update(interaction)

    @discord.ui.button(label="Bass  +", style=discord.ButtonStyle.primary, row=0)
    async def bass_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self._state()
        if s.eq_bass < 2: s.eq_bass += 1
        await self._update(interaction)

    @discord.ui.button(label="Mid   −", style=discord.ButtonStyle.secondary, row=1)
    async def mid_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self._state()
        if s.eq_mid > -2: s.eq_mid -= 1
        await self._update(interaction)

    @discord.ui.button(label="Mid   +", style=discord.ButtonStyle.primary, row=1)
    async def mid_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self._state()
        if s.eq_mid < 2: s.eq_mid += 1
        await self._update(interaction)

    @discord.ui.button(label="Treble −", style=discord.ButtonStyle.secondary, row=2)
    async def treble_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self._state()
        if s.eq_treble > -2: s.eq_treble -= 1
        await self._update(interaction)

    @discord.ui.button(label="Treble +", style=discord.ButtonStyle.primary, row=2)
    async def treble_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self._state()
        if s.eq_treble < 2: s.eq_treble += 1
        await self._update(interaction)

    @discord.ui.button(label="🔄 Reset", style=discord.ButtonStyle.danger, row=3)
    async def reset_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        s = self._state()
        s.eq_bass = s.eq_mid = s.eq_treble = 0
        await self._update(interaction)

    async def on_timeout(self):
        pass

@bot.tree.command(name="eq", description="🎛️ Buka panel Equalizer interaktif — Bass / Mid / Treble")
async def slash_eq(interaction: discord.Interaction):
    state = get_state(interaction.guild.id)
    view  = EQView(guild=interaction.guild)
    await interaction.response.send_message(embed=mk_eq_embed(state, interaction.guild), view=view)

@bot.command(name="eq", aliases=["equalizer"])
async def cmd_eq(ctx):
    state = get_state(ctx.guild.id)
    view  = EQView(guild=ctx.guild)
    await ctx.send(embed=mk_eq_embed(state, ctx.guild), view=view)

# ══════════════════════════════════════════════════════════
#  !247 PREFIX COMMANDS
# ══════════════════════════════════════════════════════════
@bot.group(name="247", invoke_without_command=True)
async def cmd_247(ctx):
    cfg = get_247(ctx.guild.id)
    vc  = ctx.guild.get_channel(cfg.get("voice_channel_id") or 0)
    bvc = ctx.guild.voice_client
    e   = discord.Embed(title="📡 24/7 Mode — NEO MUSIC", color=C_CYAN)
    e.add_field(name="📻 Default VC", value=f"**{vc.name}**" if vc else "❌ Belum diset", inline=True)
    e.add_field(name="🔌 Terhubung",  value=f"🟢 **{bvc.channel.name}**" if bvc else "🔴 Tidak", inline=True)
    e.add_field(name="\u200b", value="\u200b", inline=True)
    e.add_field(name="🏠 Stay",      value="🟢 ON" if cfg["stay_in_channel"] else "🔴 OFF", inline=True)
    e.add_field(name="🤖 Auto Join", value="🟢 ON" if cfg["auto_join"] else "🔴 OFF", inline=True)
    e.add_field(name="\u200b", value="\u200b", inline=True)
    e.add_field(name="📖 Commands", value=("`!247 bind` · `!247 stay` · `!247 auto`\n`!247 status` · `!247 reset`"), inline=False)
    e.set_footer(text="🎵 NEO MUSIC · by Xyrons2")
    await ctx.send(embed=e)

@cmd_247.command(name="bind", aliases=["setvc", "svc", "setvoicechannel"])
async def cmd_247_bind(ctx, *, channel_name: str = None):
    if ctx.author.voice and ctx.author.voice.channel:
        vc = ctx.author.voice.channel
    elif channel_name:
        vc = discord.utils.find(lambda c: c.name.lower() == channel_name.lower() and isinstance(c, discord.VoiceChannel), ctx.guild.channels)
        if not vc: return await ctx.send(embed=mk_embed(desc=f"> ❌ VC `{channel_name}` tidak ditemukan.", color=C_ERROR))
    else:
        return await ctx.send(embed=mk_embed(desc="> ❌ Masuk ke VC dulu, atau: `!247 bind NamaChannel`", color=C_WARN))
    cfg = get_247(ctx.guild.id); cfg["voice_channel_id"] = vc.id; save_247(ctx.guild.id)
    await ctx.send(embed=mk_embed(desc=f"> 📻 VC target di-bind ke **{vc.name}**!", color=C_CYAN))

@cmd_247.command(name="stay", aliases=["sc", "stayinchannel"])
async def cmd_247_stay(ctx):
    cfg = get_247(ctx.guild.id); cfg["stay_in_channel"] = not cfg["stay_in_channel"]; save_247(ctx.guild.id)
    on = cfg["stay_in_channel"]
    if on:
        vc_id = cfg.get("voice_channel_id")
        if vc_id:
            vc = ctx.guild.get_channel(vc_id)
            if vc and not ctx.guild.voice_client:
                try: await vc.connect()
                except Exception: pass
    await ctx.send(embed=mk_embed(desc=f"> 🏠 Stay in channel: **{'🟢 ON' if on else '🔴 OFF'}**\n" +
        ("> Bot akan tetap di VC walau queue habis." if on else "> Bot keluar saat queue habis."), color=C_CYAN if on else C_CYAN2))

@cmd_247.command(name="auto", aliases=["aj", "autojoin"])
async def cmd_247_auto(ctx):
    cfg = get_247(ctx.guild.id)
    if not cfg.get("voice_channel_id"): return await ctx.send(embed=mk_embed(desc="> ❌ Bind dulu VC-nya: `!247 bind`", color=C_ERROR))
    cfg["auto_join"] = not cfg["auto_join"]; save_247(ctx.guild.id)
    on = cfg["auto_join"]; vc = ctx.guild.get_channel(cfg["voice_channel_id"])
    await ctx.send(embed=mk_embed(desc=f"> 🤖 Auto join: **{'🟢 ON' if on else '🔴 OFF'}**\n" +
        f"> Bot otomatis join **{vc.name if vc else 'Unknown'}** saat bot restart.", color=C_CYAN if on else C_CYAN2))

@cmd_247.command(name="reset")
async def cmd_247_reset(ctx):
    settings_247[str(ctx.guild.id)] = {"stay_in_channel": False, "auto_join": False, "voice_channel_id": None}
    save_247_all(settings_247)
    await ctx.send(embed=mk_embed(desc="> 📡 Semua pengaturan 24/7 direset.", color=C_WARN))

@cmd_247.command(name="status", aliases=["info", "st"])
async def cmd_247_status(ctx):
    cfg = get_247(ctx.guild.id); vc = ctx.guild.get_channel(cfg.get("voice_channel_id") or 0); bvc = ctx.guild.voice_client
    await ctx.send(embed=mk_embed(title="📡 24/7 Status", desc=(
        f"> 📻 **Target VC**  : {f'**{vc.name}**' if vc else '❌ Belum di-bind'}\n"
        f"> 🔌 **Terhubung**  : {f'🟢 **{bvc.channel.name}**' if bvc else '🔴 Tidak'}\n"
        f"> 🏠 **Stay in VC** : {'🟢 ON' if cfg['stay_in_channel'] else '🔴 OFF'}\n"
        f"> 🤖 **Auto Join**  : {'🟢 ON' if cfg['auto_join'] else '🔴 OFF'}"
    ), color=C_CYAN))

# ══════════════════════════════════════════════════════════
#  /247 SLASH COMMANDS
# ══════════════════════════════════════════════════════════
@bot.tree.command(name="setchannel247", description="📻 Set voice channel target untuk mode 24/7")
@app_commands.describe(channel="Pilih voice channel target (kosong = VC kamu sekarang)")
async def slash_setchannel247(interaction: discord.Interaction, channel: discord.VoiceChannel = None):
    if channel is None:
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Masuk ke VC dulu, atau pilih channel di parameter.", color=C_ERROR), ephemeral=True)
        channel = interaction.user.voice.channel
    cfg = get_247(interaction.guild.id); cfg["voice_channel_id"] = channel.id; save_247(interaction.guild.id)
    await interaction.response.send_message(embed=mk_embed(desc=f"> 📻 VC target di-set ke **{channel.name}**!\n> Aktifkan `/stay247` atau `/auto247` untuk mulai.", color=C_CYAN))

@bot.tree.command(name="stay247", description="🏠 Toggle bot tetap di VC walau queue habis")
async def slash_stay247(interaction: discord.Interaction):
    cfg = get_247(interaction.guild.id)
    if not cfg.get("voice_channel_id"): return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Set dulu VC-nya: `/setchannel247`", color=C_ERROR), ephemeral=True)
    cfg["stay_in_channel"] = not cfg["stay_in_channel"]; save_247(interaction.guild.id); on = cfg["stay_in_channel"]
    if on and not interaction.guild.voice_client:
        vc = interaction.guild.get_channel(cfg["voice_channel_id"])
        if vc:
            try: await vc.connect()
            except Exception: pass
    vc = interaction.guild.get_channel(cfg.get("voice_channel_id") or 0)
    await interaction.response.send_message(embed=mk_embed(desc=(
        f"> 🏠 **Stay in Channel**: {'🟢 ON' if on else '🔴 OFF'}\n" +
        (f"> Bot akan tetap di **{vc.name}** walau queue habis." if on and vc else "> Bot akan keluar otomatis saat queue habis.")
    ), color=C_CYAN if on else C_CYAN2))

@bot.tree.command(name="auto247", description="🤖 Toggle bot otomatis join VC saat restart")
async def slash_auto247(interaction: discord.Interaction):
    cfg = get_247(interaction.guild.id)
    if not cfg.get("voice_channel_id"): return await interaction.response.send_message(embed=mk_embed(desc="> ❌ Set dulu VC-nya: `/setchannel247`", color=C_ERROR), ephemeral=True)
    cfg["auto_join"] = not cfg["auto_join"]; save_247(interaction.guild.id); on = cfg["auto_join"]
    vc = interaction.guild.get_channel(cfg["voice_channel_id"])
    await interaction.response.send_message(embed=mk_embed(desc=(
        f"> 🤖 **Auto Join**: {'🟢 ON' if on else '🔴 OFF'}\n" +
        (f"> Bot otomatis join **{vc.name if vc else '?'}** saat restart." if on else "> Bot tidak akan auto join saat restart.")
    ), color=C_CYAN if on else C_CYAN2))

@bot.tree.command(name="status247", description="📊 Lihat status 24/7 saat ini")
async def slash_status247(interaction: discord.Interaction):
    cfg = get_247(interaction.guild.id); vc = interaction.guild.get_channel(cfg.get("voice_channel_id") or 0)
    bvc = interaction.guild.voice_client; s = get_state(interaction.guild.id)
    e = discord.Embed(color=C_CYAN); e.set_author(name="📡  24/7 STATUS  ·  NEO MUSIC")
    e.add_field(name="📻 Target VC",   value=f"📌 **{vc.name}**" if vc else "❌ Belum diset", inline=True)
    e.add_field(name="🔌 Koneksi",     value=f"🟢 **{bvc.channel.name}**" if bvc else "🔴 Tidak terhubung", inline=True)
    e.add_field(name="",               value="", inline=True)
    e.add_field(name="🏠 Stay",        value="🟢 **ON**" if cfg["stay_in_channel"] else "🔴 **OFF**", inline=True)
    e.add_field(name="🤖 Auto Join",   value="🟢 **ON**" if cfg["auto_join"] else "🔴 **OFF**", inline=True)
    e.add_field(name="",               value="", inline=True)
    e.add_field(name="🎵 Now Playing", value=f"`{s.current['title'][:38]}…`" if s.current else "`—`", inline=True)
    e.add_field(name="📋 Queue",       value=f"`{len(s.queue)} lagu`" if s.queue else "`Kosong`", inline=True)
    e.add_field(name="",               value="", inline=True)
    e.set_footer(text="🎵 NEO MUSIC · by Xyrons2")
    await interaction.response.send_message(embed=e)

# ══════════════════════════════════════════════════════════
#  KEEPALIVE TASKS
# ══════════════════════════════════════════════════════════
@tasks.loop(minutes=5)
async def keepalive_vc():
    for guild in bot.guilds:
        vc = guild.voice_client
        if not vc or not vc.is_connected():
            cfg = get_247(guild.id)
            if cfg["stay_in_channel"]:
                vc_id = cfg.get("voice_channel_id")
                if vc_id:
                    channel = guild.get_channel(vc_id)
                    if channel:
                        try: await channel.connect(); print(f"[247] Reconnected: {channel.name}")
                        except Exception as e: print(f"[247] Reconnect gagal: {e}")
            continue
        if not vc.is_playing() and not vc.is_paused():
            try: vc.send_audio_packet(b'\xf8\xff\xfe', encode=False)
            except Exception: pass

@tasks.loop(hours=24)
async def keepalive_247():
    for guild in bot.guilds:
        cfg = get_247(guild.id)
        if not cfg["stay_in_channel"]: continue
        vc_id = cfg.get("voice_channel_id")
        if not vc_id: continue
        vc = guild.get_channel(vc_id)
        if vc and not guild.voice_client:
            try: await vc.connect(); print(f"[247] Rejoined {vc.name}")
            except Exception as e: print(f"[247] Failed: {e}")

# ── FIX #7: refresh_cookies — hapus try_extract_browser_cookies yang tidak ada ──
@tasks.loop(hours=168)
async def refresh_cookies():
    """Di Railway, cookies dari ENV VAR — re-write file dari env var setiap minggu."""
    cookie_content = os.getenv("YOUTUBE_COOKIES")
    if cookie_content:
        result = get_cookie_file()
        if result:
            print(f"[✅] Cookies di-refresh dari ENV VAR")
        else:
            print(f"[⚠️] Cookies refresh gagal — cek format YOUTUBE_COOKIES")
    else:
        print(f"[ℹ️] YOUTUBE_COOKIES tidak diset, skip refresh")

@tasks.loop(seconds=15)
async def np_auto_update():
    for gid, state in list(guild_states.items()):
        if not state.current or not state.np_message or not state.np_channel: continue
        guild = bot.get_guild(int(gid))
        if not guild: continue
        vc = guild.voice_client
        if not vc or (not vc.is_playing() and not vc.is_paused()): continue
        try:
            embed = mk_now_playing(state.current, state, len(state.queue))
            await state.np_message.edit(embed=embed)
        except Exception: state.np_message = None

# ══════════════════════════════════════════════════════════
#  EVENTS
# ══════════════════════════════════════════════════════════
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot: return
    await bot.process_commands(message)
    if not message.guild: return
    ch_id = get_request_ch(message.guild.id)
    if not ch_id or message.channel.id != ch_id: return
    if message.content.startswith("!"): return
    query = message.content.strip()
    if not query: return
    vc = message.guild.voice_client
    if not message.author.voice:
        return await message.channel.send(embed=mk_embed(desc=f"> ❌ {message.author.mention} masuk VC dulu!", color=C_ERROR), delete_after=8)
    if not vc: vc = await message.author.voice.channel.connect()
    elif vc.channel != message.author.voice.channel: await vc.move_to(message.author.voice.channel)
    state = get_state(message.guild.id)
    loading = await message.channel.send(embed=mk_embed(desc=f"> 🎵 {message.author.mention} request: **{trunc(query, 50)}**...", color=C_CYAN2))
    ok = await _do_play(message.channel, message.guild, vc, state, query, loading)
    if ok and not vc.is_playing() and not vc.is_paused():
        await play_next(message.channel, message.guild)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.id != bot.user.id: return
    if before.channel and not after.channel:
        guild = before.channel.guild; cfg = get_247(guild.id)
        if cfg["stay_in_channel"]:
            vc_id = cfg.get("voice_channel_id") or before.channel.id
            vc = guild.get_channel(vc_id)
            if vc:
                await asyncio.sleep(3)
                try: await vc.connect(); print(f"[247] Auto-rejoin: {vc.name}")
                except Exception as e: print(f"[247] Rejoin gagal: {e}")

# ── FIX #8: on_ready — cek is_running() sebelum start tasks ──
@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"[✅] Global sync: {len(synced)} commands")
    except Exception as e: print(f"[⚠️] Sync gagal: {e}")

    for guild in bot.guilds:
        cfg = get_247(guild.id); vc_id = cfg.get("voice_channel_id")
        if cfg.get("auto_join") and vc_id:
            vc = guild.get_channel(vc_id)
            if vc and not guild.voice_client:
                try: await vc.connect(); print(f"[247] Auto-join: {vc.name}")
                except Exception as e: print(f"[247] Failed: {e}")

    # FIX: Cek is_running() agar tidak error saat bot reconnect
    if not keepalive_vc.is_running():    keepalive_vc.start()
    if not keepalive_247.is_running():   keepalive_247.start()
    if not refresh_cookies.is_running(): refresh_cookies.start()
    if not np_auto_update.is_running():  np_auto_update.start()

    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!help | /help | NEO MUSIC 🎵"))
    print(f"[✅] Online  : {bot.user}")
    print(f"[🟢] Spotify : {'✅' if sp else '❌'}")
    print(f"[🌐] yt-dlp  : {yt_dlp.version.__version__}")
    print(f"[🍪] Cookies : {'✅ ' + _cookie_file if _cookie_file else '❌ (fallback mode)'}")
    print(f"[🎬] FFmpeg  : {FFMPEG_PATH}")
    print(f"[🌊] Hydra Preset: ✅ ACTIVE!")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=mk_embed(desc="> ❌ Kurang argumen. Ketik `!help`.", color=C_ERROR))
    elif not isinstance(error, (commands.CommandNotFound, commands.CheckFailure)):
        print(f"[ERR] {traceback.format_exc()}")
        await ctx.send(embed=mk_embed(desc=f"> ❌ `{error}`", color=C_ERROR))

if __name__ == "__main__":
    bot.run(TOKEN)