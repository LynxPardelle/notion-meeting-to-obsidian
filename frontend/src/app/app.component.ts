import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService, MeetingCard, NoteSummary } from './api.service';

type ThemePreference = 'light' | 'dark';
type ViewMode = 'card' | 'markdown';

interface NoteTreeItem {
  note: NoteSummary;
  key: string;
  parentKey: string | null;
  depth: number;
  hasChildren: boolean;
  childCount: number;
  childNames: string[];
}

interface NoteSourceGroup {
  label: string;
  items: NoteTreeItem[];
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html'
})
export class AppComponent {
  readonly notes = signal<NoteSummary[]>([]);
  readonly selectedPath = signal('');
  readonly markdown = signal('');
  readonly savedMarkdown = signal('');
  readonly card = signal<MeetingCard>({ summary: '', tasks: [], notes: '' });
  readonly savedCard = signal<MeetingCard>({ summary: '', tasks: [], notes: '' });
  readonly viewMode = signal<ViewMode>('card');
  readonly status = signal('Ready');
  readonly busy = signal(false);
  readonly collapsedKeys = signal<Set<string>>(new Set());
  readonly themePreference = signal<ThemePreference>('light');

  readonly selectedName = computed(() => {
    return this.selectedNote()?.name ?? 'No note selected';
  });

  readonly selectedNote = computed(() => {
    const path = this.selectedPath();
    return this.notes().find((note) => note.path === path) ?? null;
  });

  readonly selectedMetadata = computed(() => this.selectedNote()?.metadata ?? []);
  readonly preview = computed(() => this.renderPreview(this.markdown()));
  readonly treeItems = computed(() => this.buildTreeItems(this.notes()));
  readonly visibleTreeItems = computed(() => this.treeItems().filter((item) => !this.isHiddenByCollapsedAncestor(item)));
  readonly visibleSourceGroups = computed(() => this.groupBySource(this.visibleTreeItems()));
  readonly cardDirty = computed(() => JSON.stringify(this.card()) !== JSON.stringify(this.savedCard()));
  readonly markdownDirty = computed(() => this.markdown() !== this.savedMarkdown());

  constructor(private readonly api: ApiService) {
    this.loadThemePreference();
    this.refreshNotes();
  }

  sync(): void {
    this.busy.set(true);
    this.status.set('Syncing Notion...');
    this.api.sync(false).subscribe({
      next: (result) => {
        const deleted = result.deleted?.length ?? 0;
        this.status.set(`${result.synced.length} synced, ${result.skipped.length} skipped, ${deleted} removed`);
        this.refreshNotes();
      },
      error: (error) => this.fail(error),
      complete: () => this.busy.set(false)
    });
  }

  refreshNotes(): void {
    this.api.listNotes().subscribe({
      next: (notes) => {
        this.notes.set(notes);
        this.collapsedKeys.set(this.collapsibleKeys(this.buildTreeItems(notes)));
      },
      error: (error) => this.fail(error)
    });
  }

  openNote(note: NoteSummary): void {
    this.busy.set(true);
    this.status.set(`Opening ${note.name}`);
    this.api.readNote(note.path).subscribe({
      next: (response) => {
        this.selectedPath.set(response.path);
        this.markdown.set(response.markdown);
        this.savedMarkdown.set(response.markdown);
        this.card.set(this.cloneCard(response.card));
        this.savedCard.set(this.cloneCard(response.card));
        this.viewMode.set('card');
        this.status.set(`Opened ${note.name}`);
      },
      error: (error) => this.fail(error),
      complete: () => this.busy.set(false)
    });
  }

  save(): void {
    const path = this.selectedPath();
    if (!path) {
      this.status.set('Select a note before saving.');
      return;
    }
    this.busy.set(true);
    this.status.set('Saving note...');
    this.api.saveNote(path, this.markdown()).subscribe({
      next: () => {
        this.status.set('Saved');
        this.savedMarkdown.set(this.markdown());
        this.refreshNotes();
      },
      error: (error) => this.fail(error),
      complete: () => this.busy.set(false)
    });
  }

  updateMarkdown(value: string): void {
    this.markdown.set(value);
  }

  saveCurrentView(): void {
    if (this.viewMode() === 'markdown') {
      this.save();
      return;
    }
    this.saveCard();
  }

  setViewMode(mode: ViewMode): void {
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
    const tasks = this.card().tasks.map((task, current) => (current === index ? { ...task, text } : task));
    this.card.set({ ...this.card(), tasks });
  }

  toggleTask(index: number): void {
    const tasks = this.card().tasks.map((task, current) =>
      current === index ? { ...task, checked: !task.checked } : task
    );
    this.card.set({ ...this.card(), tasks });
  }

  addTask(): void {
    this.card.set({ ...this.card(), tasks: [...this.card().tasks, { text: '', checked: false }] });
  }

  removeTask(index: number): void {
    this.card.set({ ...this.card(), tasks: this.card().tasks.filter((_, current) => current !== index) });
  }

  canSaveCurrentView(): boolean {
    if (this.busy() || !this.selectedPath()) {
      return false;
    }
    return this.viewMode() === 'markdown' ? this.markdownDirty() : this.cardDirty();
  }

  currentSaveLabel(): string {
    return this.viewMode() === 'markdown' ? 'Guardar Markdown' : 'Guardar ficha';
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

  setThemePreference(theme: ThemePreference): void {
    this.themePreference.set(theme);
    localStorage.setItem('notion-obsidian-theme', theme);
    this.applyTheme(theme);
  }

  isThemeSelected(theme: ThemePreference): boolean {
    return this.themePreference() === theme;
  }

  toggleTheme(): void {
    this.setThemePreference(this.themePreference() === 'dark' ? 'light' : 'dark');
  }

  treeIndent(item: NoteTreeItem): string {
    return `${item.depth * 18}px`;
  }

  itemParentLabel(item: NoteTreeItem): string {
    if (!item.parentKey) {
      return '';
    }
    return item.parentKey.split('/').at(-1) ?? item.parentKey;
  }

  noteSubtitle(note: NoteSummary): string {
    const values = note.metadata
      .filter((item) => item.type !== 'rich_text')
      .slice(0, 2)
      .map((item) => item.value)
      .filter(Boolean);
    return values.join(' · ');
  }

  sourceLabel(note: NoteSummary): string {
    return note.source_label?.trim() || 'Notas sin tabla';
  }

  shouldShowSourceGroups(): boolean {
    const groups = this.visibleSourceGroups();
    return groups.length > 1 || (groups[0]?.label ?? '') !== 'Notas sin tabla';
  }

  childPreview(item: NoteTreeItem): string {
    if (!item.childNames.length) {
      return '';
    }
    const visible = item.childNames.slice(0, 2).join(', ');
    const remaining = item.childNames.length - 2;
    return remaining > 0 ? `${visible} +${remaining}` : visible;
  }

  formatTimestamp(value: string): string {
    if (!value) {
      return '';
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return new Intl.DateTimeFormat('es-MX', {
      dateStyle: 'medium',
      timeStyle: value.includes('T') ? 'short' : undefined
    }).format(date);
  }

  isCollapsed(item: NoteTreeItem): boolean {
    return this.collapsedKeys().has(item.key);
  }

  toggleCollapsed(item: NoteTreeItem, event: Event): void {
    event.stopPropagation();
    const next = new Set(this.collapsedKeys());
    if (next.has(item.key)) {
      next.delete(item.key);
    } else {
      next.add(item.key);
    }
    this.collapsedKeys.set(next);
  }

  private fail(error: unknown): void {
    this.busy.set(false);
    const message = this.errorMessage(error);
    this.status.set(message);
  }

  private errorMessage(error: unknown): string {
    if (error instanceof HttpErrorResponse) {
      const detail = error.error?.detail;
      if (typeof detail === 'string' && detail.trim()) {
        return detail;
      }
      if (detail) {
        return JSON.stringify(detail);
      }
      if (error.message) {
        return error.message;
      }
    }
    return error instanceof Error ? error.message : 'Request failed';
  }

  private isHiddenByCollapsedAncestor(item: NoteTreeItem): boolean {
    const parts = item.key.split('/');
    return parts.slice(0, -1).some((_, index) => this.collapsedKeys().has(parts.slice(0, index + 1).join('/')));
  }

  private buildTreeItems(notes: NoteSummary[]): NoteTreeItem[] {
    const provisional = notes.map((note, index) => {
      const parts = this.hierarchyParts(note);
      return {
        note,
        key: parts.join('/'),
        parentKey: parts.length > 1 ? parts.slice(0, -1).join('/') : null,
        depth: Math.max(0, parts.length - 1),
        index
      };
    });
    const directChildren = new Map<string, string[]>();
    for (const item of provisional) {
      if (!item.parentKey) {
        continue;
      }
      directChildren.set(item.parentKey, [...(directChildren.get(item.parentKey) ?? []), item.note.name]);
    }
    return provisional
      .map((item) => ({
        note: item.note,
        key: item.key,
        parentKey: item.parentKey,
        depth: item.depth,
        hasChildren: directChildren.has(item.key),
        childCount: directChildren.get(item.key)?.length ?? 0,
        childNames: directChildren.get(item.key) ?? [],
        index: item.index
      }))
      .sort((left, right) => this.compareTreeItems(left, right))
      .map(({ index: _index, ...item }) => item);
  }

  private compareTreeItems(left: NoteTreeItem & { index: number }, right: NoteTreeItem & { index: number }): number {
    const leftParts = left.key.split('/');
    const rightParts = right.key.split('/');
    const shared = Math.min(leftParts.length, rightParts.length);
    for (let index = 0; index < shared; index += 1) {
      const comparison = leftParts[index].localeCompare(rightParts[index], 'es', { sensitivity: 'base' });
      if (comparison !== 0) {
        return comparison;
      }
    }
    if (leftParts.length !== rightParts.length) {
      return leftParts.length - rightParts.length;
    }
    return left.index - right.index;
  }

  private groupBySource(items: NoteTreeItem[]): NoteSourceGroup[] {
    const groups: NoteSourceGroup[] = [];
    const byLabel = new Map<string, NoteSourceGroup>();
    for (const item of items) {
      const label = this.sourceLabel(item.note);
      let group = byLabel.get(label);
      if (!group) {
        group = { label, items: [] };
        byLabel.set(label, group);
        groups.push(group);
      }
      group.items.push(item);
    }
    return groups;
  }

  private hierarchyParts(note: NoteSummary): string[] {
    if (note.parent) {
      return this.compactRepeatedParts([...this.splitTreePath(note.parent), note.name]);
    }
    return this.relativeParts(note);
  }

  private splitTreePath(value: string): string[] {
    return value
      .split(/[\\/]/)
      .map((part) => part.trim())
      .filter(Boolean);
  }

  private compactRepeatedParts(parts: string[]): string[] {
    const compacted: string[] = [];
    for (const part of parts) {
      const previous = compacted.at(-1);
      if (previous && this.normalizeTreePart(previous) === this.normalizeTreePart(part)) {
        continue;
      }
      compacted.push(part);
    }
    return compacted;
  }

  private relativeParts(note: NoteSummary): string[] {
    const parts = note.relative_path.split(/[\\/]/).filter(Boolean);
    if (!parts.length) {
      return [note.name.replace(/\.md$/i, '')];
    }

    parts[parts.length - 1] = parts[parts.length - 1].replace(/\.md$/i, '');

    const last = parts.at(-1);
    const previous = parts.at(-2);
    if (last && previous && this.normalizeTreePart(last) === this.normalizeTreePart(previous)) {
      parts.pop();
    }

    return parts;
  }

  private normalizeTreePart(value: string): string {
    return value.trim().toLowerCase();
  }

  private collapsibleKeys(items: NoteTreeItem[]): Set<string> {
    return new Set(items.filter((item) => item.hasChildren).map((item) => item.key));
  }

  private loadThemePreference(): void {
    const stored = localStorage.getItem('notion-obsidian-theme');
    const theme = this.isThemePreference(stored) ? stored : 'light';
    this.themePreference.set(theme);
    this.applyTheme(theme);
  }

  private isThemePreference(value: string | null): value is ThemePreference {
    return value === 'light' || value === 'dark';
  }

  private applyTheme(theme: ThemePreference): void {
    document.documentElement.dataset['theme'] = theme;
  }

  private cloneCard(card: MeetingCard): MeetingCard {
    return {
      summary: card.summary,
      tasks: card.tasks.map((task) => ({ ...task })),
      notes: card.notes
    };
  }

  private renderPreview(markdown: string): string {
    return markdown
      .replace(/^---[\s\S]*?---\n*/m, '')
      .replace(/^# (.*)$/gm, '<h1>$1</h1>')
      .replace(/^## (.*)$/gm, '<h2>$1</h2>')
      .replace(/^### (.*)$/gm, '<h3>$1</h3>')
      .replace(/^- \[ \] (.*)$/gm, '<p class="task">☐ $1</p>')
      .replace(/^- \[x\] (.*)$/gim, '<p class="task">☑ $1</p>')
      .replace(/^- (.*)$/gm, '<p>• $1</p>')
      .replace(/\n\n/g, '<br><br>');
  }
}
