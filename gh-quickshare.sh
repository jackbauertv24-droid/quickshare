#!/bin/bash

set -e

DURATION=${1:-5}
REPO=${2:-}

if [ -z "$REPO" ]; then
    REPO=$(git remote get-url origin 2>/dev/null | sed 's/.*github.com[/:]//' | sed 's/\.git$//')
fi

if [ -z "$REPO" ]; then
    echo "Usage: $0 [duration_minutes] [owner/repo]"
    echo "  duration_minutes: How long the server should run (default: 5)"
    echo "  owner/repo: GitHub repository (default: auto-detect from git remote)"
    exit 1
fi

echo "Triggering QuickShare on $REPO for $DURATION minutes..."
gh workflow run quickshare.yml -R "$REPO" -f duration="$DURATION"

echo ""
echo "Waiting for workflow to start..."
sleep 3

RUN_ID=$(gh run list -R "$REPO" -w quickshare.yml --limit 1 --json databaseId --jq '.[0].databaseId')

echo "Workflow run ID: $RUN_ID"
echo ""
echo "Watching logs (press Ctrl+C to stop watching)..."
echo "The public URL will appear in the logs below:"
echo ""

gh run watch "$RUN_ID" -R "$REPO"