import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface NoteSummary {
  name: string;
  path: string;
  relative_path: string;
  depth: number;
  parent: string | null;
}

export interface ReadNoteResponse {
  path: string;
  markdown: string;
}

export interface SyncResponse {
  synced: Array<{ page_id: string; title: string; file_path: string; changed: boolean; parent_id: string | null; depth: number }>;
  skipped: Array<{ page_id: string; title: string; file_path: string; changed: boolean; parent_id: string | null; depth: number }>;
  deleted?: string[];
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly baseUrl = 'http://127.0.0.1:8765';

  constructor(private readonly http: HttpClient) {}

  sync(force = false): Observable<SyncResponse> {
    return this.http.post<SyncResponse>(`${this.baseUrl}/sync?force=${force}`, {});
  }

  listNotes(): Observable<NoteSummary[]> {
    return this.http.get<NoteSummary[]>(`${this.baseUrl}/notes`);
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
}
