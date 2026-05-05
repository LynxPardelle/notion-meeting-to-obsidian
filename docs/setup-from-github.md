# Setup From GitHub

This guide explains how to download the project from GitHub and run it on another computer.

The app syncs selected Notion pages into an Obsidian vault as local Markdown files.

## Requirements

Install these tools first:

- Git
- Docker Desktop
- Obsidian
- A Notion account with access to the pages you want to sync

Recommended Windows checks:

```powershell
git --version
docker --version
docker compose version
```

If Docker is installed but PowerShell does not find it, try:

```powershell
$env:Path = 'C:\Program Files\Docker\Docker\resources\bin;' + $env:Path
docker --version
```

## Download The Project

Choose a folder where you keep GitHub projects, then clone the repository:

```powershell
cd C:\Users\your-user\Documents\GitHub
git clone https://github.com/YOUR_GITHUB_USER/notion-meeting-to-obsidian.git
cd notion-meeting-to-obsidian
```

Replace `YOUR_GITHUB_USER` with the real GitHub account or organization that hosts the repo.

## Create A Notion Integration

1. Open Notion in the browser.
2. Go to `https://www.notion.so/profile/integrations`.
3. Create a new internal integration.
4. Copy the internal integration token.
5. Keep that token private. Do not commit it to GitHub.

The token usually starts with something like:

```txt
ntn_...
```

## Share Notion Pages With The Integration

The integration can only read pages that were explicitly shared with it.

For every page or database you want to sync:

1. Open the Notion page.
2. Click the three-dot menu in the top-right corner.
3. Open `Connections`.
4. Add your integration.
5. Save the access changes.

If a parent page has child pages, share the parent. The app will follow Notion child pages recursively when the integration can access them.

## Get The Notion Source ID

The app needs at least one source ID. A source can be:

- A Notion page ID
- A Notion database ID

Open the page in Notion and copy its URL. The ID is the long UUID-like part of the URL.

Example URL:

```txt
https://www.notion.so/Clase-Python-49591ac1d2684a7682613dc936387a0d
```

Source ID:

```txt
49591ac1d2684a7682613dc936387a0d
```

Both dashed and non-dashed IDs are acceptable in most cases.

If you want several roots, use `NOTION_SOURCE_IDS` with commas:

```txt
NOTION_SOURCE_IDS=id_1,id_2,id_3
```

## Find The Obsidian Vault Path

Open Obsidian and locate the vault folder on disk.

Example Windows paths:

```txt
C:\Users\your-user\Documents\Obsidian Vault
C:\Users\your-user\OneDrive\Documentos\Obsidian Vault
```

The app will create or update this folder inside the vault:

```txt
Meetings
```

The app treats Notion-generated Markdown files inside `Meetings` as a mirror of the selected Notion source tree. Manual notes without Notion frontmatter are left alone, but it is still cleaner to keep personal notes outside `Meetings`.

## Create The `.env` File

In the project folder, copy the example file:

```powershell
copy .env.example .env
```

Edit `.env` and fill in your values:

```txt
NOTION_TOKEN=ntn_your_private_token
NOTION_SOURCE_ID=your_main_page_or_database_id
NOTION_SOURCE_IDS=your_main_page_or_database_id
OBSIDIAN_VAULT_PATH=C:\Users\your-user\Documents\Obsidian Vault
OBSIDIAN_MEETINGS_FOLDER=Meetings
SYNC_STATE_PATH=
HOST_OBSIDIAN_VAULT_PATH=C:\Users\your-user\Documents\Obsidian Vault
NOTION_SYNC_ALL_ACCESSIBLE=false
OBSIDIAN_DELETE_STALE_SYNCED_NOTES=true
BIND_HOST=127.0.0.1
FRONTEND_PORT=47863
BACKEND_PORT=8765
CORS_ALLOW_ORIGINS=
```

For Docker on Windows, `HOST_OBSIDIAN_VAULT_PATH` is the important host path. Docker Compose mounts that folder into the backend container as `/vault`.

Use the same value for:

```txt
OBSIDIAN_VAULT_PATH
HOST_OBSIDIAN_VAULT_PATH
```

unless you know you need a custom setup.

`FRONTEND_PORT` controls the web app URL on your computer. `BACKEND_PORT` controls the direct API URL. Keep the defaults unless another local app is already using one of those ports.
`CORS_ALLOW_ORIGINS` is optional and normally stays empty.

## Run With Docker

Start Docker Desktop first. Wait until Docker says it is running.

Then run:

```powershell
docker compose up --build -d
```

Open the app:

```txt
http://127.0.0.1:47863
```

Backend health check:

```txt
http://127.0.0.1:8765/health
```

If you changed `FRONTEND_PORT` or `BACKEND_PORT` in `.env`, use those values in the URLs. For example, `FRONTEND_PORT=4300` means `http://127.0.0.1:4300`.

Expected health response:

```json
{"status":"ok"}
```

## Sync Notes

In the web app:

1. Click `Sync`.
2. Wait for the status message.
3. Open Obsidian.
4. Look inside the `Meetings` folder.

Parent pages with children are stored like this:

```txt
Meetings/
  Documento Padre/
    Documento Padre.md
    Nota Hijo.md
```

Obsidian may hide the `.md` extension in its file explorer. The files are still real Markdown files on disk.

## Update The App Later

From the project folder:

```powershell
git pull
docker compose up --build -d
```

## Stop The App

```powershell
docker compose down
```

## Troubleshooting

### Docker Command Not Found

Try:

```powershell
$env:Path = 'C:\Program Files\Docker\Docker\resources\bin;' + $env:Path
docker --version
```

Then run Docker Compose again.

### No Notes Appear

Check:

- `NOTION_TOKEN` is correct.
- The Notion page was shared with the integration.
- `NOTION_SOURCE_ID` or `NOTION_SOURCE_IDS` points to the right page/database.
- Docker was restarted after editing `.env`.

Restart:

```powershell
docker compose up --build -d
```

### Old Notion Notes Are Deleted

This is expected for Notion-generated files inside the configured `Meetings` folder. The app mirrors the selected Notion source tree and removes Markdown files that are no longer active in Notion when they are tracked in sync state or contain Notion frontmatter.

Manual notes without Notion frontmatter are preserved. Keeping personal notes outside `Meetings` is still recommended because that folder is primarily managed by the sync.

### Obsidian Does Not Refresh

Try:

- Close and reopen Obsidian.
- Use Obsidian's file explorer refresh.
- Confirm the files exist in Windows Explorer under your vault's `Meetings` folder.
