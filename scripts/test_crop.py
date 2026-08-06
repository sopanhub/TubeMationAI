import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from mrbeast_generator import track_and_crop
track_and_crop(Path("public/output/mrbeast_work/main_raw_c17a6eec.mp4"), 30.0, 45.0, Path("test_crop.mp4"), 1080, 1114)
print("Done")
