# Sprint 1 Visual Tree and Theme Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Improve the Angular app's note navigation by rendering deep parent/child/grandchild hierarchy clearly, defaulting groups to collapsed, and adding light/dark theme selection.

**Architecture:** Keep the current single Angular component structure for this sprint. Add focused helper methods for tree depth, collapsed state, theme state, and CSS variables without changing the backend API.

**Tech Stack:** Angular standalone component, TypeScript signals, CSS custom properties, `localStorage`, Angular production build.

---

## Files

- Modify: `frontend/src/app/app.component.ts`
- Modify: `frontend/src/app/app.component.html`
- Modify: `frontend/src/styles.css`
- Verify: `frontend/package.json`

## Task 1: Tree Depth and Default Collapse

**Files:**
- Modify: `frontend/src/app/app.component.ts`
- Modify: `frontend/src/app/app.component.html`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Define the behavior to verify manually**

Use this note shape in the running app or browser devtools when checking behavior:

```ts
[
  { name: 'Padre', relative_path: 'Padre/Padre.md', depth: 0 },
  { name: 'Hijo', relative_path: 'Padre/Hijo/Hijo.md', depth: 1 },
  { name: 'Nieto', relative_path: 'Padre/Hijo/Nieto.md', depth: 2 }
]
```

Expected behavior:

```txt
Padre starts collapsed.
Clicking Padre shows Hijo indented one level.
Clicking Hijo shows Nieto indented two levels.
Refreshing notes collapses all groups again.
```

- [ ] **Step 2: Update component helpers**

Add public helpers:

```ts
noteDepth(note: NoteSummary): number {
  return Math.max(0, this.relativeParts(note).length - 1);
}

treeIndent(note: NoteSummary): string {
  return `${this.noteDepth(note) * 18}px`;
}
```

Make `relativeParts()` collapse folder-note duplicates, so `Documento Padre/Documento Padre.md` displays as one node while deeper children still calculate correctly.

- [ ] **Step 3: Update template**

Use CSS custom property binding:

```html
[style.--depth.px]="noteDepth(note)"
```

Use disclosure buttons only for nodes that have children, and hide descendants when any ancestor is collapsed.

- [ ] **Step 4: Update CSS**

Replace the single `.child` offset with depth-aware rules:

```css
.note-list button {
  padding-left: calc(8px + (var(--depth, 0) * 18px));
}
```

Use subtle connector styling so deep levels remain readable.

- [ ] **Step 5: Verify**

Run:

```bash
npm run build
```

Expected: Angular build succeeds.

## Task 2: Theme Preference

**Files:**
- Modify: `frontend/src/app/app.component.ts`
- Modify: `frontend/src/app/app.component.html`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Define theme modes**

Add a theme type:

```ts
type ThemePreference = 'light' | 'dark';
```

- [ ] **Step 2: Add state and persistence**

Add signal and methods:

```ts
readonly themePreference = signal<ThemePreference>('light');

setThemePreference(theme: ThemePreference): void {
  this.themePreference.set(theme);
  localStorage.setItem('notion-obsidian-theme', theme);
  this.applyTheme(theme);
}
```

`applyTheme()` should set `document.documentElement.dataset.theme` to `light` or `dark`.

- [ ] **Step 3: Add UI control**

Add a compact segmented control in the sidebar:

```html
<button type="button" (click)="setThemePreference('light')">Claro</button>
<button type="button" (click)="setThemePreference('dark')">Oscuro</button>
```

Show the active option with an `.active` class.

- [ ] **Step 4: Add CSS tokens**

Define:

```css
:root[data-theme="light"] { ... }
:root[data-theme="dark"] { ... }
```

Use variables for backgrounds, panels, ink, muted text, borders, editor, hover, and preview.

- [ ] **Step 5: Verify**

Run:

```bash
npm run build
```

Expected: Angular build succeeds and theme buttons compile.

## Task 3: Manual UI Verification

**Files:**
- Verify: running Angular app

- [ ] **Step 1: Start or rebuild the app**

Run:

```bash
docker compose up --build -d
```

Expected: backend and frontend containers are running.

- [ ] **Step 2: Check browser**

Open:

```txt
http://127.0.0.1:<frontend-port>/
```

Expected:

```txt
The app loads.
Tree groups are collapsed by default.
Opening nested groups shows deeper indentation.
Theme control switches between light and dark.
Opening, editing, and saving an existing note still works.
```

- [ ] **Step 3: Commit**

Run:

```bash
git add frontend/src/app/app.component.ts frontend/src/app/app.component.html frontend/src/styles.css docs/superpowers/plans/2026-05-01-sprint-1-visual-tree-and-theme.md
git commit -m "feat: improve note tree and theme controls"
```
