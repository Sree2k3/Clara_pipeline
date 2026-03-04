#!/usr/bin/env bash
# ----------------------------------------------------
# run_all.sh – one‑click demo + onboarding processing
# ----------------------------------------------------
set -euo pipefail

# ----------------------------------------------------
# 1️⃣ Load .env (skip comment lines, export the rest)
# ----------------------------------------------------
if [[ -f .env ]]; then
  set -a                       # automatically export variables we source
  while IFS= read -r line || [[ -n "$line" ]]; do
    # Trim whitespace
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    # Skip empty lines / comments
    [[ -z "$line" || "${line:0:1}" == "#" ]] && continue
    export "$line"
  done < .env
  set +a
fi

# ----------------------------------------------------
# 2️⃣ Basic‑Auth credentials (must match docker‑compose.yml)
# ----------------------------------------------------
N8N_USER="${N8N_BASIC_AUTH_USER:-admin}"
N8N_PASS="${N8N_BASIC_AUTH_PASSWORD:-admin123}"

# ----------------------------------------------------
# 3️⃣ Build the *production* webhook URLs
#    (n8n always expects the extra `/webhook` segment)
# ----------------------------------------------------
WEBHOOK_BASE="${WEBHOOK_BASE_URL}"                # e.g. http://localhost:5678
WEBHOOK_DEMO="${WEBHOOK_BASE}/webhook/webhook-demo"
WEBHOOK_ONBOARD="${WEBHOOK_BASE}/webhook/webhook-onboard"

# Show what we will call – useful for debugging
echo "🔗 Using webhook URLs:"
echo "   Demo → $WEBHOOK_DEMO"
echo "   Onboard → $WEBHOOK_ONBOARD"
echo ""

# ----------------------------------------------------
# 4️⃣ Demo → v1
# ----------------------------------------------------
echo "=== Demo → v1 (POST to $WEBHOOK_DEMO) ==="
for demo_path in data/demo/*.txt; do
  account_id=$(basename "$demo_path" .txt)   # e.g. demo_001
  echo "🔹 $account_id → $demo_path"
  curl -u "${N8N_USER}:${N8N_PASS}" -X POST "$WEBHOOK_DEMO" \
    -H "Content-Type: application/json" \
    -d "{\"account_id\":\"$account_id\",\"transcript_path\":\"$demo_path\"}"
  echo   # blank line for readability
done

# ----------------------------------------------------
# 5️⃣ Onboarding → v2
# ----------------------------------------------------
echo "=== Onboarding → v2 (POST to $WEBHOOK_ONBOARD) ==="
for onboard_path in data/onboard/*.txt; do
  base=$(basename "$onboard_path" .txt)              # e.g. onboard_001
  # Align onboarding id with the demo id (demo_001)
  account_id="demo_${base#onboard_}"
  echo "🔹 $account_id → $onboard_path"
  curl -u "${N8N_USER}:${N8N_PASS}" -X POST "$WEBHOOK_ONBOARD" \
    -H "Content-Type: application/json" \
    -d "{\"account_id\":\"$account_id\",\"onboard_path\":\"$onboard_path\"}"
  echo
done

echo "✅ Finished – inspect ./outputs/ for v1 & v2 results."
