#!/usr/bin/env bash
set -euo pipefail

# ----------------------------------------------------
# 1️⃣  EXPECTED FILE NAMING
# ----------------------------------------------------
# Demo transcripts:   data/demo/demo_001.txt … demo_005.txt
# Onboard transcripts: data/onboard/onboard_001.txt … onboard_005.txt
# The numeric part must match across the two sets.

# ----------------------------------------------------
# 2️⃣  PROCESS DEMO (v1)
# ----------------------------------------------------
echo "=== Running Demo → v1 pipeline for all demo files ==="
for demo_path in data/demo/*.txt; do
  base=$(basename "$demo_path" .txt)   # e.g. demo_001
  account_id="${base}"                # we just reuse the filename as ID
  echo "🔹 Processing $demo_path (account: $account_id)"

  # Call n8n webhook for demo
  curl -s -X POST "http://localhost:5678/webhook-demo" \
    -H "Content-Type: application/json" \
    -d "{\"account_id\":\"$account_id\",\"transcript_path\":\"$demo_path\"}"
done

# ----------------------------------------------------
# 3️⃣  PROCESS ONBOARDING (v2)
# ----------------------------------------------------
echo "=== Running Onboarding → v2 pipeline for all onboarding files ==="
for onboard_path in data/onboard/*.txt; do
  # Assume the onboarding file has the same numeric suffix as its demo counterpart
  base=$(basename "$onboard_path" .txt)   # e.g. onboard_001
  # Strip the "onboard_" prefix to get the account_id
  account_id="${base#onboard_}"
  echo "🔹 Updating $account_id with $onboard_path"

  curl -s -X POST "http://localhost:5678/webhook-onboard" \
    -H "Content-Type: application/json" \
    -d "{\"account_id\":\"$account_id\",\"onboard_path\":\"$onboard_path\"}"
done

echo "✅ All pipelines executed. Check the outputs/ directory."
