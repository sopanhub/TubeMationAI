import os
import json
import asyncio
import psutil
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

STATE_PATH = os.path.join(os.getcwd(), 'scheduler_state.json')
OUTPUT_DIR = os.path.join(os.getcwd(), 'public', 'output')

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

class UrlLibraryRequest(BaseModel):
    channel: str
    url: str

class SchedulerStartRequest(BaseModel):
    action: str
    channel: Optional[str] = None
    interval_hours: Optional[int] = 5

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

def read_state():
    try:
        with open(STATE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {
            "minecraft": {"urls": [], "used_urls": [], "is_running": False, "next_run": None, "last_run": None, "interval_hours": 5},
            "mrbeast": {"urls": [], "used_urls": [], "clip_queue": [], "is_running": False, "next_run": None, "last_run": None, "interval_hours": 5},
            "scheduler_pid": None
        }

def write_state(state):
    with open(STATE_PATH, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)

def is_pid_alive(pid):
    if not pid:
        return False
    try:
        process = psutil.Process(pid)
        return process.is_running()
    except psutil.NoSuchProcess:
        return False
    except Exception:
        return False

# ── URL Library ──
@app.get("/api/url-library")
async def get_url_library(channel: str):
    state = read_state()
    ch = state.get(channel)
    if not ch:
        raise HTTPException(status_code=400, detail="Invalid channel")
    return {"urls": ch.get("urls", []), "used_urls": ch.get("used_urls", [])}

@app.post("/api/url-library")
async def add_url(data: UrlLibraryRequest):
    state = read_state()
    if data.channel not in state:
        raise HTTPException(status_code=400, detail="Invalid channel")
    
    ch = state[data.channel]
    all_urls = ch.get("urls", []) + ch.get("used_urls", [])
    if data.url in all_urls:
        raise HTTPException(status_code=409, detail="URL already exists in library")
    
    ch["urls"] = ch.get("urls", []) + [data.url]
    write_state(state)
    return {"success": True, "urls": ch["urls"]}

@app.delete("/api/url-library")
async def remove_url(data: UrlLibraryRequest):
    state = read_state()
    if data.channel not in state:
        raise HTTPException(status_code=400, detail="Invalid channel")
    
    ch = state[data.channel]
    ch["urls"] = [u for u in ch.get("urls", []) if u != data.url]
    ch["used_urls"] = [u for u in ch.get("used_urls", []) if u != data.url]
    write_state(state)
    return {"success": True}

# ── Scheduler Controls ──
@app.get("/api/scheduler")
async def get_scheduler():
    state = read_state()
    return state

@app.post("/api/scheduler")
async def control_scheduler(data: SchedulerStartRequest):
    state = read_state()
    action = data.action
    channel = data.channel
    interval_hours = data.interval_hours or 5

    if action == 'start' and channel:
        if channel not in state:
            raise HTTPException(status_code=400, detail="Invalid channel")
        state[channel]["is_running"] = True
        state[channel]["interval_hours"] = interval_hours
        import datetime
        next_run_dt = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=interval_hours)
        state[channel]["next_run"] = next_run_dt.isoformat()
        write_state(state)
        return {"success": True, "message": f"Scheduler started for {channel}. Next run in {interval_hours}h."}

    if action == 'stop' and channel:
        if channel not in state:
            raise HTTPException(status_code=400, detail="Invalid channel")
        state[channel]["is_running"] = False
        state[channel]["next_run"] = None
        write_state(state)
        return {"success": True, "message": f"Scheduler stopped for {channel}."}

    if action == 'trigger_now' and channel:
        if channel not in state:
            raise HTTPException(status_code=400, detail="Invalid channel")
        import datetime
        state[channel]["next_run"] = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=10)).isoformat()
        if not state[channel]["is_running"]:
            state[channel]["is_running"] = True
        write_state(state)
        return {"success": True, "message": f"Triggered immediate run for {channel}."}

    if action == 'set_interval' and channel:
        if channel not in state:
            raise HTTPException(status_code=400, detail="Invalid channel")
        state[channel]["interval_hours"] = interval_hours
        write_state(state)
        return {"success": True, "message": f"Interval set to {interval_hours}h for {channel}."}

    if action == 'clear_queue' and channel == 'mrbeast':
        state["mrbeast"]["clip_queue"] = []
        write_state(state)
        return {"success": True, "message": "MrBeast clip queue cleared."}

    raise HTTPException(status_code=400, detail="Unknown action")

# ── Scheduler Process ──
@app.get("/api/scheduler-process")
async def get_scheduler_process():
    state = read_state()
    pid = state.get("scheduler_pid")
    alive = is_pid_alive(pid)
    if not alive and pid:
        state["scheduler_pid"] = None
        write_state(state)
    return {"running": alive, "pid": pid if alive else None}

@app.post("/api/scheduler-process")
async def control_scheduler_process(req: Request):
    body = await req.json()
    action = body.get("action")
    state = read_state()

    if action == 'start':
        if is_pid_alive(state.get("scheduler_pid")):
            return {"success": True, "message": "Scheduler already running.", "pid": state["scheduler_pid"]}
        
        script_path = os.path.join(os.getcwd(), 'scripts', 'auto_scheduler.py')
        # Spawn python3 process in background
        process = asyncio.create_subprocess_exec(
            "python3", script_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            start_new_session=True
        )
        proc = await process
        state["scheduler_pid"] = proc.pid
        write_state(state)
        return {"success": True, "message": "Scheduler process started.", "pid": proc.pid}

    if action == 'stop':
        pid = state.get("scheduler_pid")
        if not pid or not is_pid_alive(pid):
            state["scheduler_pid"] = None
            write_state(state)
            return {"success": True, "message": "Scheduler was not running."}
        try:
            p = psutil.Process(pid)
            p.terminate()
            state["scheduler_pid"] = None
            write_state(state)
            return {"success": True, "message": "Scheduler stopped."}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to stop: {str(e)}")

    raise HTTPException(status_code=400, detail="Unknown action")

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
