from fastapi import FastAPI, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import yt_dlp
import os
import requests

app = FastAPI(title="SEEK_TECH API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Opciones para yt-dlp
YDL_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'extract_flat': True,
}

@app.get("/search")
async def search_songs(q: str = Query(..., description="Término de búsqueda")):
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
    """Devuelve la URL del audio"""
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'quiet': True,
            'format': 'bestaudio/best',
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Buscar el mejor audio
            audio_url = None
            if 'url' in info:
                audio_url = info['url']
            elif 'formats' in info:
                # Priorizar audio opus o m4a
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        if f.get('ext') in ['m4a', 'opus', 'webm']:
                            audio_url = f['url']
                            break
                if not audio_url:
                    for f in info['formats']:
                        if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                            audio_url = f['url']
                            break
            
            if audio_url:
                return JSONResponse(content={'stream_url': audio_url, 'success': True})
            else:
                return JSONResponse(content={'error': 'No se encontró audio', 'success': False}, status_code=404)
    except Exception as e:
        error_msg = str(e)
        if 'Video unavailable' in error_msg:
            return JSONResponse(content={'error': 'Video no disponible', 'success': False}, status_code=403)
        return JSONResponse(content={'error': error_msg, 'success': False}, status_code=500)

@app.get("/proxy-stream")
async def proxy_stream(video_id: str = Query(..., description="ID del video de YouTube")):
    """Transmite el audio directamente (soluciona problemas de CORS)"""
    try:
        # Primero obtener la URL del audio
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'quiet': True,
            'format': 'bestaudio/best',
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            audio_url = None
            if 'formats' in info:
                for f in info['formats']:
                    if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                        audio_url = f['url']
                        break
            
            if audio_url:
                # Descargar y transmitir el audio
                response = requests.get(audio_url, stream=True)
                return StreamingResponse(
                    response.iter_content(chunk_size=8192),
                    media_type="audio/mpeg",
                    headers={"Content-Disposition": f"inline; filename={video_id}.mp3"}
                )
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
