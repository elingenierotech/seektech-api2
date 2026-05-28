from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# CONFIGURACION YTDLP

YDL_OPTS = {
    "format": "bestaudio[ext=m4a]/bestaudio/best",
    "quiet": True,
    "nocheckcertificate": True,
    "ignoreerrors": True,
    "no_warnings": True,
    "extract_flat": False,
    "noplaylist": True,
    "source_address": "0.0.0.0",
}

@app.get("/")
def root():
    return {"status": "SEEK TECH API ONLINE"}

# SEARCH

@app.get("/search")
async def search(q: str):

    try:

        with yt_dlp.YoutubeDL({
            "quiet": True,
            "extract_flat": "in_playlist",
            "skip_download": True,
        }) as ydl:

            results = ydl.extract_info(
                f"ytsearch20:{q}",
                download=False
            )

        items = []

        for entry in results["entries"]:

            if not entry:
                continue

            items.append({
                "videoId": entry.get("id"),
                "title": entry.get("title"),
                "artist": entry.get("channel", "Unknown")
            })

        return {
            "items": items
        }

    except Exception as e:

        return {
            "items": [],
            "error": str(e)
        }

# STREAM

@app.get("/stream")
async def stream(video_id: str):

    try:

        url = f"https://www.youtube.com/watch?v={video_id}"

        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:

            info = ydl.extract_info(url, download=False)

            stream_url = info.get("url")

            if not stream_url:

                return {
                    "error": "No stream found"
                }

            return {
                "stream_url": stream_url
            }

    except Exception as e:

        return {
            "error": str(e)
        }
