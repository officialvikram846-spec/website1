
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
from faster_whisper import WhisperModel

print("Loading AI transcription model...")

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

print("AI transcription model loaded successfully!")

app = FastAPI(
    title="AI Creative Studio",
    description="Your personal AI content creation platform",
    version="1.0.0"
)

# Allow our frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def home():
    return {
        "message": "Welcome to AI Creative Studio!",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "application": "AI Creative Studio"
    }


@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):

    if not file.content_type or not file.content_type.startswith("video/"):
        return {"error": "Please upload a video file"}

    extension = os.path.splitext(file.filename or "")[1]
    filename = f"{uuid.uuid4()}{extension}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    print("Starting AI transcription...")

    segments, info = model.transcribe(
        filepath,
        beam_size=5
    )

    transcription = []

    for segment in segments:
        transcription.append({
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip()
        })

    print("Transcription completed!")

    return {
        "message": "Video uploaded and transcribed successfully!",
        "filename": filename,
        "language": info.language,
        "transcription": transcription
    }
