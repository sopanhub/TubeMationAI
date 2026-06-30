import re
from pathlib import Path

path = Path("scripts/mrbeast_generator.py")
content = path.read_text()

# 1. Update config globals to support re-assignment
old_globals = """# ─── Config ───────────────────────────────────────────────────────────────────

TARGET_W = 1080
TARGET_H = 1920
TARGET_FPS = 60
CLIP_DURATION = 60.0       # seconds to take from the main video
GAMEPLAY_DURATION = 60.0   # seconds of bottom gameplay

SPLIT_RATIO = 0.58          # top portion for the face-tracked speaker
BOTTOM_H = int(TARGET_H * (1 - SPLIT_RATIO))
TOP_H    = TARGET_H - BOTTOM_H"""

new_globals = """# ─── Config ───────────────────────────────────────────────────────────────────

TARGET_W = 1080
TARGET_H = 1920
TARGET_FPS = 60
ENCODING_PRESET = "slow"
ENCODING_CRF = "14"
CLIP_DURATION = 60.0       # seconds to take from the main video
GAMEPLAY_DURATION = 60.0   # seconds of bottom gameplay

SPLIT_RATIO = 0.58          # top portion for the face-tracked speaker
BOTTOM_H = int(TARGET_H * (1 - SPLIT_RATIO))
TOP_H    = TARGET_H - BOTTOM_H"""

content = content.replace(old_globals, new_globals)

# 2. Update mux_and_encode to use the dynamic preset/CRF and print the file size
old_mux = """def mux_and_encode(video_path: Path, audio_path: Path, out_path: Path) -> Path:
    \"\"\"Combine video (mp4v) and mutated audio → final H.264 MP4.\"\"\"
    log(f"  Writing final video: {out_path}")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-preset", "slow",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "320k",
        "-movflags", "+faststart",
        "-shortest",
        str(out_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if out_path.exists() and out_path.stat().st_size > 1024 * 100:
        log(f"  ✅ DONE: {out_path}")
        return out_path"""

new_mux = """def mux_and_encode(video_path: Path, audio_path: Path, out_path: Path) -> Path:
    \"\"\"Combine video (mp4v) and mutated audio → final H.264 MP4.\"\"\"
    log(f"  Writing final video: {out_path}")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-preset", ENCODING_PRESET,
        "-crf", ENCODING_CRF,
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "320k",
        "-movflags", "+faststart",
        "-shortest",
        str(out_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if out_path.exists() and out_path.stat().st_size > 1024 * 100:
        size_mb = out_path.stat().st_size / (1024 * 1024)
        log(f"FINAL_FILE_SIZE: {size_mb:.2f} MB")
        log(f"  ✅ DONE: {out_path}")
        return out_path"""

content = content.replace(old_mux, new_mux)

# 3. Update main() arguments and dynamic global re-assignment
old_main_args = """def main():
    parser = argparse.ArgumentParser(description="MrBeast Shorts Generator")
    parser.add_argument("--url", required=True, help="Main video YouTube URL")
    parser.add_argument("--gameplay-url", default=None, help="Gameplay bottom-screen URL (optional)")
    args = parser.parse_args()

    WORK_DIR.mkdir(parents=True, exist_ok=True)"""

new_main_args = """def main():
    global TARGET_W, TARGET_H, TARGET_FPS, ENCODING_PRESET, ENCODING_CRF, BOTTOM_H, TOP_H
    parser = argparse.ArgumentParser(description="MrBeast Shorts Generator")
    parser.add_argument("--url", required=True, help="Main video YouTube URL")
    parser.add_argument("--gameplay-url", default=None, help="Gameplay bottom-screen URL (optional)")
    parser.add_argument("--quality", default="high", choices=["low", "medium", "high"], help="Video quality preset")
    args = parser.parse_args()

    if args.quality == "low":
        TARGET_W = 480
        TARGET_H = 854
        TARGET_FPS = 30
        ENCODING_PRESET = "fast"
        ENCODING_CRF = "22"
    elif args.quality == "medium":
        TARGET_W = 720
        TARGET_H = 1280
        TARGET_FPS = 30
        ENCODING_PRESET = "medium"
        ENCODING_CRF = "18"
    else:  # high
        TARGET_W = 1080
        TARGET_H = 1920
        TARGET_FPS = 60
        ENCODING_PRESET = "slow"
        ENCODING_CRF = "14"

    BOTTOM_H = int(TARGET_H * (1 - SPLIT_RATIO))
    TOP_H    = TARGET_H - BOTTOM_H

    WORK_DIR.mkdir(parents=True, exist_ok=True)"""

content = content.replace(old_main_args, new_main_args)

path.write_text(content)
print("Quality selector patch applied to python script.")
