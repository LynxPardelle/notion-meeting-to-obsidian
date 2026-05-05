import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface NoteSummary {
  created_time: string;
  last_edited_time: string;
  metadata: NoteMetadata[];
  name: string;
  notion_url: string;
  path: string;
  relative_path: string;
  depth: number;
  parent: string | null;
  parent_id: string | null;
  source_id: string;
  source_label: string;
}

export interface NoteMetadata {
  name: string;
  type: string;
  value: string;
}

export interface NoteSource {
  id: string;
  name: string;
  note_count: number;
}

export interface NoteSourceProperty {
  name: string;
  type: string;
  usage_count: number;
  sample: string;
}

export interface NoteSourceMapping {
  date: string | null;
  notes: string | null;
  people: string | null;
  status: string | null;
  summary: string | null;
  tasks: string | null;
}

export interface NoteSourceSchema {
  id: string;
  name: string;
  note_count: number;
  properties: NoteSourceProperty[];
  mapping: NoteSourceMapping;
}

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

export interface SyncResponse {
  synced: Array<{ page_id: string; title: string; file_path: string; changed: boolean; parent_id: string | null; depth: number }>;
  skipped: Array<{ page_id: string; title: string; file_path: string; changed: boolean; parent_id: string | null; depth: number }>;
  deleted?: string[];
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly baseUrl = '/api';

  constructor(private readonly http: HttpClient) {}

  sync(force = false): Observable<SyncResponse> {
    return this.http.post<SyncResponse>(`${this.baseUrl}/sync?force=${force}`, {});
  }

  listNotes(): Observable<NoteSummary[]> {
    return this.http.get<NoteSummary[]>(`${this.baseUrl}/notes`);
  }

  listNoteSources(): Observable<NoteSource[]> {
    return this.http.get<NoteSource[]>(`${this.baseUrl}/note-sources`);
  }

  listNoteSourceSchemas(): Observable<NoteSourceSchema[]> {
    return this.http.get<NoteSourceSchema[]>(`${this.baseUrl}/note-sources/schema`);
  }

  readNote(path: string): Observable<ReadNoteResponse> {
    return this.http.get<ReadNoteResponse>(`${this.baseUrl}/notes/read`, { params: { path } });
  }

  saveNote(path: string, markdown: string): Observable<{ path: string; status: string }> {
    return this.http.post<{ path: string; status: string }>(`${this.baseUrl}/notes/save`, {
      path,
      markdown
    });
  }

  saveMeetingCard(path: string, card: MeetingCard): Observable<{ path: string; status: string }> {
    return this.http.post<{ path: string; status: string }>(`${this.baseUrl}/notes/card/save`, {
      path,
      card
    });
  }
}
