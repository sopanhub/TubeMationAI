import re
from pathlib import Path

path = Path("scripts/mrbeast_generator.py")
content = path.read_text()

# 1. Update ytdlp_download to stream output in real time and remove --quiet
old_ytdlp = """def ytdlp_download(url: str, out_path: Path, extra_args: List[str] = None) -> bool:
    \"\"\"Download a YouTube video to out_path using yt-dlp. Returns True on success.\"\"\"
    args = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best",
        "--merge-output-format", "mp4",
        "-o", str(out_path),
        "--quiet", "--no-warnings",
    ]
    if extra_args:
        args += extra_args
    args.append(url)
    try:
        run(args)
        return out_path.exists() and out_path.stat().st_size > 1024 * 50
    except subprocess.CalledProcessError as e:
        log(f"  ❌ yt-dlp failed: {e.stderr[:300]}")
        return False"""

new_ytdlp = """def ytdlp_download(url: str, out_path: Path, extra_args: List[str] = None) -> bool:
    \"\"\"Download a YouTube video to out_path using yt-dlp. Returns True on success.\"\"\"
    args = [
        "yt-dlp",
        "-f", "bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]/best",
        "--merge-output-format", "mp4",
        "-o", str(out_path),
    ]
    if extra_args:
        args += extra_args
    args.append(url)
    
    try:
        # Run Popen to stream progress bar and download size logs in real time
        process = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
        )
        for line in process.stdout:
            cleaned = line.strip()
            if cleaned:
                log(f"  [yt-dlp] {cleaned}")
        process.wait()
        return out_path.exists() and out_path.stat().st_size > 1024 * 50
    except Exception as e:
        log(f"  ❌ yt-dlp download process error: {e}")
        return False"""

content = content.replace(old_ytdlp, new_ytdlp)

# 2. Fix the mediapipe import issue
old_mp = """    try:
        import mediapipe as mp
        mp_face = mp.solutions.face_detection
    except ImportError:"""

new_mp = """    try:
        import mediapipe as mp
        import mediapipe.python.solutions.face_detection as mp_face
    except (ImportError, AttributeError):"""

content = content.replace(old_mp, new_mp)

path.write_text(content)
print("Patch successfully applied!")
