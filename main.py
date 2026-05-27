from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import yt_dlp
import os
import tempfile

app = FastAPI(title="SEEK_TECH API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Obtener cookies desde variable de entorno
COOKIES = os.environ.get("COOKIES", "")

def get_ydl_opts(extract_flat=True):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': extract_flat,
    }
    
    # Si hay cookies, guardarlas en un archivo temporal
    if COOKIES:
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(COOKIES)
                opts['cookiefile'] = f.name
        except Exception as e:
            print(f"Error al guardar cookies: {e}")
    
    return opts

@app.get("/search")
async def search_songs(q: str = Query(..., description="Término de búsqueda")):
    try:
        ydl_opts = get_ydl_opts(True)
        ydl_opts['playlistend'] = 10
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch10:{q}"
            info = ydl.extract_info(search_query, download=False)
            
            results = []
            if 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        video_id = entry.get('id', '')
                        thumbnail = f"https://img.youtube.com/vi/{video_id}/mqdefault.jpg" if video_id else ""
                        
                        results.append({
                            'title': entry.get('title', 'Sin título'),
                            'artist': entry.get('uploader', 'Desconocido'),
                            'videoId': video_id,
                            'thumbnail': thumbnail,
                            'duration': entry.get('duration', 0)
                        })
            
            return JSONResponse(content={'items': results})
    except Exception as e:
        return JSONResponse(content={'error': str(e), 'items': []}, status_code=500)

@app.get("/stream")
async def get_stream(video_id: str = Query(..., description="ID del video de YouTube")):
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = get_ydl_opts(False)
        ydl_opts['format'] = 'bestaudio/best'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            audio_url = None
            if 'url' in info:
                audio_url = info['url']
            elif 'formats' in info:
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        audio_url = f['url']
                        break
            
            if audio_url:
                return JSONResponse(content={'stream_url': audio_url})
            else:
                return JSONResponse(content={'error': 'No se encontró audio'}, status_code=404)
    except Exception as e:
        return JSONResponse(content={'error': str(e)}, status_code=500)

@app.get("/health")
async def health_check():
    return JSONResponse(content={'status': 'ok', 'message': 'SEEK_TECH API funcionando'})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
