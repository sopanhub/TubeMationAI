# Video Automation Studio (TubeMationAI)

A powerful, AI-driven automation suite that creates viral YouTube Shorts from long-form content automatically. 

## Features
- **Minecraft Shaders Pipeline**: Analyzes long gameplay videos using Gemini to find before/after shader comparisons, cuts them perfectly, adds voiceover using Edge-TTS, and burns in word-level captions.
- **MrBeast & Streamers Pipeline**: Advanced face tracking, split-screen gameplay integration (e.g., GTA V parkour below the facecam), animated Impact captions, and dynamic audio masking for viral streamer clips.
- **Web Interface**: Clean, premium Next.js dashboard to manage generations, view history, and preview clips.
- **Settings UI**: Configure all API keys (Gemini, Groq, YouTube) securely through the web interface without manually modifying the `.env` file.
- **YouTube Auto-Upload**: Push generated Shorts directly to YouTube right from the dashboard history.

---

## Prerequisites
Before you start, ensure you have the following installed on your system:
- **Node.js** (v18 or higher)
- **Python** (v3.10 or higher)
- **FFmpeg** (Must be installed and accessible on your system's `PATH`)

---

## Step-by-Step Setup Guide

### 1. Clone the repository
```bash
git clone https://github.com/sopanhub/TubeMationAI.git
cd TubeMationAI
```

### 2. Install Node.js Dependencies
Install the required packages for the Next.js frontend:
```bash
npm install
```

### 3. Install Python Dependencies
Install the required packages for the AI video processing scripts:
```bash
pip install -r requirements.txt
```

### 4. Install FFmpeg
FFmpeg is required by `moviepy` to process and render videos.
- **Mac**: `brew install ffmpeg`
- **Windows**: Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) or use `winget install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

Verify it is installed by running `ffmpeg -version` in your terminal.

### 5. Setup Environment Variables
You can configure your environment variables either manually or through the Web UI.

**Manual Setup:**
```bash
cp .env.example .env
```
Open the `.env` file and fill in your keys.

**UI Setup:**
Once the app is running (see Step 7), click the **⚙️ Settings** button on the homepage to enter your keys safely. 
- **Gemini API Key** (Required for video analysis)
- **Groq API Key** (Optional - for Magic Edit voice/captioning)
- **YouTube OAuth Credentials** (Optional - to upload videos directly)

### 6. Generate YouTube OAuth Tokens (Optional)
If you want to use the auto-upload feature to push shorts to YouTube automatically, you must generate a refresh token.
1. Create OAuth 2.0 Client IDs in the [Google Cloud Console](https://console.cloud.google.com/). Ensure the "YouTube Data API v3" is enabled.
2. Run the included helper script:
```bash
python3 scripts/generate_youtube_token.py
```
3. Follow the on-screen instructions to log into your Google Account.
4. Copy the generated Refresh Token and paste it into the Web Settings UI (or your `.env` file).

### 7. Run the Application
Start the development server. This command will launch both the Next.js frontend and the Python FastAPI backend.
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## How to Use the App

### Minecraft Shaders Pipeline
1. Go to the **Minecraft Shaders** page.
2. Paste a YouTube URL of a long-form Minecraft shader showcase video.
3. Click **Generate**.
4. Gemini will watch the video, detect the "before" and "after" transition moments, and automatically slice the best clips.
5. The pipeline generates an AI voiceover, overlays captions, and renders a 9:16 vertical short.

### MrBeast & Streamers Pipeline
1. Go to the **MrBeast & Streamers** page.
2. Paste a YouTube URL of a streamer or talking-head video.
3. Paste a "Gameplay URL" (optional) for the split-screen bottom half (e.g., GTA V parkour).
4. Click **Generate**.
5. The pipeline uses AI face-tracking to keep the speaker centered, adds engaging animated captions, and mixes the audio.

### Managing Videos
- View your previously generated clips by clicking the **History** button in either pipeline.
- From the History modal, you can **Download** the video locally or click **Upload to YT** to push it directly to your channel.

---

## Troubleshooting
- **Python script fails / command not found**: Ensure you are using `python3` and that your virtual environment (if you use one) is activated.
- **Missing `ffprobe` or `ffmpeg`**: Ensure FFmpeg is installed and added to your system's PATH variables. Restart your terminal after installing.
- **Missing API Keys error**: Ensure you have configured your Gemini API key in the web settings.
