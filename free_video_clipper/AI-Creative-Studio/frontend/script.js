const videoInput = document.getElementById("videoInput");
const uploadButton = document.getElementById("uploadButton");
const fileName = document.getElementById("fileName");
const uploadStatus = document.getElementById("uploadStatus");
const dropZone = document.getElementById("dropZone");
const transcriptionResult = document.getElementById("transcriptionResult");
const detectedLanguage = document.getElementById("detectedLanguage");
const transcriptionText = document.getElementById("transcriptionText");
const uploadProgress = document.getElementById("uploadProgress");
const uploadProgressBar = document.getElementById("uploadProgressBar");
const uploadPercentage = document.getElementById("uploadPercentage");
const uploadProgressLabel = document.getElementById("uploadProgressLabel");

uploadButton.addEventListener("click", () => {
    videoInput.click();
});

videoInput.addEventListener("change", (event) => {
    console.log("FILE INPUT CHANGE EVENT FIRED");

    const file = event.target.files[0];

    if (file) {
        console.log("Selected video:", file.name);
        uploadVideo(file);
    }
});

dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropZone.style.background = "#201a32";
});

dropZone.addEventListener("dragleave", () => {
    dropZone.style.background = "";
});

dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropZone.style.background = "";

    const file = event.dataTransfer.files[0];

    if (file) {
        uploadVideo(file);
    }
});

function uploadVideo(file) {
    console.log("UPLOAD FUNCTION STARTED");

    if (!file.type.startsWith("video/")) {
        uploadStatus.textContent = "Please select a valid video.";
        return;
    }

    if (file.size > 100 * 1024 * 1024) {
        uploadStatus.textContent = "File exceeds the 100 MB limit.";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    fileName.textContent = "Selected: " + file.name;
    uploadStatus.textContent = "Preparing upload...";

    uploadButton.disabled = true;

    uploadProgress.style.display = "block";
    uploadProgressBar.style.width = "0%";
    uploadPercentage.textContent = "0%";
    uploadProgressLabel.textContent = "⬆ Uploading video";

    const xhr = new XMLHttpRequest();

    xhr.open("POST", "http://127.0.0.1:8000/upload");

    // Track actual upload progress
    xhr.upload.addEventListener("progress", (event) => {
        if (event.lengthComputable) {
            const percentage = Math.round(
                (event.loaded / event.total) * 100
            );

            uploadProgressBar.style.width = percentage + "%";
            uploadPercentage.textContent = percentage + "%";

            console.log("Upload progress:", percentage + "%");
        }
    });

    // Upload completed; backend can now transcribe
    xhr.upload.addEventListener("load", () => {
        uploadProgressBar.style.width = "100%";
        uploadPercentage.textContent = "100%";
        uploadProgressLabel.textContent = "✓ Video uploaded";

        uploadStatus.textContent = "Video uploaded! AI transcription starting...";
    });

    xhr.addEventListener("load", () => {
        try {
            const result = JSON.parse(xhr.responseText);

            if (xhr.status < 200 || xhr.status >= 300 || result.error) {
                throw new Error(result.error || "Upload failed");
            }

            uploadProgressLabel.textContent = "✓ Video uploaded";
            uploadPercentage.textContent = "100%";

            uploadStatus.textContent =
                "✓ Video uploaded successfully! Transcription completed.";

            uploadStatus.style.color = "#65e6a0";

            detectedLanguage.textContent =
                "Detected language: " + result.language;

            transcriptionText.innerHTML = "";

            result.transcription.forEach((segment) => {
                const paragraph = document.createElement("p");

                paragraph.textContent =
                    `[${segment.start}s - ${segment.end}s] ${segment.text}`;

                transcriptionText.appendChild(paragraph);
            });

            transcriptionResult.style.display = "block";

        } catch (error) {
            uploadStatus.textContent = "Error: " + error.message;
            uploadStatus.style.color = "#ff8585";

            console.error("UPLOAD ERROR:", error);

        } finally {
            uploadButton.disabled = false;
        }
    });

    xhr.addEventListener("error", () => {
        uploadStatus.textContent = "Network error. Please try again.";
        uploadStatus.style.color = "#ff8585";
        uploadButton.disabled = false;
    });

    xhr.send(formData);
}
