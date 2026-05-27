from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import yt_dlp
import os

app = FastAPI(title="SEEK_TECH API", description="API para buscar música en YouTube sin API Key")

# Configurar CORS para que tu app Android pueda conectarse
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/search")
async def search_songs(q: str = Query(..., description="Término de búsqueda")):
    """Busca canciones en YouTube"""
    try:
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'playlistend': 10
        }
        
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
    """Obtiene la URL directa del audio a partir del ID del video"""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'quiet': True,
            'format': 'bestaudio/best',
        }
        
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
    """Verifica que el servidor esté funcionando"""
    return JSONResponse(content={'status': 'ok', 'message': 'SEEK_TECH API funcionando'})

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)