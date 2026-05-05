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


def test_sync_preflight_allows_configured_frontend_port(monkeypatch):
    monkeypatch.setenv("FRONTEND_PORT", "49123")
    client = TestClient(create_app())

    response = client.options(
        "/sync?force=false",
        headers={
            "Origin": "http://127.0.0.1:49123",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:49123"


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


def test_read_note_uses_notion_summary_metadata_when_markdown_summary_is_empty(tmp_path, monkeypatch):
    client, vault = configured_client(tmp_path, monkeypatch)
    note_path = vault / "Meetings" / "Demo.md"
    note_path.parent.mkdir(parents=True)
    note_path.write_text("# Demo\n\nContenido de la nota.\n", encoding="utf-8")
    state_path = vault / ".notion-meeting-sync" / "state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        '{"pages":{"page-1":{'
        '"file_path":"' + note_path.as_posix() + '",'
        '"metadata":[{"name":"Summary","type":"rich_text","value":"Resumen desde Notion"}]'
        "}}}",
        encoding="utf-8",
    )

    response = client.get("/notes/read", params={"path": str(note_path)})

    assert response.status_code == 200
    assert response.json()["card"]["summary"] == "Resumen desde Notion"


def test_read_note_uses_source_mapping_for_empty_meeting_card_fields(tmp_path, monkeypatch):
    client, vault = configured_client(tmp_path, monkeypatch)
    note_path = vault / "Meetings" / "Demo.md"
    note_path.parent.mkdir(parents=True)
    note_path.write_text("# Demo\n", encoding="utf-8")
    state_path = vault / ".notion-meeting-sync" / "state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        '{"active_page_ids":["page-1"],'
        '"data_sources":{"source-a":{"id":"source-a","name":"Tabla principal"}},'
        '"pages":{"page-1":{'
        '"file_path":"' + note_path.as_posix() + '",'
        '"source_id":"source-a",'
        '"metadata":['
        '{"name":"Summary","type":"rich_text","value":"Resumen desde propiedad"},'
        '{"name":"Texto","type":"rich_text","value":"Notas largas desde la tabla"},'
        '{"name":"Tareas","type":"rich_text","value":"- [x] Revisar API\\n- Documentar flujo"}'
        "]"
        "}}}",
        encoding="utf-8",
    )

    response = client.get("/notes/read", params={"path": str(note_path)})

    assert response.status_code == 200
    assert response.json()["card"] == {
        "summary": "Resumen desde propiedad",
        "tasks": [
            {"text": "Revisar API", "checked": True},
            {"text": "Documentar flujo", "checked": False},
        ],
        "notes": "Notas largas desde la tabla",
    }


def test_list_notes_uses_synced_parent_and_source_metadata(tmp_path, monkeypatch):
    client, vault = configured_client(tmp_path, monkeypatch)
    meetings = vault / "Meetings"
    parent_path = meetings / "Reunion de lunes" / "Reunion de lunes.md"
    child_path = meetings / "Reunion de lunes" / "Notas internas de prueba.md"
    child_path.parent.mkdir(parents=True)
    parent_path.write_text("# Reunion de lunes\n", encoding="utf-8")
    child_path.write_text("# Notas internas de prueba\n", encoding="utf-8")
    state_path = vault / ".notion-meeting-sync" / "state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        '{"active_page_ids":["parent","child"],"pages":{'
        '"parent":{"file_path":"' + parent_path.as_posix() + '","title":"Reunion de lunes","depth":0,'
        '"source_id":"source-a","source_label":"Tabla principal"},'
        '"child":{"file_path":"' + child_path.as_posix() + '","title":"Notas internas de prueba",'
        '"parent_id":"parent","depth":1,"source_id":"source-a","source_label":"Tabla principal"}'
        "}}",
        encoding="utf-8",
    )

    response = client.get("/notes")

    assert response.status_code == 200
    child = next(item for item in response.json() if item["name"] == "Notas internas de prueba")
    assert child["parent"] == "Reunion de lunes"
    assert child["parent_id"] == "parent"
    assert child["depth"] == 1
    assert child["source_label"] == "Tabla principal"


def test_list_note_sources_includes_empty_data_sources(tmp_path, monkeypatch):
    client, vault = configured_client(tmp_path, monkeypatch)
    note_path = vault / "Meetings" / "Demo.md"
    note_path.parent.mkdir(parents=True)
    note_path.write_text("# Demo\n", encoding="utf-8")
    state_path = vault / ".notion-meeting-sync" / "state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        '{"active_page_ids":["page-1"],'
        '"data_sources":{'
        '"source-a":{"id":"source-a","name":"Tabla con notas"},'
        '"source-b":{"id":"source-b","name":"Tabla vacia"}'
        '},'
        '"pages":{'
        '"page-1":{"file_path":"' + note_path.as_posix() + '","title":"Demo",'
        '"source_id":"source-a","source_label":"Tabla con notas"}'
        "}}",
        encoding="utf-8",
    )

    response = client.get("/note-sources")

    assert response.status_code == 200
    assert response.json() == [
        {"id": "source-a", "name": "Tabla con notas", "note_count": 1},
        {"id": "source-b", "name": "Tabla vacia", "note_count": 0},
    ]


def test_list_note_source_schema_groups_properties_by_table(tmp_path, monkeypatch):
    client, vault = configured_client(tmp_path, monkeypatch)
    state_path = vault / ".notion-meeting-sync" / "state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        '{"active_page_ids":["page-1","page-2"],'
        '"data_sources":{'
        '"source-a":{"id":"source-a","name":"Tabla principal"},'
        '"source-b":{"id":"source-b","name":"Tabla vacia"}'
        '},'
        '"pages":{'
        '"page-1":{"source_id":"source-a","source_label":"Tabla principal",'
        '"metadata":['
        '{"name":"Summary","type":"rich_text","value":"Resumen"},'
        '{"name":"Texto","type":"people","value":"Oswaldo"},'
        '{"name":"Estado","type":"status","value":"En curso"}'
        ']},'
        '"page-2":{"source_id":"source-a","source_label":"Tabla principal",'
        '"metadata":['
        '{"name":"Summary","type":"rich_text","value":"Otro resumen"},'
        '{"name":"Fecha","type":"date","value":"2026-05-05"}'
        ']}'
        "}}",
        encoding="utf-8",
    )

    response = client.get("/note-sources/schema")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": "source-a",
            "name": "Tabla principal",
            "note_count": 2,
            "properties": [
                {"name": "Estado", "type": "status", "usage_count": 1, "sample": "En curso"},
                {"name": "Fecha", "type": "date", "usage_count": 1, "sample": "2026-05-05"},
                {"name": "Summary", "type": "rich_text", "usage_count": 2, "sample": "Resumen"},
                {"name": "Texto", "type": "people", "usage_count": 1, "sample": "Oswaldo"},
            ],
            "mapping": {
                "date": "Fecha",
                "notes": None,
                "people": "Texto",
                "status": "Estado",
                "summary": "Summary",
                "tasks": None,
            },
        },
        {
            "id": "source-b",
            "name": "Tabla vacia",
            "note_count": 0,
            "properties": [],
            "mapping": {
                "date": None,
                "notes": None,
                "people": None,
                "status": None,
                "summary": None,
                "tasks": None,
            },
        },
    ]


def test_read_note_keeps_local_markdown_summary_over_notion_metadata(tmp_path, monkeypatch):
    client, vault = configured_client(tmp_path, monkeypatch)
    note_path = vault / "Meetings" / "Demo.md"
    note_path.parent.mkdir(parents=True)
    note_path.write_text("# Demo\n\n## Resumen\n\nResumen local.\n", encoding="utf-8")
    state_path = vault / ".notion-meeting-sync" / "state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        '{"pages":{"page-1":{'
        '"file_path":"' + note_path.as_posix() + '",'
        '"metadata":[{"name":"Summary","type":"rich_text","value":"Resumen desde Notion"}]'
        "}}}",
        encoding="utf-8",
    )

    response = client.get("/notes/read", params={"path": str(note_path)})

    assert response.status_code == 200
    assert response.json()["card"]["summary"] == "Resumen local."


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
