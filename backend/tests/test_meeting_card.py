from notion_meeting_to_obsidian.meeting_card import (
    MeetingCard,
    MeetingTask,
    parse_meeting_card,
    preserve_existing_card_sections,
    update_meeting_card_sections,
)


def test_parse_meeting_card_extracts_spanish_sections():
    markdown = """---
title: "Demo"
---

# Demo

Intro text.

## Resumen

Resumen actual.

## Tareas

- [ ] Pendiente
- [x] Terminada

## Notas

Notas libres.
"""

    card = parse_meeting_card(markdown)

    assert card.summary == "Resumen actual."
    assert card.tasks == [
        MeetingTask(text="Pendiente", checked=False),
        MeetingTask(text="Terminada", checked=True),
    ]
    assert card.notes == "Notas libres."


def test_parse_meeting_card_uses_plain_body_as_notes_when_sections_are_missing():
    card = parse_meeting_card("# Demo\n\nContenido sin secciones.\n")

    assert card.summary == ""
    assert card.tasks == []
    assert card.notes == "Contenido sin secciones."


def test_parse_meeting_card_uses_unsectioned_notion_body_as_notes():
    markdown = """---
title: "Demo"
---

# Demo

Texto generado por Notion sin encabezados estructurados.

Otra linea de contexto.
"""

    card = parse_meeting_card(markdown)

    assert card.summary == ""
    assert card.tasks == []
    assert card.notes == "Texto generado por Notion sin encabezados estructurados.\n\nOtra linea de contexto."


def test_parse_meeting_card_prefers_explicit_notes_section_over_unsectioned_body():
    markdown = """# Demo

Intro que no debe reemplazar la seccion explicita.

## Notas

Notas estructuradas.
"""

    card = parse_meeting_card(markdown)

    assert card.notes == "Notas estructuradas."


def test_update_meeting_card_sections_preserves_frontmatter_and_unknown_sections():
    markdown = """---
title: "Demo"
---

# Demo

## Contexto

No tocar.

## Resumen

Viejo.
"""
    card = MeetingCard(
        summary="Nuevo resumen.",
        tasks=[MeetingTask(text="Nueva tarea", checked=False)],
        notes="Nueva nota.",
    )

    updated = update_meeting_card_sections(markdown, card)

    assert 'title: "Demo"' in updated
    assert "## Contexto\n\nNo tocar." in updated
    assert "## Resumen\n\nNuevo resumen." in updated
    assert "## Tareas\n\n- [ ] Nueva tarea" in updated
    assert "## Notas\n\nNueva nota." in updated
    assert "Viejo." not in updated


def test_preserve_existing_card_sections_keeps_local_summary_tasks_and_notes():
    incoming = """---
title: "Demo"
---

# Demo

Nuevo cuerpo desde Notion.
"""
    existing = """---
title: "Demo"
---

# Demo

Cuerpo anterior desde Notion.

## Resumen

Resumen local.

## Tareas

- [x] Tarea local

## Notas

Notas locales.
"""

    merged = preserve_existing_card_sections(incoming, existing)

    assert "Nuevo cuerpo desde Notion." in merged
    assert "Cuerpo anterior desde Notion." not in merged
    assert "## Resumen\n\nResumen local." in merged
    assert "## Tareas\n\n- [x] Tarea local" in merged
    assert "## Notas\n\nNotas locales." in merged


def test_preserve_existing_card_sections_ignores_unsectioned_existing_body():
    incoming = "# Demo\n\nNuevo cuerpo desde Notion.\n"
    existing = "# Demo\n\nCuerpo anterior sin secciones.\n"

    merged = preserve_existing_card_sections(incoming, existing)

    assert "Nuevo cuerpo desde Notion." in merged
    assert "Cuerpo anterior sin secciones." not in merged
