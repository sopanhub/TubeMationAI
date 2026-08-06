#!/usr/bin/env python3
"""
gemini_analyzer.py
──────────────────────────────────────────────────────────────────────────────
Gemini multi-modal video analyzer for the MrBeast pipeline.
Extracts the top 5 highest-retention clips (20-40s each) with structured
3-part voiceover scripts: HOOK → BODY → END.
"""

import json
import os
import re
import time
from pathlib import Path
from typing import Optional, List


def log(msg: str):
    print(msg, flush=True)


# ─── Master Prompt ─────────────────────────────────────────────────────────────

def get_gemini_master_prompt(num_clips: int = 5, avoid_timestamps: str = "") -> str:
    avoid_clause = ""
    if avoid_timestamps:
        avoid_clause = f"\n3. AVOID TIMESTAMPS: You MUST NOT pick any clips that overlap with these already generated timestamps: {avoid_timestamps}\n"

    return f"""
You are an expert viral YouTube Shorts editor specialized in retention engineering for high-energy content like MrBeast and IShowSpeed videos.

Analyze this video and extract the top {num_clips} moments BEST SUITED for highly viral YouTube Shorts.

CRITICAL CONSTRAINTS:
1. Every clip duration must be strictly between 15 seconds and 25 seconds maximum. Do not go under 15 seconds or over 25 seconds.
2. STRICT CLIP SEPARATION: You MUST select {num_clips} completely distinct segments from the video. The timestamps for each clip must be at least 60 seconds apart from each other. Do NOT pull multiple clips from the exact same scene or timestamp. Space them out across the entire video.{avoid_clause}

For each clip, provide exact Start/End timestamps.

You must return STRICTLY a raw JSON array with EXACTLY {num_clips} objects. NO markdown, NO ```json fences, NO commentary — just the raw array:

[
  {{
    "clip_number": 1,
    "start_time": "MM:SS",
    "end_time": "MM:SS",
    "duration_seconds": 20,
    "viral_title": "he is so so insaane?!"
  }}
]

ABSOLUTE RULES:
1. Return EXACTLY {num_clips} clips in the array.
2. duration_seconds for EVERY clip MUST be between 15 and 25.
3. start_time and end_time MUST be accurate real timestamps from the actual video content.
4. Identify moments with loud audio peaks, dramatic reactions, surprise reveals, challenge completions, or emotional climaxes.
5. Output ONLY the raw JSON array. Absolutely nothing else.
"""


# ─── Helpers ──────────────────────────────────────────────────────────────────

def parse_mm_ss(ts: str) -> float:
    """Convert 'MM:SS' or 'HH:MM:SS' to float seconds."""
    ts = ts.strip()
    parts = ts.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return float(ts)


def _clamp_clip(clip: dict) -> dict:
    """Enforce 15-25s duration on a single clip dict."""
    start = clip.get("start_sec", 30.0)
    end   = clip.get("end_sec", 50.0)
    dur   = end - start
    if dur < 15:
        end = start + 18  # extend to 18s minimum
        log(f"  ⚠ Clip {clip.get('clip_number','')} was {dur:.0f}s — extended to 18s.")
    elif dur > 25:
        end = start + 23  # trim to 23s
        log(f"  ⚠ Clip {clip.get('clip_number','')} was {dur:.0f}s — trimmed to 23s.")
    clip["end_sec"] = end
    clip["duration_seconds"] = end - start
    return clip


def _normalise_clip(raw: dict, idx: int) -> dict:
    """Parse timestamps and compute start_sec/end_sec."""
    start_sec = parse_mm_ss(raw.get("start_time", "0:30"))
    end_sec   = parse_mm_ss(raw.get("end_time", "1:00"))
    raw["start_sec"] = start_sec
    raw["end_sec"]   = end_sec
    raw["clip_number"] = raw.get("clip_number", idx + 1)
    
    # We no longer require hook_script

    return _clamp_clip(raw)


# ─── Robust JSON parser ───────────────────────────────────────────────────────

def _robust_json_parse(raw: str) -> list:
    """
    Try multiple strategies to extract a valid JSON array from Gemini output.
    Handles: markdown fences, trailing commas, JS comments, single quotes,
    embedded prose, and truncated responses.
    """
    def _attempt(text: str):
        return json.loads(text)

    def _clean(text: str) -> str:
        # 1. Strip markdown code fences
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text.strip())
        # 2. Remove JS-style single-line comments  // ...
        text = re.sub(r"//[^\n]*", "", text)
        # 3. Remove JS-style block comments /* ... */
        text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
        # 4. Remove trailing commas before ] or }
        text = re.sub(r",\s*([}\]])", r"\1", text)
        # 5. Replace Python/JS True/False/None
        text = re.sub(r"\bTrue\b", "true", text)
        text = re.sub(r"\bFalse\b", "false", text)
        text = re.sub(r"\bNone\b", "null", text)
        return text.strip()

    # Strategy 1: clean then parse
    try:
        return _attempt(_clean(raw))
    except Exception:
        pass

    # Strategy 2: extract first [...] block from the text
    try:
        m = re.search(r"(\[.*\])", raw, re.DOTALL)
        if m:
            return _attempt(_clean(m.group(1)))
    except Exception:
        pass

    # Strategy 3: extract first {...} block and wrap in list
    try:
        m = re.search(r"(\{.*\})", raw, re.DOTALL)
        if m:
            result = _attempt(_clean(m.group(1)))
            return result if isinstance(result, list) else [result]
    except Exception:
        pass

    # Strategy 4: use json5 if available (handles single quotes etc.)
    try:
        import json5  # type: ignore
        return json5.loads(_clean(raw))
    except Exception:
        pass

    raise ValueError(f"All JSON parse strategies failed. Raw (first 600 chars):\n{raw[:600]}")


# ─── Gemini analysis ──────────────────────────────────────────────────────────

def analyze_with_gemini(video_path: Path, youtube_url: Optional[str] = None, num_clips: int = 5, avoid_timestamps: str = "") -> Optional[List[dict]]:
    """
    Upload video to Gemini Files API (or use YouTube URL directly) and analyze with the master prompt.
    Returns a list of up to `num_clips` clip dicts, or None on failure.
    """
    try:
        from google import genai
        from google.genai import types
        from google.api_core import exceptions as google_exceptions
    except ImportError:
        raise RuntimeError("google-genai not installed. Run: pip install google-genai")

    from dotenv import load_dotenv
    load_dotenv(override=True)

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in .env")

    client = genai.Client(api_key=api_key)

    if not youtube_url and video_path:
        proxy_path = video_path.parent / "gemini_proxy.mp4"
        if not proxy_path.exists():
            log("  Creating a lightweight proxy video for faster Gemini processing...")
            import subprocess
            subprocess.run([
                "ffmpeg", "-y", "-i", str(video_path),
                "-vf", "scale=-2:360", "-r", "15", "-b:v", "300k", "-b:a", "64k",
                str(proxy_path)
            ], capture_output=True)
            if proxy_path.exists():
                log("  ✅ Proxy created successfully.")
        
        upload_target = proxy_path if proxy_path.exists() else video_path
    else:
        upload_target = video_path

    MAX_RETRIES = 5
    BASE_WAIT   = 60

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            if youtube_url:
                log(f"  Using YouTube URL directly for Gemini: {youtube_url}")
                video_file = None
            else:
                log(f"  Uploading video to Gemini Files API (attempt {attempt}/{MAX_RETRIES})...")
                video_file = client.files.upload(
                    file=str(upload_target),
                    config={"display_name": upload_target.name}
                )
    
                max_wait_time = 60  # 1 minute max wait
                wait_elapsed = 0
                while video_file.state == "PROCESSING":
                    if wait_elapsed >= max_wait_time:
                        raise RuntimeError("Gemini processing timed out after 1 minute.")
                    log("  ... video is processing, waiting 10s ...")
                    time.sleep(10)
                    wait_elapsed += 10
                    video_file = client.files.get(name=video_file.name)
    
                if video_file.state == "FAILED":
                    raise RuntimeError("Gemini processing failed.")
    
                log("  Video ready. Asking Gemini to find top 5 viral moments...")

            # Prepend URL to prompt if using youtube url
            prompt = get_gemini_master_prompt(num_clips, avoid_timestamps)
            if youtube_url:
                prompt = f"Here is the YouTube video link: {youtube_url}\n\n" + prompt

            contents = [video_file, prompt] if video_file else [prompt]
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.35,
                    max_output_tokens=8192,
                )
            )

            raw_text = response.text.strip()
            log(f"  Gemini response received ({len(raw_text)} chars).")
            log(f"  [DEBUG] Raw Gemini output: {raw_text[:500]}")

            clips_raw = _robust_json_parse(raw_text)

            if not isinstance(clips_raw, list):
                clips_raw = [clips_raw]  # handle if Gemini returned a single object

            clips = [_normalise_clip(c, i) for i, c in enumerate(clips_raw)]

            log(f"  Gemini found {len(clips)} clip(s):")
            for c in clips:
                log(f"    #{c['clip_number']}: {c.get('start_time')} -> {c.get('end_time')} ({c['duration_seconds']:.0f}s) — {c.get('viral_title', 'N/A')}")
                log(f"    Script: {c.get('hook_script', 'None')}")

            return clips

        except Exception as e:
            from google.genai.errors import APIError
            if (isinstance(e, APIError) and getattr(e, "code", 200) in [429, 500, 503]) or isinstance(e, ValueError):
                wait = BASE_WAIT * attempt
                log(f"  Gemini error/parse failure (attempt {attempt}/{MAX_RETRIES}): {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                log(f"  Gemini analysis failed: {e}")
                import traceback
                traceback.print_exc()
                break

    return None


# ─── Public entry point ───────────────────────────────────────────────────────

def get_all_clips(video_path: Path, youtube_url: Optional[str] = None, num_clips: int = 5, avoid_timestamps: str = "") -> List[dict]:
    """Main entry — returns top `num_clips` clips via Gemini."""
    clips = analyze_with_gemini(video_path, youtube_url, num_clips, avoid_timestamps)
    if not clips:
        raise RuntimeError("Gemini analysis failed. PySceneDetect fallback has been disabled by user request.")
    return clips


# Keep a single-clip alias for backwards compatibility
def get_best_clip(video_path: Path, youtube_url: Optional[str] = None, avoid_timestamps: str = "") -> dict:
    """Returns only the #1 highest-retention clip."""
    return get_all_clips(video_path, youtube_url, avoid_timestamps=avoid_timestamps)[0]


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("Usage: gemini_analyzer.py <video_path>")
        sys.exit(1)
    clips = get_all_clips(Path(sys.argv[1]))
    print(json.dumps(clips, indent=2))
