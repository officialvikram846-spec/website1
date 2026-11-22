import os
import sys
from unittest.mock import MagicMock

# Tests must not download or load the Whisper model.
sys.modules["faster_whisper"] = MagicMock()

import main
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "UPLOAD_DIR", str(tmp_path))

    segment = MagicMock(start=1.25, end=2.5, text=" hello world ")
    info = MagicMock(language="en")
    main.model.transcribe.reset_mock()
    main.model.transcribe.side_effect = None
    main.model.transcribe.return_value = ([segment], info)

    return TestClient(main.app)


def test_upload_directory_is_outside_the_project():
    project_dir = os.path.abspath(os.path.join(os.path.dirname(main.__file__), ".."))
    upload_dir = os.path.abspath(main.UPLOAD_DIR)

    assert os.path.isdir(upload_dir)
    assert not upload_dir.startswith(project_dir + os.sep)
    assert upload_dir != project_dir


def test_upload_transcribes_and_stores_the_video_outside_the_repo(client, tmp_path):
    response = client.post(
        "/upload",
        files={"file": ("clip.mp4", b"fake-video-bytes", "video/mp4")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "en"
    assert body["transcription"] == [
        {"start": 1.25, "end": 2.5, "text": "hello world"}
    ]

    saved = list(tmp_path.iterdir())
    assert len(saved) == 1
    assert saved[0].suffix == ".mp4"
    assert saved[0].read_bytes() == b"fake-video-bytes"
    assert not str(saved[0]).startswith(
        os.path.abspath(os.path.join(os.path.dirname(main.__file__), "..")) + os.sep
    )

    main.model.transcribe.assert_called_once()
    called_path = main.model.transcribe.call_args.args[0]
    assert called_path == str(saved[0])


def test_non_video_is_rejected(client, tmp_path):
    response = client.post(
        "/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["error"] == "Please upload a video file"
    assert list(tmp_path.iterdir()) == []
    main.model.transcribe.assert_not_called()


def test_transcription_failure_returns_an_error(client, tmp_path):
    main.model.transcribe.side_effect = RuntimeError("decoder missing")

    response = client.post(
        "/upload",
        files={"file": ("clip.mp4", b"fake-video-bytes", "video/mp4")},
    )

    assert response.status_code == 500
    assert response.json()["error"] == "Transcription failed: decoder missing"
    assert len(list(tmp_path.iterdir())) == 1
