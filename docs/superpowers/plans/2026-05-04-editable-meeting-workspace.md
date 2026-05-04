# Editable Meeting Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a card-first meeting workspace where users can edit `Resumen`, `Tareas`, and `Notas`, while keeping the full Markdown editor available as an advanced mode.

**Architecture:** Add a backend Markdown section parser/writer that treats Obsidian `.md` files as the editable source of truth. Expose structured card read/save data through FastAPI, then update the Angular app to default to a meeting card and switch into full Markdown editing only when requested.

**Tech Stack:** Python, FastAPI, pytest, Angular standalone component, TypeScript signals, Docker Compose.

---

## File Structure

- Create: `backend/src/notion_meeting_to_obsidian/meeting_card.py`
  - Owns parsing and updating Markdown sections for `Resumen`, `Tareas`, and `Notas`.
- Create: `backend/tests/test_meeting_card.py`
  - Unit tests for parsing, updating, missing sections, frontmatter preservation, and checkbox tasks.
- Modify: `backend/src/notion_meeting_to_obsidian/api.py`
  - Adds structured response models and `/notes/card/save`.
  - Extends `/notes/read` to return parsed meeting card data.
- Modify: `backend/tests/test_api.py`
  - Adds API tests for reading parsed card data and saving structured card changes.
- Modify: `frontend/src/app/api.service.ts`
  - Adds TypeScript interfaces and `saveMeetingCard`.
- Modify: `frontend/src/app/app.component.ts`
  - Adds card mode, Markdown mode, dirty-state tracking, editable fields, and task helpers.
- Modify: `frontend/src/app/app.component.html`
  - Replaces default editor-first layout with card-first layout and secondary Markdown editor mode.
- Modify: `frontend/src/styles.css`
  - Adds card workspace, editable sections, task rows, metadata/details layout, and mobile behavior.

---

### Task 1: Backend Markdown Card Parser

**Files:**
- Create: `backend/src/notion_meeting_to_obsidian/meeting_card.py`
- Test: `backend/tests/test_meeting_card.py`

- [ ] **Step 1: Write failing parser tests**

Create `backend/tests/test_meeting_card.py`:

```python
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
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m pytest backend/tests/test_meeting_card.py -v
```

Expected: fail because `notion_meeting_to_obsidian.meeting_card` does not exist.

- [ ] **Step 3: Implement parser/writer**

Create `backend/src/notion_meeting_to_obsidian/meeting_card.py`:

```python
from __future__ import annotations

from dataclasses import dataclass
import re


SECTION_NAMES = {
    "summary": "Resumen",
    "tasks": "Tareas",
    "notes": "Notas",
}

SECTION_ORDER = ["summary", "tasks", "notes"]
HEADING_RE = re.compile(r"(?m)^##\s+(.+?)\s*$")
TASK_RE = re.compile(r"^-\s+\[( |x|X)\]\s+(.*)$")


@dataclass(frozen=True)
class MeetingTask:
    text: str
    checked: bool = False


@dataclass(frozen=True)
class MeetingCard:
    summary: str = ""
    tasks: list[MeetingTask] | None = None
    notes: str = ""

    def normalized_tasks(self) -> list[MeetingTask]:
        return self.tasks or []


def parse_meeting_card(markdown: str) -> MeetingCard:
    sections = _section_map(markdown)
    return MeetingCard(
        summary=sections.get("Resumen", "").strip(),
        tasks=_parse_tasks(sections.get("Tareas", "")),
        notes=sections.get("Notas", "").strip(),
    )


def update_meeting_card_sections(markdown: str, card: MeetingCard) -> str:
    result = markdown.rstrip()
    replacements = {
        "Resumen": card.summary.strip(),
        "Tareas": _format_tasks(card.normalized_tasks()),
        "Notas": card.notes.strip(),
    }

    for heading, content in replacements.items():
        result = _replace_or_append_section(result, heading, content)

    return result.rstrip() + "\n"


def _section_map(markdown: str) -> dict[str, str]:
    matches = list(HEADING_RE.finditer(markdown))
    sections: dict[str, str] = {}
    for index, match in enumerate(matches):
        heading = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        sections[heading] = markdown[start:end].strip()
    return sections


def _parse_tasks(raw: str) -> list[MeetingTask]:
    tasks: list[MeetingTask] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = TASK_RE.match(stripped)
        if match:
            tasks.append(MeetingTask(text=match.group(2).strip(), checked=match.group(1).lower() == "x"))
        elif stripped.startswith("- "):
            tasks.append(MeetingTask(text=stripped[2:].strip(), checked=False))
        else:
            tasks.append(MeetingTask(text=stripped, checked=False))
    return tasks


def _format_tasks(tasks: list[MeetingTask]) -> str:
    return "\n".join(f"- [{'x' if task.checked else ' '}] {task.text.strip()}" for task in tasks if task.text.strip())


def _replace_or_append_section(markdown: str, heading: str, content: str) -> str:
    matches = list(HEADING_RE.finditer(markdown))
    for index, match in enumerate(matches):
        if match.group(1).strip() != heading:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(markdown)
        return markdown[:start].rstrip() + "\n\n" + content.rstrip() + "\n\n" + markdown[end:].lstrip()

    return markdown.rstrip() + f"\n\n## {heading}\n\n{content.rstrip()}\n"
```

- [ ] **Step 4: Run parser tests**

Run:

```powershell
python -m pytest backend/tests/test_meeting_card.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit**

```powershell
git add backend/src/notion_meeting_to_obsidian/meeting_card.py backend/tests/test_meeting_card.py
git commit -m "feat: parse editable meeting card sections"
```

---

### Task 2: Backend Structured Card API

**Files:**
- Modify: `backend/src/notion_meeting_to_obsidian/api.py`
- Test: `backend/tests/test_api.py`

- [ ] **Step 1: Add failing API tests**

Append to `backend/tests/test_api.py`:

```python
def test_read_note_returns_meeting_card(client, tmp_path, monkeypatch):
    note_path = tmp_path / "Meetings" / "Demo.md"
    note_path.parent.mkdir()
    note_path.write_text("# Demo\n\n## Resumen\n\nHola.\n\n## Tareas\n\n- [x] Lista\n\n## Notas\n\nDetalle.\n", encoding="utf-8")

    response = client.get("/notes/read", params={"path": str(note_path)})

    assert response.status_code == 200
    payload = response.json()
    assert payload["card"]["summary"] == "Hola."
    assert payload["card"]["tasks"] == [{"text": "Lista", "checked": True}]
    assert payload["card"]["notes"] == "Detalle."


def test_save_note_card_updates_only_structured_sections(client, tmp_path, monkeypatch):
    note_path = tmp_path / "Meetings" / "Demo.md"
    note_path.parent.mkdir()
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
```

- [ ] **Step 2: Run API tests and verify failure**

Run:

```powershell
python -m pytest backend/tests/test_api.py -v
```

Expected: fail because `/notes/read` does not include `card` and `/notes/card/save` does not exist.

- [ ] **Step 3: Implement API models and endpoint**

Modify `backend/src/notion_meeting_to_obsidian/api.py`:

```python
from .meeting_card import MeetingCard, MeetingTask, parse_meeting_card, update_meeting_card_sections
```

Add models:

```python
class MeetingTaskPayload(BaseModel):
    text: str
    checked: bool = False


class MeetingCardPayload(BaseModel):
    summary: str = ""
    tasks: list[MeetingTaskPayload] = []
    notes: str = ""


class SaveMeetingCardRequest(BaseModel):
    path: str
    card: MeetingCardPayload
```

Update `/notes/read` return body:

```python
markdown = note_path.read_text(encoding="utf-8")
card = parse_meeting_card(markdown)
return {
    "path": str(note_path),
    "markdown": markdown,
    "card": {
        "summary": card.summary,
        "tasks": [task.__dict__ for task in card.normalized_tasks()],
        "notes": card.notes,
    },
}
```

Add endpoint:

```python
@app.post("/notes/card/save")
def save_note_card(payload: SaveMeetingCardRequest) -> dict[str, str]:
    config = load_config()
    note_path = safe_note_path(config, payload.path)
    if not note_path.exists():
        raise HTTPException(status_code=404, detail="Note not found.")
    markdown = note_path.read_text(encoding="utf-8")
    card = MeetingCard(
        summary=payload.card.summary,
        tasks=[MeetingTask(text=task.text, checked=task.checked) for task in payload.card.tasks],
        notes=payload.card.notes,
    )
    note_path.write_text(update_meeting_card_sections(markdown, card), encoding="utf-8", newline="\n")
    return {"path": str(note_path), "status": "saved"}
```

- [ ] **Step 4: Run backend tests**

Run:

```powershell
python -m pytest backend/tests/test_meeting_card.py backend/tests/test_api.py -v
```

Expected: pass.

- [ ] **Step 5: Commit**

```powershell
git add backend/src/notion_meeting_to_obsidian/api.py backend/tests/test_api.py
git commit -m "feat: expose editable meeting card api"
```

---

### Task 3: Angular API Types and State

**Files:**
- Modify: `frontend/src/app/api.service.ts`
- Modify: `frontend/src/app/app.component.ts`

- [ ] **Step 1: Add TypeScript API types**

Modify `frontend/src/app/api.service.ts`:

```typescript
export interface MeetingTask {
  text: string;
  checked: boolean;
}

export interface MeetingCard {
  summary: string;
  tasks: MeetingTask[];
  notes: string;
}

export interface ReadNoteResponse {
  path: string;
  markdown: string;
  card: MeetingCard;
}
```

Add:

```typescript
saveMeetingCard(path: string, card: MeetingCard): Observable<{ path: string; status: string }> {
  return this.http.post<{ path: string; status: string }>(`${this.baseUrl}/notes/card/save`, {
    path,
    card
  });
}
```

- [ ] **Step 2: Add component state**

Modify import:

```typescript
import { ApiService, MeetingCard, MeetingTask, NoteSummary } from './api.service';
```

Add state:

```typescript
readonly viewMode = signal<'card' | 'markdown'>('card');
readonly card = signal<MeetingCard>({ summary: '', tasks: [], notes: '' });
readonly savedCard = signal<MeetingCard>({ summary: '', tasks: [], notes: '' });
readonly savedMarkdown = signal('');
```

Add computed:

```typescript
readonly cardDirty = computed(() => JSON.stringify(this.card()) !== JSON.stringify(this.savedCard()));
readonly markdownDirty = computed(() => this.markdown() !== this.savedMarkdown());
```

- [ ] **Step 3: Wire note open and structured save**

Update `openNote` success:

```typescript
this.selectedPath.set(response.path);
this.markdown.set(response.markdown);
this.savedMarkdown.set(response.markdown);
this.card.set(response.card);
this.savedCard.set(this.cloneCard(response.card));
this.viewMode.set('card');
this.status.set(`Opened ${note.name}`);
```

Add methods:

```typescript
setViewMode(mode: 'card' | 'markdown'): void {
  if (mode === 'card' && this.markdownDirty() && !window.confirm('Hay cambios Markdown sin guardar. ¿Salir sin guardar?')) {
    return;
  }
  if (mode === 'markdown' && this.cardDirty() && !window.confirm('Hay cambios en la ficha sin guardar. ¿Salir sin guardar?')) {
    return;
  }
  this.viewMode.set(mode);
}

updateCardField(field: 'summary' | 'notes', value: string): void {
  this.card.set({ ...this.card(), [field]: value });
}

updateTaskText(index: number, text: string): void {
  const tasks = this.card().tasks.map((task, current) => current === index ? { ...task, text } : task);
  this.card.set({ ...this.card(), tasks });
}

toggleTask(index: number): void {
  const tasks = this.card().tasks.map((task, current) => current === index ? { ...task, checked: !task.checked } : task);
  this.card.set({ ...this.card(), tasks });
}

addTask(): void {
  this.card.set({ ...this.card(), tasks: [...this.card().tasks, { text: '', checked: false }] });
}

removeTask(index: number): void {
  this.card.set({ ...this.card(), tasks: this.card().tasks.filter((_, current) => current !== index) });
}

saveCard(): void {
  const path = this.selectedPath();
  if (!path) {
    this.status.set('Select a note before saving.');
    return;
  }
  this.busy.set(true);
  this.status.set('Saving meeting card...');
  this.api.saveMeetingCard(path, this.card()).subscribe({
    next: () => {
      this.status.set('Saved');
      const selected = this.selectedNote();
      if (selected) {
        this.openNote(selected);
      }
    },
    error: (error) => this.fail(error),
    complete: () => this.busy.set(false)
  });
}

private cloneCard(card: MeetingCard): MeetingCard {
  return {
    summary: card.summary,
    notes: card.notes,
    tasks: card.tasks.map((task) => ({ ...task }))
  };
}
```

- [ ] **Step 4: Run frontend build**

Run:

```powershell
npm run build
```

Expected: TypeScript compiles.

- [ ] **Step 5: Commit**

```powershell
git add frontend/src/app/api.service.ts frontend/src/app/app.component.ts
git commit -m "feat: add editable meeting card state"
```

---

### Task 4: Card-First Angular UI

**Files:**
- Modify: `frontend/src/app/app.component.html`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Replace workspace center with card/markdown modes**

In `frontend/src/app/app.component.html`, keep sidebar and toolbar, then replace the editor grid area with:

```html
<section class="meeting-layout" *ngIf="selectedPath(); else emptyState">
  <article class="meeting-card" *ngIf="viewMode() === 'card'">
    <div class="card-header">
      <div>
        <p class="eyebrow">Ficha de reunión</p>
        <h3>{{ selectedName() }}</h3>
      </div>
      <button type="button" class="secondary" (click)="setViewMode('markdown')">Editar Markdown</button>
    </div>

    <label class="field-block">
      <span>Resumen</span>
      <textarea [ngModel]="card().summary" (ngModelChange)="updateCardField('summary', $event)"></textarea>
    </label>

    <section class="field-block">
      <div class="section-row">
        <span>Tareas</span>
        <button type="button" class="icon-action" (click)="addTask()">+</button>
      </div>
      <div class="task-row" *ngFor="let task of card().tasks; let index = index">
        <input type="checkbox" [checked]="task.checked" (change)="toggleTask(index)" />
        <input type="text" [ngModel]="task.text" (ngModelChange)="updateTaskText(index, $event)" />
        <button type="button" class="icon-action" (click)="removeTask(index)">×</button>
      </div>
      <p class="empty-copy" *ngIf="!card().tasks.length">Sin tareas registradas.</p>
    </section>

    <label class="field-block">
      <span>Notas</span>
      <textarea class="notes-area" [ngModel]="card().notes" (ngModelChange)="updateCardField('notes', $event)"></textarea>
    </label>

    <div class="card-actions">
      <button type="button" (click)="saveCard()" [disabled]="busy() || !cardDirty()">Guardar ficha</button>
      <span class="status" *ngIf="cardDirty()">Cambios sin guardar</span>
    </div>
  </article>

  <div class="editor-grid" *ngIf="viewMode() === 'markdown'">
    <section class="pane">
      <div class="pane-header">
        <span>Markdown</span>
        <button type="button" class="secondary" (click)="setViewMode('card')">Volver a ficha</button>
      </div>
      <textarea
        [ngModel]="markdown()"
        (ngModelChange)="updateMarkdown($event)"
        spellcheck="false"
        aria-label="Markdown editor"></textarea>
    </section>

    <section class="pane preview">
      <div class="pane-header">Preview</div>
      <article [innerHTML]="preview()"></article>
    </section>
  </div>

  <aside class="details-panel">
    <h3>Propiedades</h3>
    <div class="metadata-item" *ngFor="let item of selectedMetadata()">
      <span>{{ item.name }}</span>
      <strong>{{ item.value }}</strong>
    </div>
    <div class="metadata-item" *ngIf="selectedNote()?.last_edited_time">
      <span>Editado en Notion</span>
      <strong>{{ formatTimestamp(selectedNote()?.last_edited_time || '') }}</strong>
    </div>
    <div class="metadata-item" *ngIf="selectedNote()?.relative_path">
      <span>Obsidian</span>
      <strong>{{ selectedNote()?.relative_path }}</strong>
    </div>
  </aside>
</section>

<ng-template #emptyState>
  <section class="empty-state">
    <h3>Selecciona una reunión</h3>
    <p>Elige una nota sincronizada para revisar su ficha, editar secciones o abrir el Markdown completo.</p>
  </section>
</ng-template>
```

- [ ] **Step 2: Adjust toolbar save buttons**

In `frontend/src/app/app.component.html`, keep the existing top `Save` button only for Markdown mode:

```html
<button type="button" (click)="save()" [disabled]="busy() || !selectedPath() || viewMode() !== 'markdown'">Guardar Markdown</button>
```

- [ ] **Step 3: Add responsive styles**

Append to `frontend/src/styles.css`:

```css
.meeting-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  min-height: 0;
}

.meeting-card {
  padding: 28px;
  overflow: auto;
}

.card-header,
.section-row,
.card-actions {
  align-items: center;
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.field-block {
  display: grid;
  gap: 8px;
  margin-top: 22px;
}

.field-block > span,
.section-row > span {
  color: var(--muted);
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.field-block textarea,
.task-row input[type='text'] {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font: inherit;
  line-height: 1.55;
  padding: 12px;
  width: 100%;
}

.field-block textarea {
  min-height: 130px;
  resize: vertical;
}

.field-block .notes-area {
  min-height: 220px;
}

.task-row {
  align-items: center;
  display: grid;
  gap: 10px;
  grid-template-columns: auto minmax(0, 1fr) auto;
  margin-top: 8px;
}

.icon-action {
  align-items: center;
  border-radius: 999px;
  display: inline-flex;
  height: 32px;
  justify-content: center;
  padding: 0;
  width: 32px;
}

.details-panel {
  border-left: 1px solid var(--border);
  padding: 22px;
  overflow: auto;
}

.empty-state {
  display: grid;
  place-content: center;
  padding: 32px;
  text-align: center;
}

@media (max-width: 900px) {
  .meeting-layout {
    grid-template-columns: 1fr;
  }

  .details-panel {
    border-left: 0;
    border-top: 1px solid var(--border);
  }
}
```

- [ ] **Step 4: Build frontend**

Run:

```powershell
npm run build
```

Expected: production build succeeds.

- [ ] **Step 5: Commit**

```powershell
git add frontend/src/app/app.component.html frontend/src/styles.css
git commit -m "feat: make meeting card the default workspace"
```

---

### Task 5: Full Verification

**Files:**
- No source files expected unless verification reveals a bug.

- [ ] **Step 1: Run backend tests**

```powershell
python -m pytest
```

Expected: all tests pass.

- [ ] **Step 2: Run frontend build**

```powershell
npm run build
```

Expected: Angular build succeeds.

- [ ] **Step 3: Rebuild and start Docker**

```powershell
docker compose up -d --build
```

Expected: backend and frontend containers start.

- [ ] **Step 4: Check backend health**

```powershell
Invoke-RestMethod -Uri 'http://127.0.0.1:8765/health' | ConvertTo-Json
```

Expected:

```json
{
  "status": "ok"
}
```

- [ ] **Step 5: Manual browser verification**

Open:

```text
http://127.0.0.1:47863/
```

Verify:

- Selecting a note opens card mode by default.
- Editing `Resumen`, `Tareas`, and `Notas` enables `Guardar ficha`.
- Saving updates the `.md` in Obsidian.
- `Editar Markdown` shows full Markdown and preview.
- Saving Markdown refreshes card mode after reopening the note.
- Metadata displays generically.
- Mobile layout does not show the old oversized theme control.

- [ ] **Step 6: Final commit if verification fixes were needed**

```powershell
git status --short
```

Expected: clean, unless a verification fix was committed.

---

## Self-Review

- Spec coverage: covered structured card editing, Markdown advanced mode, Obsidian save, generic metadata display, mobile behavior, and tests.
- Placeholder scan: no `TODO`, `TBD`, or user-specific logic.
- Type consistency: `MeetingCard` and `MeetingTask` names are consistent across backend payloads and frontend interfaces.
