
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.main import app


def fake_stream(*args, **kwargs):
    yield "event: pipeline_started\ndata: {}\n\n"
    yield "event: analysis_completed\ndata: {}\n\n"


with patch(
    "backend.streaming.run_streaming_analysis",
    fake_stream,
):
    client = TestClient(app)

    response = client.post(
        "/analyze/stream",
        json={"claim": "The Earth orbits the Sun."},
    )

    print("STATUS:", response.status_code)
    print(
        "SSE STARTED:",
        "event: pipeline_started" in response.text,
    )
    print(
        "SSE COMPLETED:",
        "event: analysis_completed" in response.text,
    )
