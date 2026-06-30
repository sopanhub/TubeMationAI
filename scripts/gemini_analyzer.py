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

GEMINI_MASTER_PROMPT = """
You are an expert viral YouTube Shorts editor specialized in retention engineering for high-energy content like MrBeast and IShowSpeed videos.

Analyze this video and extract the top 5 moments BEST SUITED for highly viral YouTube Shorts.

CRITICAL CONSTRAINT: Every clip duration must be strictly between 20 seconds and 40 seconds maximum. Do not go under 20 seconds or over 40 seconds.

For each clip, provide exact Start/End timestamps and break the voiceover_script into 3 parts:
- HOOK (0-4 seconds): High-energy opener to instantly grab attention and stop the scroll.
- BODY (4 to end-5 seconds): The core challenge, climax, or high-intensity action narrative.
- END (last 3-5 seconds): A rapid closing loop or clean call-to-action.

You must return STRICTLY a raw JSON array with EXACTLY 5 objects. NO markdown, NO ```json fences, NO commentary — just the raw array:

[
  {
    "clip_number": 1,
    "start_time": "MM:SS",
    "end_time": "MM:SS",
    "duration_seconds": 30,
    "viral_title": "He survived 24 hours underground for THIS?!",
    "hook_type": "Extreme Challenge Reveal",
    "hook": "Nobody thought he would actually do it. But here we are.",
    "body": "For twenty four hours straight, with zero food, zero light, and temperatures dropping below freezing, he pushed through every single limit. The moment his team tried to pull him out early, he refused. This is what REAL determination looks like.",
    "end": "Drop a fire emoji if you thought he was gonna quit. Part two drops tomorrow.",
    "voiceover_script": "Nobody thought he would actually do it. But here we are. For twenty four hours straight, with zero food, zero light, and temperatures dropping below freezing, he pushed through every single limit. The moment his team tried to pull him out early, he refused. This is what REAL determination looks like. Drop a fire emoji if you thought he was gonna quit. Part two drops tomorrow."
  }
]

ABSOLUTE RULES:
1. Return EXACTLY 5 clips in the array. Not more, not fewer.
2. duration_seconds for EVERY clip MUST be between 20 and 40. Non-negotiable.
3. start_time and end_time MUST be accurate real timestamps from the actual video content.
4. Write ALL numbers as spoken words in voiceover_script (e.g. 'twenty four' not '24', 'five hundred thousand' not '$500,000') because this is fed directly to text-to-speech.
5. The voiceover_script should be 50-90 words — energetic, dramatic, fast-paced storytelling.
6. Identify moments with loud audio peaks, dramatic reactions, surprise reveals, challenge completions, or emotional climaxes.
7. Space the clips throughout the video — do NOT cluster them all at the beginning.
8. Output ONLY the raw JSON array. Absolutely nothing else.
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
    """Enforce 20-40s duration on a single clip dict."""
    start = clip.get("start_sec", 30.0)
    end   = clip.get("end_sec", 60.0)
    dur   = end - start
    if dur < 20:
        end = start + 25  # extend to 25s minimum
        log(f"  ⚠ Clip {clip.get('clip_number','')} was {dur:.0f}s — extended to 25s.")
    elif dur > 40:
        end = start + 38  # trim to 38s
        log(f"  ⚠ Clip {clip.get('clip_number','')} was {dur:.0f}s — trimmed to 38s.")
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

    # Build combined voiceover_script from parts if not already present
    if not raw.get("voiceover_script"):
        parts = " ".join(filter(None, [
            raw.get("hook", ""),
            raw.get("body", ""),
            raw.get("end", ""),
        ]))
        raw["voiceover_script"] = parts.strip()

    return _clamp_clip(raw)


# ─── Gemini analysis ──────────────────────────────────────────────────────────

def analyze_with_gemini(video_path: Path) -> Optional[List[dict]]:
    """
    Upload video to Gemini Files API and analyze with the master prompt.
    Returns a list of up to 5 clip dicts, or None on failure.
    """
    try:
        import google.generativeai as google_genai
        from google.api_core import exceptions as google_exceptions
    except ImportError:
        raise RuntimeError("google-generativeai not installed. Run: pip install google-generativeai")

    from dotenv import load_dotenv
    load_dotenv(override=True)

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set in .env")

    google_genai.configure(api_key=api_key)

    MAX_RETRIES = 5
    BASE_WAIT   = 60

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            log(f"  Uploading video to Gemini Files API (attempt {attempt}/{MAX_RETRIES})...")
            video_file = google_genai.upload_file(
                path=str(video_path),
                display_name=video_path.name
            )

            while video_file.state.name == "PROCESSING":
                log("  ... video is processing, waiting 10s ...")
                time.sleep(10)
                video_file = google_genai.get_file(name=video_file.name)

            if video_file.state.name == "FAILED":
                raise RuntimeError(f"Gemini processing failed: {video_file.error}")

            log("  Video ready. Asking Gemini to find top 5 viral moments...")

            model = google_genai.GenerativeModel(model_name="models/gemini-2.0-flash")
            response = model.generate_content(
                [video_file, GEMINI_MASTER_PROMPT],
                generation_config=google_genai.GenerationConfig(
                    temperature=0.35,
                    max_output_tokens=4096,
                )
            )

            raw_text = response.text.strip()
            log(f"  Gemini response received ({len(raw_text)} chars).")

            # Strip any accidental markdown
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text.strip())

            clips_raw = json.loads(raw_text)

            if not isinstance(clips_raw, list):
                clips_raw = [clips_raw]  # handle if Gemini returned a single object

            clips = [_normalise_clip(c, i) for i, c in enumerate(clips_raw)]

            log(f"  Gemini found {len(clips)} clip(s):")
            for c in clips:
                log(f"    #{c['clip_number']}: {c.get('start_time')} -> {c.get('end_time')} ({c['duration_seconds']:.0f}s) — {c.get('viral_title', 'N/A')}")

            return clips

        except (google_exceptions.ResourceExhausted, google_exceptions.InternalServerError) as e:
            wait = BASE_WAIT * attempt
            log(f"  Gemini rate limited (attempt {attempt}/{MAX_RETRIES}). Retrying in {wait}s...")
            time.sleep(wait)
        except Exception as e:
            log(f"  Gemini analysis failed: {e}")
            import traceback
            traceback.print_exc()
            break

    log("  Gemini analysis failed. Switching to PySceneDetect fallback.")
    return None


# ─── Fallback ─────────────────────────────────────────────────────────────────

def fallback_scenes(video_path: Path) -> List[dict]:
    """PySceneDetect fallback — returns up to 5 scene clips."""
    log("  Running PySceneDetect fallback...")
    clips = []
    try:
        from scenedetect import detect, ContentDetector
        scene_list = detect(str(video_path), ContentDetector(threshold=27))
        for i, scene in enumerate(scene_list):
            if len(clips) >= 5:
                break
            s = scene[0].get_seconds()
            e = scene[1].get_seconds()
            if s < 30 or (e - s) < 20:
                continue
            dur = min(e - s, 35)
            clips.append({
                "clip_number": len(clips) + 1,
                "start_sec": s,
                "end_sec": s + dur,
                "duration_seconds": dur,
                "start_time": f"{int(s)//60}:{int(s)%60:02d}",
                "end_time": f"{int(s+dur)//60}:{int(s+dur)%60:02d}",
                "viral_title": f"You won't believe what happens at #{len(clips)+1}!",
                "hook_type": "Dramatic Reveal",
                "hook": "Wait — you are NOT ready for this.",
                "body": "Nobody expected this moment to hit so hard. The energy, the chaos, the raw emotion on his face — this is the kind of content that breaks the internet every single time.",
                "end": "Drop a comment if this actually surprised you. Part two coming soon.",
                "voiceover_script": "Wait — you are NOT ready for this. Nobody expected this moment to hit so hard. The energy, the chaos, the raw emotion on his face — this is the kind of content that breaks the internet every single time. Drop a comment if this actually surprised you. Part two coming soon.",
            })
    except ImportError:
        pass

    # Fill remaining with hard-coded offsets
    while len(clips) < 5:
        i = len(clips)
        s = 30.0 + i * 45
        clips.append({
            "clip_number": i + 1,
            "start_sec": s,
            "end_sec": s + 30,
            "duration_seconds": 30,
            "start_time": f"{int(s)//60}:{int(s)%60:02d}",
            "end_time": f"{int(s+30)//60}:{int(s+30)%60:02d}",
            "viral_title": f"Clip #{i+1} — This is INSANE!",
            "hook_type": "Action Peak",
            "hook": "Nobody saw this coming.",
            "body": "This is one of the most unbelievable moments ever put on camera. If you blinked, you missed it. The crowd, the chaos, the reaction — absolutely legendary.",
            "end": "Like and follow for part two!",
            "voiceover_script": "Nobody saw this coming. This is one of the most unbelievable moments ever put on camera. If you blinked, you missed it. The crowd, the chaos, the reaction — absolutely legendary. Like and follow for part two!",
        })

    return clips


# ─── Public entry point ───────────────────────────────────────────────────────

def get_all_clips(video_path: Path) -> List[dict]:
    """Main entry — returns top 5 clips via Gemini or PySceneDetect fallback."""
    clips = analyze_with_gemini(video_path)
    if clips:
        return clips
    return fallback_scenes(video_path)


# Keep a single-clip alias for backwards compatibility
def get_best_clip(video_path: Path) -> dict:
    """Returns only the #1 highest-retention clip."""
    return get_all_clips(video_path)[0]


if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 2:
        print("Usage: gemini_analyzer.py <video_path>")
        sys.exit(1)
    clips = get_all_clips(Path(sys.argv[1]))
    print(json.dumps(clips, indent=2))
