import re
from pathlib import Path

path = Path("scripts/video_generator.py")
content = path.read_text()

# 1. Update the prompt template to use the user's specific template
old_prompt = r'''            VOICEOVER SCRIPT TASK:
            Write an engaging, energetic voiceover script that matches the flow of these pairs. 
            The script should excitedly introduce each shader by name as it appears. Ensure the pacing fits roughly 5-10 seconds per shader pair.'''

new_prompt = r'''            VOICEOVER SCRIPT TASK:
            Write the voiceover script using EXACTLY the following template, but replacing the bracketed placeholders with the names of the shaders you found:
            "Stop playing Minecraft with boring default graphics! Here are 3 shaders that will completely change your world.
            First up, {Shader 1 Name}. The king of performance. It makes water look crystal clear and shadows crisp without killing your FPS.
            Number two: {Shader 2 Name}. It’s incredibly vibrant and adds beautiful waving animations to every single leaf and grass block.
            And finally, Number three: {Shader 3 Name}. If you have a beast of a PC, this is the most realistic lighting you will ever see in the game.
            Which one are you rocking? links of the shader is the discription"'''

content = content.replace(old_prompt, new_prompt)

# 2. Add fallback VTT generation in generate_tts
old_tts = r'''        if not out_path.exists() or out_path.stat().st_size < 1024:
            log(f"  ❌ TTS generation failed: output file is missing or empty ({out_path})")
            return None
        log(f"  TTS audio generated successfully.")
        return AudioFileClip(str(out_path))'''

new_tts = r'''        if not out_path.exists() or out_path.stat().st_size < 1024:
            log(f"  ❌ TTS generation failed: output file is missing or empty ({out_path})")
            return None
        log(f"  TTS audio generated successfully.")
        audio = AudioFileClip(str(out_path))
        
        # Fallback for missing WordBoundary events (common with some neural voices)
        if vtt_path and vtt_path.exists():
            vtt_content = vtt_path.read_text(encoding="utf-8").strip()
            if not vtt_content or vtt_content == "WEBVTT":
                log("  ⚠ No WordBoundary events found. Generating proportional fallback VTT...")
                words = text.split()
                duration = audio.duration
                word_dur = duration / max(len(words), 1)
                lines = ["WEBVTT\n\n"]
                for i, word in enumerate(words):
                    start = i * word_dur
                    end = (i + 1) * word_dur
                    def fmt_time(t):
                        h = int(t / 3600)
                        m = int((t % 3600) / 60)
                        s = t % 60
                        return f"{h:02d}:{m:02d}:{s:06.3f}"
                    lines.append(f"{fmt_time(start)} --> {fmt_time(end)}\n{word}\n\n")
                vtt_path.write_text("".join(lines), encoding="utf-8")
                
        return audio'''

content = content.replace(old_tts, new_tts)
path.write_text(content)
print("Patch applied successfully.")
