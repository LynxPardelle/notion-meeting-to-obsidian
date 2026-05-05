# Integrations

## Notion

The backend uses the official Notion REST API through `NotionClient`.

Implemented calls include:

- Database query: `POST /databases/{database_id}/query`.
- Data source query: `POST /data_sources/{data_source_id}/query` with Notion version `2025-09-03`.
- Database data source discovery: `GET /databases/{database_id}`.
- Page retrieval: `GET /pages/{page_id}`.
- Search visible pages: `POST /search`.
- Block children retrieval: `GET /blocks/{block_id}/children`.

Authentication uses `NOTION_TOKEN`.

## Obsidian

There is no Obsidian API integration. The app writes Markdown files directly into the configured vault folder.

Important variables:

- `OBSIDIAN_VAULT_PATH`
- `OBSIDIAN_MEETINGS_FOLDER`
- `HOST_OBSIDIAN_VAULT_PATH` for Docker bind mounts

## Local HTTP

The backend exposes a local FastAPI app. The frontend calls it through `/api`.

In Docker, Nginx forwards `/api` to the backend service. In local development, Angular uses `frontend/proxy.conf.js`.

## Docker

Docker Compose defines two services:

- `backend`: Python/FastAPI app on container port `8765`.
- `frontend`: Nginx-served Angular app on container port `8080`.

Host ports are dynamic:

- `BACKEND_PORT`, default `8765`.
- `FRONTEND_PORT`, default `47863`.

## External Hosted Services

No external database, hosted backend, queue, object storage, or analytics service is configured in the repo.

## Evidence

- `backend/src/notion_meeting_to_obsidian/notion.py`
- `backend/src/notion_meeting_to_obsidian/api.py`
- `backend/src/notion_meeting_to_obsidian/writer.py`
- `docker-compose.yml`
- `frontend/nginx.conf`
- `frontend/proxy.conf.js`
- `.env.example`
