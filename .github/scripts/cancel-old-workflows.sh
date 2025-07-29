#!/bin/bash
# Script to cancel workflow runs from old commits

echo "🔍 Checking for workflow runs from old commits..."

# Get the SHA mentioned in the error
OLD_SHA="2d46073749314641a1bb6f785efd54a2a6ee44d1"

# List workflow runs
echo "Fetching workflow runs..."
gh run list --limit 50 --json databaseId,headSha,status,name,workflowName | jq -r '.[] | select(.headSha | startswith("'${OLD_SHA:0:7}'")) | "\(.databaseId) \(.status) \(.workflowName)"'

# Cancel any running workflows from the old SHA
echo "Cancelling workflows from SHA ${OLD_SHA:0:7}..."
gh run list --limit 50 --json databaseId,headSha,status | jq -r '.[] | select(.headSha | startswith("'${OLD_SHA:0:7}'")) | select(.status == "in_progress" or .status == "queued") | .databaseId' | while read run_id; do
    echo "Cancelling run $run_id"
    gh run cancel $run_id
done

echo "✅ Done!"
