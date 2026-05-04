from fastapi.testclient import TestClient

from notion_meeting_to_obsidian.api import create_app


def configured_client(tmp_path, monkeypatch):
    vault = tmp_path / "vault"
    monkeypatch.setenv("NOTION_TOKEN", "test-token")
    monkeypatch.setenv("NOTION_SOURCE_ID", "test-source")
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault))
    return TestClient(create_app()), vault


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


def test_read_note_returns_meeting_card(tmp_path, monkeypatch):
    client, vault = configured_client(tmp_path, monkeypatch)
    note_path = vault / "Meetings" / "Demo.md"
    note_path.parent.mkdir(parents=True)
    note_path.write_text(
        "# Demo\n\n## Resumen\n\nHola.\n\n## Tareas\n\n- [x] Lista\n\n## Notas\n\nDetalle.\n",
        encoding="utf-8",
    )

    response = client.get("/notes/read", params={"path": str(note_path)})

    assert response.status_code == 200
    payload = response.json()
    assert payload["card"]["summary"] == "Hola."
    assert payload["card"]["tasks"] == [{"text": "Lista", "checked": True}]
    assert payload["card"]["notes"] == "Detalle."


def test_save_note_card_updates_only_structured_sections(tmp_path, monkeypatch):
    client, vault = configured_client(tmp_path, monkeypatch)
    note_path = vault / "Meetings" / "Demo.md"
    note_path.parent.mkdir(parents=True)
    note_path.write_text("# Demo\n\n## Extra\n\nConservar.\n\n## Resumen\n\nViejo.\n", encoding="utf-8")

    response = client.post(
        "/notes/card/save",
        json={
            "path": str(note_path),
            "card": {
                "summary": "Nuevo.",
                "tasks": [{"text": "Hacer prueba", "checked": False}],
                "notes": "Notas nuevas.",
            },
        },
    )

    assert response.status_code == 200
    saved = note_path.read_text(encoding="utf-8")
    assert "## Extra\n\nConservar." in saved
    assert "## Resumen\n\nNuevo." in saved
    assert "- [ ] Hacer prueba" in saved
    assert "## Notas\n\nNotas nuevas." in saved
