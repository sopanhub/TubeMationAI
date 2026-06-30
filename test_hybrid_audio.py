import subprocess
from pathlib import Path

def create_hybrid_audio(original_video: Path, tts_audio: Path, start_sec: float, dur: float, out_path: Path):
    # 1. Get TTS duration using ffprobe
    res = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(tts_audio)],
        capture_output=True, text=True
    )
    tts_dur = float(res.stdout.strip())
    
    if tts_dur >= dur:
        # TTS is longer than the clip, just use TTS
        pass

    # We need:
    # [0:a] is TTS
    # [1:a] is original video audio, starting from start_sec. We want the piece from (start_sec + tts_dur) to (start_sec + dur).
    
    # Actually, the simplest way is to extract the whole clip audio first:
    clip_audio = out_path.parent / "clip_audio_temp.wav"
    subprocess.run([
        "ffmpeg", "-y", "-ss", str(start_sec), "-t", str(dur),
        "-i", str(original_video),
        "-q:a", "0", "-map", "a", str(clip_audio)
    ], capture_output=True)

    # Now we combine them. We want TTS at the start, and clip_audio from tts_dur onwards.
    # ffmpeg -i tts -i clip_audio -filter_complex "[1:a]atrim=start=tts_dur[part2]; [0:a][part2]concat=n=2:v=0:a=1[out]"
    
    filter_complex = f"[1:a]atrim=start={tts_dur},asetpts=PTS-STARTPTS[part2]; [0:a][part2]concat=n=2:v=0:a=1[out]"
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(tts_audio),
        "-i", str(clip_audio),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        str(out_path)
    ], capture_output=True)

