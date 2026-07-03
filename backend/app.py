import os
import json
import asyncio
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

app = FastAPI()

# Enable CORS so the Vercel frontend can call the endpoints directly
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = os.path.join(os.getcwd(), 'public', 'output')

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

class UploadVideoRequest(BaseModel):
    title: str
    description: str
    channel: Optional[str] = 'minecraft'
    videoFilename: Optional[str] = None

class GenerateVideoRequest(BaseModel):
    urls: List[str]

class GenerateMrBeastRequest(BaseModel):
    url: str
    gameplayUrl: Optional[str] = None
    quality: Optional[str] = 'high'

# ── History ──
@app.get("/api/history")
async def get_history(channel: str = 'all'):
    video_exts = {'.mp4', '.webm', '.mov'}
    files = []
    
    if os.path.exists(OUTPUT_DIR):
        for entry in os.scandir(OUTPUT_DIR):
            if entry.is_file() and os.path.splitext(entry.name)[1].lower() in video_exts:
                stat = entry.stat()
                file_channel = 'mrbeast' if entry.name.startswith('mrbeast') else 'minecraft'
                files.append({
                    "name": entry.name,
                    "url": f"/output/{entry.name}",
                    "sizeBytes": stat.st_size,
                    "sizeMB": f"{(stat.st_size / (1024 * 1024)):.2f}",
                    "createdAt": datetime_to_iso(stat.st_ctime),
                    "channel": file_channel
                })
        # Sort by creation time desc
        files.sort(key=lambda x: x["createdAt"], reverse=True)

    if channel != 'all':
        files = [f for f in files if f["channel"] == channel]
    
    return {"files": files}

def datetime_to_iso(timestamp):
    import datetime
    return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).isoformat()

@app.delete("/api/history")
async def delete_history_file(req: Request):
    body = await req.json()
    filename = body.get("filename")
    if not filename:
        raise HTTPException(status_code=400, detail="filename required")

    basename = os.path.basename(filename)
    file_path = os.path.join(OUTPUT_DIR, basename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    try:
        os.remove(file_path)
        return {"success": True, "deleted": basename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Upload Video ──
@app.post("/api/upload-video")
async def upload_video(data: UploadVideoRequest):
    if not data.title or not data.description:
        raise HTTPException(status_code=400, detail="Title and description are required")

    prefix = data.channel.upper() + '_'
    if not os.environ.get(f"{prefix}YOUTUBE_CLIENT_ID") or not os.environ.get(f"{prefix}YOUTUBE_CLIENT_SECRET") or not os.environ.get(f"{prefix}YOUTUBE_REFRESH_TOKEN"):
        raise HTTPException(
            status_code=500,
            detail=f"Server is missing YouTube credentials for {data.channel}. Set {prefix}YOUTUBE_CLIENT_ID, {prefix}YOUTUBE_CLIENT_SECRET, and {prefix}YOUTUBE_REFRESH_TOKEN."
        )

    script_path = os.path.join(os.getcwd(), 'scripts', 'video_generator.py')
    cmd = ["python3", script_path, "--action", "upload", "--title", data.title, "--description", data.description, "--channel", data.channel]

    if data.videoFilename:
        video_path = os.path.join(OUTPUT_DIR, os.path.basename(data.videoFilename))
        cmd.extend(["--video", video_path])

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        if process.returncode == 0:
            return {"success": True, "stdout": stdout.decode('utf-8')}
        else:
            raise HTTPException(status_code=500, detail=f"Upload failed: {stderr.decode('utf-8')}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Video Generation Streams ──
async def stream_video_generation(urls_json, api_key):
    script_path = os.path.join(os.getcwd(), 'scripts', 'video_generator.py')
    music_path = os.path.join(os.getcwd(), 'scripts', 'music.mp3')
    
    cmd = ["python3", script_path, "--action", "generate", "--sources", urls_json, "--music", music_path]
    env = {
        **os.environ,
        "PYTHONUNBUFFERED": "1",
        "GEMINI_API_KEY": api_key
    }

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=env
    )

    yield json.dumps({"type": "log", "message": "Starting Gemini video analysis…\n"}) + "\n"

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        text = line.decode('utf-8')
        yield json.dumps({"type": "log", "message": text}) + "\n"

    await process.wait()
    if process.returncode == 0:
        yield json.dumps({"type": "success"}) + "\n"
    else:
        yield json.dumps({"type": "error", "message": f"Python script exited with code {process.returncode}"}) + "\n"

@app.post("/api/generate-video")
async def generate_video(data: GenerateVideoRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Server is missing GEMINI_API_KEY. Add it to environment variables.")

    if not data.urls:
        raise HTTPException(status_code=400, detail="Provide at least one source video URL.")

    urls_json = json.dumps(data.urls)
    return StreamingResponse(
        stream_video_generation(urls_json, api_key),
        media_type="application/x-ndjson"
    )

async def stream_mrbeast_generation(url, gameplay_url, quality):
    script_path = os.path.join(os.getcwd(), 'scripts', 'mrbeast_generator.py')
    
    cmd = ["python3", "-u", script_path, "--url", url]
    if gameplay_url:
        cmd.extend(["--gameplay-url", gameplay_url])
    if quality:
        cmd.extend(["--quality", quality])

    env = {
        **os.environ,
        "PYTHONIOENCODING": "utf-8"
    }

    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        env=env
    )

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        text = line.decode('utf-8')
        yield json.dumps({"type": "log", "message": text}) + "\n"

    await process.wait()
    if process.returncode == 0:
        yield json.dumps({"type": "success", "message": "Short generation complete."}) + "\n"
    else:
        yield json.dumps({"type": "error", "message": f"Process exited with code {process.returncode}"}) + "\n"

@app.post("/api/generate-mrbeast")
async def generate_mrbeast(data: GenerateMrBeastRequest):
    if not data.url:
        raise HTTPException(status_code=400, detail="Provide a valid main video URL.")

    return StreamingResponse(
        stream_mrbeast_generation(data.url, data.gameplayUrl, data.quality),
        media_type="application/x-ndjson"
    )

# Serve output folder statically
app.mount("/output", StaticFiles(directory=OUTPUT_DIR), name="output")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)
