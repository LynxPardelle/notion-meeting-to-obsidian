import { CommonModule } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService, NoteSummary } from './api.service';

type ThemePreference = 'light' | 'dark';

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
  readonly status = signal('Ready');
  readonly busy = signal(false);
  readonly collapsedKeys = signal<Set<string>>(new Set());
  readonly themePreference = signal<ThemePreference>('light');

  readonly selectedName = computed(() => {
    const path = this.selectedPath();
    return this.notes().find((note) => note.path === path)?.name ?? 'No note selected';
  });

  readonly preview = computed(() => this.renderPreview(this.markdown()));
  readonly visibleNotes = computed(() => this.notes().filter((note) => !this.isHiddenByCollapsedAncestor(note)));

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
        this.collapsedKeys.set(this.collapsibleKeys(notes));
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
        this.refreshNotes();
      },
      error: (error) => this.fail(error),
      complete: () => this.busy.set(false)
    });
  }

  updateMarkdown(value: string): void {
    this.markdown.set(value);
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

  noteDepth(note: NoteSummary): number {
    return Math.max(0, this.relativeParts(note).length - 1);
  }

  treeIndent(note: NoteSummary): string {
    return `${this.noteDepth(note) * 18}px`;
  }

  hasChildren(note: NoteSummary): boolean {
    const key = this.treeKey(note);
    return this.notes().some((candidate) => this.parentKeys(candidate).includes(key));
  }

  isCollapsed(note: NoteSummary): boolean {
    return this.collapsedKeys().has(this.treeKey(note));
  }

  toggleCollapsed(note: NoteSummary, event: Event): void {
    event.stopPropagation();
    const key = this.treeKey(note);
    const next = new Set(this.collapsedKeys());
    if (next.has(key)) {
      next.delete(key);
    } else {
      next.add(key);
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

  private isHiddenByCollapsedAncestor(note: NoteSummary): boolean {
    return this.parentKeys(note).some((key) => this.collapsedKeys().has(key));
  }

  private parentKeys(note: NoteSummary): string[] {
    const parts = this.relativeParts(note);
    return parts.slice(0, -1).map((_, index) => parts.slice(0, index + 1).join('/'));
  }

  private treeKey(note: NoteSummary): string {
    return this.relativeParts(note).join('/');
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

  private collapsibleKeys(notes: NoteSummary[]): Set<string> {
    const keys = new Set<string>();
    for (const note of notes) {
      for (const key of this.parentKeys(note)) {
        keys.add(key);
      }
    }
    return keys;
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
