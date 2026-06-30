import asyncio
import edge_tts

async def main():
    text = "Hello world, this is a test of captions."
    for voice in ["en-US-ChristopherNeural", "en-US-GuyNeural", "en-US-AriaNeural", "en-US-SteffanNeural", "en-US-BrianMultilingualNeural"]:
        communicate = edge_tts.Communicate(text, voice)
        word_boundaries = 0
        async for chunk in communicate.stream():
            if chunk["type"] == "WordBoundary":
                word_boundaries += 1
        print(f"{voice}: {word_boundaries} WordBoundary events")

asyncio.run(main())
