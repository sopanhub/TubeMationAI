import re
from pathlib import Path

path = Path("scripts/video_generator.py")
content = path.read_text()

# 1. Update get_gemini_pairs signature
content = re.sub(
    r'def get_gemini_pairs\(video_path: Path, num_pairs: int\) -> List\[Dict\[str, float\]\]:',
    r'def get_gemini_pairs(video_path: Path) -> dict:',
    content
)

# 2. Update prompt
old_prompt = r'''            prompt = f"""
            You are a professional YouTube Shorts video editor\. Watch this Minecraft shader comparison video carefully\.
            Your task is to find exactly {num_pairs} pairs of timestamps showing the BEST before/after shader contrast\.
            For each pair, also identify the NAME of the shader pack being shown \(e\.g\. "BSL Shaders", "Complementary Shaders", etc\.\)\.
            
            CRITICAL VISUAL RULES:
            - Find gameplay that is FULL SCREEN\.
            - Do NOT select moments with black screens, heavy UI overlays, menus, or obstacles blocking the view\.
            - "vanilla_start" is the start of a clearly VANILLA \(no shader\) moment\.
            - "shader_start" is the start of a clearly SHADERS-ON moment\.
            - Space the pairs out\. Do NOT cluster them all at the start\.
            
            DESCRIPTION TASK:
            Write an engaging YouTube description using the following template, but replace \[SHADER_NAMES\] with the actual names you found:
            "Looking for the best ultra-realistic shaders for Minecraft Pocket Edition \(MCPE\) and Minecraft Bedrock Edition that work smoothly on lightweight, low-end, and mid-range devices\?\\nIn this video, we showcase \[SHADER_NAMES\] featuring stunning graphics, realistic lighting, beautiful skies, enhanced water reflections, volumetric fog, dynamic shadows, and an immersive next-generation visual experience—all without requiring a high-end phone or an RTX graphics card\!\\n\\n✨ Key Features\\nPerformance: Lightweight, FPS-friendly, and optimized for low-end devices\.\\nVisuals: Enhanced sky, realistic clouds, vibrant colors, and improved water visuals\.\\nLighting: Better sunlight, realistic moonlight, and dynamic shadow effects\.\\nAtmosphere: Smooth atmospheric effects and volumetric fog\.\\nAccessibility: 100% FREE to download with No RTX Required\.\\n\\n🔗 Download Links\\n👉 Get all the shaders featured in this video here: 👇\\nhttps://www\.piglixmcmods\.dev/\\n\\n💬 Join the Conversation\!\\nWhich shader was your favorite\? Comment the name below\! 👇\\nWhat shader pack or mod should I review next\? Let me know in the comments\!\\nDon't forget to Like and Subscribe for more Minecraft Bedrock content\! 👍\\n🔍 SEO & Keywords \(Search Optimization\)\\nBSL, Newb, SEUS, SLS, Complementary realistic minecraft shaders, mcpe shaders, render dragon shaders, low-end device shaders, no lag shaders, minecraft, minecraft shaders, realistic minecraft, minecraft mod, minecraft texture pack, minecraft java, minecraft bedrock, best minecraft shaders, gaming shorts, viral minecraft, shader pack tutorial\.\\n\\n🏷️ Tags\\n#MinecraftPE #MinecraftShaders #MCPE #BedrockEdition #patchshaders #mcpeshaders #BSLShaders #NewbShaders #SEUSShaders #SLSShaders #ComplementaryShaders"
            
            Return ONLY a valid JSON object, no other text\. Format:
            {{
              "description": "Your full description text here, exactly as generated with newlines",
              "pairs": \[
                {{"shader_name": "\.\.\.", "vanilla_start": 0\.0, "shader_start": 0\.0}}
              \]
            }}
            """'''

new_prompt = r'''            prompt = f"""
            You are a professional YouTube Shorts video editor. Watch this Minecraft shader comparison video carefully.
            Your task is to find ALL the unique shader packs showcased in the video.
            For each shader pack you find, extract ONE perfect before/after timestamp pair showing the BEST contrast.
            Also identify the NAME of the shader pack being shown (e.g. "BSL Shaders", "Complementary Shaders", etc.).
            
            CRITICAL VISUAL RULES:
            - Find gameplay that is FULL SCREEN.
            - Do NOT select moments with black screens, heavy UI overlays, menus, or obstacles blocking the view.
            - STRICTLY EXCLUDE closing transition scenes, outro graphics, or "thanks for watching" end screens.
            - "vanilla_start" is the start of a clearly VANILLA (no shader) moment.
            - "shader_start" is the start of a clearly SHADERS-ON moment.
            
            VOICEOVER SCRIPT TASK:
            Write an engaging, energetic voiceover script that matches the flow of these pairs. 
            The script should excitedly introduce each shader by name as it appears. Ensure the pacing fits roughly 5-10 seconds per shader pair.
            
            DESCRIPTION TASK:
            Write an engaging YouTube description using the following template, replacing [SHADER_NAMES] with the actual names you found:
            "Looking for the best ultra-realistic shaders for Minecraft Pocket Edition (MCPE) and Minecraft Bedrock Edition that work smoothly on lightweight, low-end, and mid-range devices?\\nIn this video, we showcase [SHADER_NAMES] featuring stunning graphics, realistic lighting, beautiful skies, enhanced water reflections, volumetric fog, dynamic shadows, and an immersive next-generation visual experience—all without requiring a high-end phone or an RTX graphics card!\\n\\n✨ Key Features\\nPerformance: Lightweight, FPS-friendly, and optimized for low-end devices.\\nVisuals: Enhanced sky, realistic clouds, vibrant colors, and improved water visuals.\\nLighting: Better sunlight, realistic moonlight, and dynamic shadow effects.\\nAtmosphere: Smooth atmospheric effects and volumetric fog.\\nAccessibility: 100% FREE to download with No RTX Required.\\n\\n🔗 Download Links\\n👉 Get all the shaders featured in this video here: 👇\\nhttps://www.piglixmcmods.dev/\\n\\n💬 Join the Conversation!\\nWhich shader was your favorite? Comment the name below! 👇\\nWhat shader pack or mod should I review next? Let me know in the comments!\\nDon't forget to Like and Subscribe for more Minecraft Bedrock content! 👍\\n🔍 SEO & Keywords (Search Optimization)\\nBSL, Newb, SEUS, SLS, Complementary realistic minecraft shaders, mcpe shaders, render dragon shaders, low-end device shaders, no lag shaders, minecraft, minecraft shaders, realistic minecraft, minecraft mod, minecraft texture pack, minecraft java, minecraft bedrock, best minecraft shaders, gaming shorts, viral minecraft, shader pack tutorial.\\n\\n🏷️ Tags\\n#MinecraftPE #MinecraftShaders #MCPE #BedrockEdition #patchshaders #mcpeshaders #BSLShaders #NewbShaders #SEUSShaders #SLSShaders #ComplementaryShaders"
            
            Return ONLY a valid JSON object, no other text. Format:
            {{
              "description": "Your full description text here",
              "voiceover_script": "Your energetic voiceover script covering all the shaders",
              "pairs": [
                {{"shader_name": "...", "vanilla_start": 0.0, "shader_start": 0.0}}
              ]
            }}
            """'''
content = re.sub(old_prompt, new_prompt, content)

# 3. Update return logic in get_gemini_pairs
old_return = r'''            raw_pairs = raw_response.get\("pairs", \[\]\)
            pairs = _sanitize_pairs\(raw_pairs, num_pairs\)
            log\(f"  Gemini returned \{len\(pairs\)\} usable pair\(s\)"\)
            return pairs'''
new_return = r'''            raw_pairs = raw_response.get("pairs", [])
            pairs = _sanitize_pairs(raw_pairs, len(raw_pairs)) # keep however many it found
            log(f"  Gemini returned {len(pairs)} usable pair(s)")
            return {"pairs": pairs, "voiceover_script": raw_response.get("voiceover_script", "")}'''
content = re.sub(old_return, new_return, content)

# 4. Fallback return in get_gemini_pairs
old_fallback = r'''    log\("  Using fallback timestamps\."\)
    return \[\{"shader_name": f"Shader Pack \{i \+ 1\}", "vanilla_start": 10\.0 \+ i\*40, "shader_start": 30\.0 \+ i\*40\} for i in range\(num_pairs\)\]'''
new_fallback = r'''    log("  Using fallback timestamps.")
    pairs = [{"shader_name": f"Shader Pack {i + 1}", "vanilla_start": 10.0 + i*40, "shader_start": 30.0 + i*40} for i in range(3)]
    return {"pairs": pairs, "voiceover_script": ""}'''
content = re.sub(old_fallback, new_fallback, content)

# 5. Update build_reference_style_video
old_build = r'''    # Ask Gemini to find exactly 3 shader pairs with names
    pairs = get_gemini_pairs\(raw_path, 3\)

    # 3 pairs x \(before \+ after\) x 5\.0s = 30s, matching the requested ~30s short\.
    CLIP_DURATION = 5\.0  # BEFORE \+ AFTER per pair

    # ── Build voiceover script timed to the actual clip structure ────────────
    # Layout: \[BEFORE_1 5\.0s\]\[AFTER_1 5\.0s\]\[BEFORE_2 5\.0s\]\[AFTER_2 5\.0s\]\[BEFORE_3 5\.0s\]\[AFTER_3 5\.0s\]
    # Total = 30 seconds
    pair_lines = \[\]
    for i, p in enumerate\(pairs\):
        name = p\.get\("shader_name", f"this shader pack"\)
        if i == 0:
            pair_lines\.append\(
                f"First up, we have \{name\}\. "
                f"Watch how it transforms the world with incredible lighting and vibrant colors\."
            \)
        elif i == 1:
            pair_lines\.append\(
                f"Next, let's check out \{name\}\. "
                f"This one adds stunning water reflections and realistic shadows\. It's a game-changer\."
            \)
        else:
            pair_lines\.append\(
                f"And for our final shader, this is \{name\}\. "
                f"The god rays and atmospheric fog are just breathtaking\. You have to try this one\."
            \)

    # Each pair = 10s -> 3 pairs = 30s total\.
    # Voiceover lines are spread roughly across the matching pair's window\.
    VOICEOVER_SCRIPT = "  "\.join\(pair_lines\)
    log\(f"  Voiceover script: \{VOICEOVER_SCRIPT\[:80\]\}…"\)'''

new_build = r'''    # Ask Gemini to dynamically find all shaders and write the script
    gemini_data = get_gemini_pairs(raw_path)
    pairs = gemini_data.get("pairs", [])
    
    VOICEOVER_SCRIPT = gemini_data.get("voiceover_script", "")
    if not VOICEOVER_SCRIPT:
        # Fallback script if Gemini failed to generate one
        pair_lines = []
        for i, p in enumerate(pairs):
            name = p.get("shader_name", f"this shader pack")
            pair_lines.append(f"Here is {name}. Check out how it transforms the world with incredible visuals.")
        VOICEOVER_SCRIPT = " ".join(pair_lines)

    CLIP_DURATION = 5.0  # BEFORE + AFTER per pair
    log(f"  Voiceover script: {VOICEOVER_SCRIPT[:80]}…")'''
content = re.sub(old_build, new_build, content)

path.write_text(content)
print("Patched video_generator.py")
