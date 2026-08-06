import sys
from pathlib import Path
sys.path.insert(0, str(Path("scripts").resolve()))
from gemini_analyzer import get_all_clips
clips = get_all_clips(Path("public/output/mrbeast_work/main_raw_c17a6eec.mp4"), num_clips=1, avoid_timestamps="10:00-11:00")
print(clips)
