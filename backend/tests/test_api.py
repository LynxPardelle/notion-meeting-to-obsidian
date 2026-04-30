from fastapi.testclient import TestClient

from notion_meeting_to_obsidian.api import create_app


def test_sync_preflight_allows_docker_frontend_origin():
    client = TestClient(create_app())

    response = client.options(
        "/sync?force=false",
        headers={
            "Origin": "http://127.0.0.1:47863",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:47863"
