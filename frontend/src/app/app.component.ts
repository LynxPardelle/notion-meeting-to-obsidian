import { CommonModule } from '@angular/common';
import { Component, computed, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService, NoteSummary } from './api.service';

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

  readonly selectedName = computed(() => {
    const path = this.selectedPath();
    return this.notes().find((note) => note.path === path)?.name ?? 'No note selected';
  });

  readonly preview = computed(() => this.renderPreview(this.markdown()));

  constructor(private readonly api: ApiService) {
    this.refreshNotes();
  }

  sync(): void {
    this.busy.set(true);
    this.status.set('Syncing Notion...');
    this.api.sync(false).subscribe({
      next: (result) => {
        this.status.set(`${result.synced.length} synced, ${result.skipped.length} skipped`);
        this.refreshNotes();
      },
      error: (error) => this.fail(error),
      complete: () => this.busy.set(false)
    });
  }

  refreshNotes(): void {
    this.api.listNotes().subscribe({
      next: (notes) => this.notes.set(notes),
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

  private fail(error: unknown): void {
    this.busy.set(false);
    const message = error instanceof Error ? error.message : 'Request failed';
    this.status.set(message);
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
