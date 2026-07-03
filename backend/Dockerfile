FROM python:3.10-slim

# Install system dependencies (ffmpeg, build tools for mediapipe/psutil, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    build-essential \
    python3-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set up a working directory
WORKDIR /app

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories
RUN mkdir -p /app/scripts /app/public/output

# Copy scripts and backend files
COPY scripts/ /app/scripts/
COPY backend/app.py /app/app.py

# Expose port 7860 (Hugging Face standard)
EXPOSE 7860

# Run the FastAPI server
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
