
from fastapi import FastAPI, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import tempfile
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

# Keep videos out of the project folder. A file watcher (uvicorn --reload,
# Live Server) treats a new file there as a change and reloads the page.
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "ai-creative-studio-uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def transcribe_file(path):
    segments, info = model.transcribe(
        path,
        beam_size=5
    )

    transcription = []

    for segment in segments:
        transcription.append({
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip()
        })

    return info.language, transcription


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
        return JSONResponse(
            status_code=400,
            content={"error": "Please upload a video file"},
        )

    extension = os.path.splitext(file.filename or "")[1]
    filename = f"{uuid.uuid4()}{extension}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    print("Starting AI transcription...")

    try:
        language, transcription = await run_in_threadpool(transcribe_file, filepath)
    except Exception as exc:
        print("Transcription failed:", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "Transcription failed: " + str(exc)},
        )

    print("Transcription completed!")

    return {
        "message": "Video uploaded and transcribed successfully!",
        "filename": filename,
        "language": language,
        "transcription": transcription
    }
