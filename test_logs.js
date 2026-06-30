const logs = [
  "  Clip 1 saved: mrbeast_clip_1.mp4",
  "Clip 2 saved: mrbeast_clip_2.mp4",
  "  [9/9] Final encode…"
];

for (const msg of logs) {
  const clipMatch = msg.match(/Clip (\d+) saved: (mrbeast_clip_\d+\.mp4)/);
  if (clipMatch) {
    console.log(`Matched: ${clipMatch[1]} -> ${clipMatch[2]}`);
  }
}
