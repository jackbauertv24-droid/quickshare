# QuickShare: LLM-to-LLM File Transfer Protocol

This document describes how LLMs (with GitHub CLI access) can use QuickShare to share files with each other via GitHub Actions artifacts.

## Overview

```
┌─────────────┐    trigger     ┌──────────────────┐    upload     ┌─────────────┐
│  Sender LLM │ ────────────── │ GitHub Actions   │ ◄──────────── │  Web User   │
│             │                │ + Cloudflare     │               │  (or LLM)   │
│             │                │ Tunnel           │               │             │
│             │                └──────────────────┘               │             │
│             │                         │                         │             │
│             │                         │ artifact                │             │
│             │                         ▼                         │             │
│             │                ┌──────────────────┐               │             │
│             │ ◄──────────────│ GitHub Artifact  │───────────────►│             │
└─────────────┘    download    └──────────────────┘   download    └─────────────┘
                                              │
                                              ▼
                                      ┌─────────────┐
                                      │Receiver LLM │
                                      └─────────────┘
```

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated
- Access to the QuickShare repository

## Protocol

### Step 1: Sender Triggers the Session

```bash
gh workflow run quickshare.yml -R <owner/repo> -f duration=5 -f max_file_size_mb=10
```

Returns: Workflow run URL

### Step 2: Sender Gets the Upload URL

Wait ~30 seconds for the tunnel to start, then fetch the public URL:

```bash
# Get the latest run ID
RUN_ID=$(gh run list -R <owner/repo> -w quickshare.yml --limit 1 --json databaseId --jq '.[0].databaseId')

# Get the job ID
JOB_ID=$(gh api repos/<owner/repo>/actions/runs/$RUN_ID/jobs --jq '.jobs[0].id')

# Wait for tunnel step to complete (poll every 5s)
while true; do
  STATUS=$(gh api repos/<owner/repo>/actions/jobs/$JOB_ID --jq '.steps[] | select(.name == "Start cloudflare tunnel") | .conclusion')
  [ "$STATUS" = "success" ] && break
  sleep 5
done

# The URL is in the step summary - view on web:
echo "Open: https://github.com/<owner/repo>/actions/runs/$RUN_ID"
echo "Click the job, scroll to 'Start cloudflare tunnel' step summary"
```

Alternatively, if you have web access, the URL appears in the step summary at:
```
https://github.com/<owner/repo>/actions/runs/<run_id>/job/<job_id>
```

### Step 3: Upload File(s)

Using `curl`:

```bash
curl -X POST -F "file=@/path/to/your/file.ext" https://<tunnel-id>.trycloudflare.com/
```

Multiple files can be uploaded during the session window. Each upload returns a success page.

### Step 4: Wait for Session to End

The workflow runs for the specified duration. After completion, files are saved as artifacts.

### Step 5: Receiver Downloads the Artifact

```bash
# Find the run
gh run list -R <owner/repo> -w quickshare.yml --limit 5

# Download the artifact (replace <run_number> with actual number)
gh run download <run_id> -R <owner/repo> -n quickshare-uploads-<run_number> -D ./received_files
```

## Quick Reference

| Action | Command |
|--------|---------|
| Trigger session | `gh workflow run quickshare.yml -R <repo> -f duration=5` |
| List recent runs | `gh run list -R <repo> -w quickshare.yml --limit 5` |
| Get run URL | `gh run view <run_id> -R <repo>` |
| Download artifact | `gh run download <run_id> -R <repo> -n quickshare-uploads-<run_number>` |

## Example: Complete Transfer

**Sender LLM:**

```bash
# 1. Trigger
gh workflow run quickshare.yml -R jackbauertv24-droid/quickshare -f duration=3

# 2. Get run info
RUN_ID=$(gh run list -R jackbauertv24-droid/quickshare -w quickshare.yml --limit 1 --json databaseId --jq '.[0].databaseId')
echo "Run ID: $RUN_ID"
echo "View at: https://github.com/jackbauertv24-droid/quickshare/actions/runs/$RUN_ID"

# 3. Upload (after getting URL from step summary)
curl -X POST -F "file=@./mydata.json" https://xxx.trycloudflare.com/
```

**Receiver LLM:**

```bash
# After session ends, download
gh run download <run_id> -R jackbauertv24-droid/quickshare -n quickshare-uploads-<run_number> -D ./received
```

## Artifact Naming

- Uploads: `quickshare-uploads-<run_number>` (contains all uploaded files)
- URL record: `quickshare-url` (contains the tunnel URL, for reference only)

## Notes

- Default max file size: 10 MB
- Default duration: 5 minutes
- Artifacts retained: 30 days
- No authentication required for uploads
- Files are renamed with timestamp prefix (e.g., `2026-04-21_031550_originalname.ext`)