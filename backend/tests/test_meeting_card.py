from notion_meeting_to_obsidian.meeting_card import (
    MeetingCard,
    MeetingTask,
    parse_meeting_card,
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


def test_parse_meeting_card_returns_empty_values_for_missing_sections():
    card = parse_meeting_card("# Demo\n\nContenido sin secciones.\n")

    assert card.summary == ""
    assert card.tasks == []
    assert card.notes == ""


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
