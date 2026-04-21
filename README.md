# QuickShare

Ephemeral file upload server powered by GitHub Actions. Spin up a temporary public upload endpoint in seconds.

## How It Works

1. Trigger the GitHub Action manually
2. A cloudflare tunnel exposes the upload server to the public internet
3. Share the generated URL with anyone who needs to upload files
4. Files are saved as GitHub Artifacts after the session ends

## Usage

### Via GitHub CLI (Recommended)

```bash
# Trigger with default 5-minute duration
./gh-quickshare.sh

# Custom duration (in minutes)
./gh-quickshare.sh 10

# Specify repo
./gh-quickshare.sh 5 owner/repo
```

### Via GitHub Web UI

1. Go to Actions → QuickShare
2. Click "Run workflow"
3. Set duration and max file size
4. Wait for the workflow to start
5. Check the logs for the public URL
6. Share that URL

## Files

| File | Purpose |
|------|---------|
| `upload_server.py` | Local standalone server (single file) |
| `upload_server_gh.py` | GitHub Actions version (multi-file, configurable) |
| `gh-quickshare.sh` | CLI helper to trigger and watch the workflow |
| `.github/workflows/quickshare.yml` | GitHub Actions workflow |

## Local Usage

```bash
# Simple local server (overwrites same file)
python upload_server.py

# Multi-file local server
python upload_server_gh.py
PORT=9000 UPLOAD_DIR=./myuploads python upload_server_gh.py
```

## Security Notes

- Files are saved with sanitized names (no path traversal)
- Max file size is configurable (default 10MB)
- Server runs for a limited time only
- Artifacts are only visible to repo collaborators
- No authentication - anyone with the URL can upload

## Configuration (GitHub Actions)

| Input | Default | Description |
|-------|---------|-------------|
| `duration` | 5 | Server uptime in minutes |
| `max_file_size_mb` | 10 | Max upload size in MB |