from pathlib import Path

path = Path("scripts/mrbeast_generator.py")
content = path.read_text()

# 1. Replace old detect_best_scene with Gemini-powered get_best_clip
old_scene = """# ─── Stage 2: PySceneDetect – find first good scene ───────────────────────────

def detect_best_scene(video_path: Path, target_duration: float) -> Tuple[float, float]:
    \"\"\"Return (start_sec, end_sec) of the best non-intro scene to clip.\"\"\"
    log("  Detecting scene cuts…")
    try:
        from scenedetect import detect, ContentDetector
        scene_list = detect(str(video_path), ContentDetector(threshold=27))
        # Skip first 30 seconds (often intro/branding) and find a scene >= target_duration
        for scene in scene_list:
            s = scene[0].get_seconds()
            e = scene[1].get_seconds()
            if s >= 30 and (e - s) >= 10:
                end = min(s + target_duration, e)
                log(f"  Scene selected: {s:.1f}s → {end:.1f}s")
                return s, end
        # Fallback: just use from 30s onward
        log("  No ideal scene found, using 30s → 90s fallback.")
        return 30.0, 30.0 + target_duration
    except ImportError:
        log("  ⚠ scenedetect not available, using offset fallback.")
        return 30.0, 30.0 + target_duration"""

new_scene = """# ─── Stage 2: Gemini AI Viral Segment Analyzer ──────────────────────────────

def get_best_clip(video_path: Path) -> dict:
    \"\"\"Ask Gemini to find the single most viral 25-40s segment. Falls back to PySceneDetect.\"\"\"
    sys.path.insert(0, str(SCRIPT_DIR))
    from gemini_analyzer import get_best_clip as _analyzer
    return _analyzer(video_path)"""

content = content.replace(old_scene, new_scene)

# 2. Update the main() pipeline to use Gemini clip data & voiceover
old_pipeline = """    log("=== MrBeast Generator Pipeline Started ===")
    t0 = time.time()

    # ── 1. Download main video
    log("[1/9] Downloading main video…")
    main_raw = download_main(args.url, WORK_DIR)

    # ── 2. Detect scene
    log("[2/9] Detecting scenes…")
    start_sec, end_sec = detect_best_scene(main_raw, CLIP_DURATION)
    clip_duration = end_sec - start_sec

    has_gameplay = args.gameplay_url is not None

    # ── 3. Face-tracked crop
    log("[3/9] Tracking face and cropping to vertical…")
    top_tracked = WORK_DIR / "top_tracked.mp4"
    if has_gameplay:
        track_and_crop(main_raw, start_sec, end_sec, top_tracked, TARGET_W, TOP_H)
    else:
        track_and_crop(main_raw, start_sec, end_sec, top_tracked, TARGET_W, TARGET_H)

    # ── 4. Gameplay
    gameplay_cropped = None
    if has_gameplay:
        log("[4/9] Preparing gameplay footage…")
        gameplay_raw = get_gameplay(args.gameplay_url, WORK_DIR)
        gameplay_cropped = WORK_DIR / "gameplay_cropped.mp4"
        crop_gameplay(gameplay_raw, gameplay_cropped)
    else:
        log("[4/9] Skipping gameplay (single-screen mode)…")

    # ── 5. Video composition
    log("[5/9] Composing video layout…")
    dual_silent = WORK_DIR / "dual_silent.mp4"
    compose_dual_screen(top_tracked, gameplay_cropped, dual_silent, clip_duration)

    # ── 6. Extract audio & Whisper transcription
    log("[6/9] Running Whisper transcription…")
    raw_audio = WORK_DIR / "raw_audio.wav"
    words = transcribe_video(main_raw, raw_audio)

    # ── 7. Captions
    log("[7/9] Rendering MrBeast-style captions…")
    if words:
        chunks = chunk_words(words, chunk_size=3)
        captioned_video = WORK_DIR / "captioned.mp4"
        overlay_captions_on_video(dual_silent, chunks, captioned_video)
    else:
        log("  ⚠ No words to caption, skipping caption overlay.")
        captioned_video = dual_silent

    # ── 8. Audio mutations
    log("[8/9] Mutating audio (Content ID evasion)…")
    lofi = download_lofi(WORK_DIR)
    mutated_audio = WORK_DIR / "mutated_audio.mp3"
    apply_audio_mutations(main_raw, raw_audio, lofi, mutated_audio, clip_duration)

    # ── 9. Final encode
    log("[9/9] Final encode…")
    mux_and_encode(captioned_video, mutated_audio, OUTPUT_PATH)

    elapsed = time.time() - t0
    log(f"=== Pipeline complete in {elapsed:.0f}s. Output: {OUTPUT_PATH} ===\")"""

new_pipeline = """    log("=== MrBeast Generator Pipeline Started ===")
    t0 = time.time()

    # ── 1. Download main video
    log("[1/9] Downloading main video…")
    main_raw = download_main(args.url, WORK_DIR)

    # ── 2. Gemini AI analysis — find the most viral 25-40s segment + voiceover script
    log("[2/9] Asking Gemini AI to find the best viral segment…")
    clip_data = get_best_clip(main_raw)
    start_sec    = clip_data["start_sec"]
    end_sec      = clip_data["end_sec"]
    clip_duration = clip_data["duration_seconds"]
    viral_title   = clip_data.get("viral_title", "")
    vo_script     = clip_data.get("voiceover_script", "")

    if viral_title:
        log(f"  🎯 Viral title: {viral_title}")
    log(f"  ⏱ Clip: {start_sec:.1f}s → {end_sec:.1f}s ({clip_duration:.0f}s)")

    has_gameplay = args.gameplay_url is not None

    # ── 3. Face-tracked crop
    log("[3/9] Tracking face and cropping to vertical…")
    top_tracked = WORK_DIR / "top_tracked.mp4"
    if has_gameplay:
        track_and_crop(main_raw, start_sec, end_sec, top_tracked, TARGET_W, TOP_H)
    else:
        track_and_crop(main_raw, start_sec, end_sec, top_tracked, TARGET_W, TARGET_H)

    # ── 4. Gameplay
    gameplay_cropped = None
    if has_gameplay:
        log("[4/9] Preparing gameplay footage…")
        gameplay_raw = get_gameplay(args.gameplay_url, WORK_DIR)
        gameplay_cropped = WORK_DIR / "gameplay_cropped.mp4"
        crop_gameplay(gameplay_raw, gameplay_cropped)
    else:
        log("[4/9] Skipping gameplay (single-screen mode)…")

    # ── 5. Video composition
    log("[5/9] Composing video layout…")
    dual_silent = WORK_DIR / "dual_silent.mp4"
    compose_dual_screen(top_tracked, gameplay_cropped, dual_silent, clip_duration)

    # ── 6. Generate TTS from Gemini voiceover script + Whisper word-level captions
    log("[6/9] Generating TTS voiceover from Gemini script…")
    raw_audio = WORK_DIR / "raw_audio.wav"

    if vo_script:
        log(f"  🎙️ Voiceover: \"{vo_script[:80]}…\"")
        # Write the script to a temp text file to track it
        script_file = WORK_DIR / "vo_script.txt"
        script_file.write_text(vo_script, encoding="utf-8")
        # Generate TTS audio from Gemini's script using edge-tts / fallback
        tts_audio = _generate_tts_voiceover(vo_script, WORK_DIR)
        if tts_audio and tts_audio.exists():
            raw_audio = tts_audio
            words = _words_from_tts_script(vo_script, tts_audio)
        else:
            log("  ⚠ TTS failed. Falling back to Whisper transcription.")
            words = transcribe_video(main_raw, raw_audio)
    else:
        log("  ⚠ No voiceover script from Gemini — running Whisper transcription.")
        words = transcribe_video(main_raw, raw_audio)

    # ── 7. Captions
    log("[7/9] Rendering MrBeast-style captions…")
    if words:
        chunks = chunk_words(words, chunk_size=3)
        captioned_video = WORK_DIR / "captioned.mp4"
        overlay_captions_on_video(dual_silent, chunks, captioned_video)
    else:
        log("  ⚠ No words to caption, skipping caption overlay.")
        captioned_video = dual_silent

    # ── 8. Audio mutations
    log("[8/9] Mutating audio (Content ID evasion)…")
    lofi = download_lofi(WORK_DIR)
    mutated_audio = WORK_DIR / "mutated_audio.mp3"
    apply_audio_mutations(main_raw, raw_audio, lofi, mutated_audio, clip_duration)

    # ── 9. Final encode
    log("[9/9] Final encode…")
    mux_and_encode(captioned_video, mutated_audio, OUTPUT_PATH)

    elapsed = time.time() - t0
    log(f"=== Pipeline complete in {elapsed:.0f}s. Output: {OUTPUT_PATH} ===\")"""

content = content.replace(old_pipeline, new_pipeline)
Path("scripts/mrbeast_generator.py").write_text(content)
print("Pipeline integration patch applied.")
