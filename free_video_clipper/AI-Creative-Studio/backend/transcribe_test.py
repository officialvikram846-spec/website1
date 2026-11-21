
from faster_whisper import WhisperModel

print("Loading AI model...")

model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

print("Transcribing video...")

segments, info = model.transcribe(
    "test_video.mp4",
    beam_size=5
)

print("\nDetected language:", info.language)
print("\nTRANSCRIPTION:\n")

for segment in segments:
    print(
        f"[{segment.start:.2f}s - {segment.end:.2f}s] "
        f"{segment.text}"
    )

print("\nTranscription completed!")
