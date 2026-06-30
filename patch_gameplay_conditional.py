import re
from pathlib import Path

path = Path("scripts/mrbeast_generator.py")
content = path.read_text()

# 1. Update compose_dual_screen signature and body to handle optional bottom_path
old_compose = """def compose_dual_screen(top_path: Path, bottom_path: Path, out_path: Path, duration: float) -> Path:
    \"\"\"Stack top (face-tracked) and bottom (gameplay) frames into one 9:16 video.\"\"\"
    log("  Composing dual-screen layout…")

    top_cap = cv2.VideoCapture(str(top_path))
    bot_cap = cv2.VideoCapture(str(bottom_path))
    fps = TARGET_FPS

    # Apply 1.03x rescale (visual mutation against Content ID)
    SCALE = 1.03
    scaled_w = int(TARGET_W * SCALE)
    scaled_h = int(TARGET_H * SCALE)
    pad_x = (scaled_w - TARGET_W) // 2
    pad_y = (scaled_h - TARGET_H) // 2

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (TARGET_W, TARGET_H))

    total = int(duration * fps)
    for i in range(total):
        ret_t, top_frame = top_cap.read()
        ret_b, bot_frame = bot_cap.read()

        if not ret_t:
            top_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            _, top_frame = top_cap.read()
        if not ret_b:
            bot_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            _, bot_frame = bot_cap.read()

        if top_frame is None or bot_frame is None:
            break

        # Ensure correct sizes
        top_frame = cv2.resize(top_frame, (TARGET_W, TOP_H))
        bot_frame = cv2.resize(bot_frame, (TARGET_W, BOTTOM_H))

        # Stack
        canvas = np.vstack([top_frame, bot_frame])

        # Rescale then centre-crop (pixel mutation)
        scaled = cv2.resize(canvas, (scaled_w, scaled_h))
        final = scaled[pad_y: pad_y + TARGET_H, pad_x: pad_x + TARGET_W]"""

new_compose = """def compose_dual_screen(top_path: Path, bottom_path: Optional[Path], out_path: Path, duration: float) -> Path:
    \"\"\"Stack top (face-tracked) and optional bottom (gameplay) frames into one 9:16 video.\"\"\"
    log("  Composing video layout…")

    top_cap = cv2.VideoCapture(str(top_path))
    bot_cap = cv2.VideoCapture(str(bottom_path)) if bottom_path else None
    fps = TARGET_FPS

    # Apply 1.03x rescale (visual mutation against Content ID)
    SCALE = 1.03
    scaled_w = int(TARGET_W * SCALE)
    scaled_h = int(TARGET_H * SCALE)
    pad_x = (scaled_w - TARGET_W) // 2
    pad_y = (scaled_h - TARGET_H) // 2

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (TARGET_W, TARGET_H))

    total = int(duration * fps)
    for i in range(total):
        ret_t, top_frame = top_cap.read()

        if not ret_t:
            top_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            _, top_frame = top_cap.read()

        if top_frame is None:
            break

        if bot_cap:
            ret_b, bot_frame = bot_cap.read()
            if not ret_b:
                bot_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                _, bot_frame = bot_cap.read()
            if bot_frame is None:
                break
            # Ensure correct sizes
            top_frame = cv2.resize(top_frame, (TARGET_W, TOP_H))
            bot_frame = cv2.resize(bot_frame, (TARGET_W, BOTTOM_H))
            # Stack
            canvas = np.vstack([top_frame, bot_frame])
        else:
            canvas = cv2.resize(top_frame, (TARGET_W, TARGET_H))

        # Rescale then centre-crop (pixel mutation)
        scaled = cv2.resize(canvas, (scaled_w, scaled_h))
        final = scaled[pad_y: pad_y + TARGET_H, pad_x: pad_x + TARGET_W]"""

content = content.replace(old_compose, new_compose)

# Update post-processing loop of compose_dual_screen to safely release bot_cap
old_release = """    top_cap.release()
    bot_cap.release()
    writer.release()
    log("  ✅ Dual-screen composition done.")"""

new_release = """    top_cap.release()
    if bot_cap:
        bot_cap.release()
    writer.release()
    log("  ✅ Video composition done.")"""

content = content.replace(old_release, new_release)

# 2. Update main() logic
old_main_logic = """    # ── 3. Face-tracked crop (top portion)
    log("[3/9] Tracking face and cropping to vertical…")
    top_tracked = WORK_DIR / "top_tracked.mp4"
    track_and_crop(main_raw, start_sec, end_sec, top_tracked)

    # ── 4. Gameplay
    log("[4/9] Preparing gameplay footage…")
    gameplay_raw = get_gameplay(args.gameplay_url, WORK_DIR)
    gameplay_cropped = WORK_DIR / "gameplay_cropped.mp4"
    crop_gameplay(gameplay_raw, gameplay_cropped)

    # ── 5. Dual-screen composition
    log("[5/9] Composing dual-screen layout…")
    dual_silent = WORK_DIR / "dual_silent.mp4"
    compose_dual_screen(top_tracked, gameplay_cropped, dual_silent, clip_duration)"""

new_main_logic = """    has_gameplay = args.gameplay_url is not None

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
    compose_dual_screen(top_tracked, gameplay_cropped, dual_silent, clip_duration)"""

content = content.replace(old_main_logic, new_main_logic)

path.write_text(content)
print("Patch successfully applied!")
