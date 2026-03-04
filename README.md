# Clara AI – Zero‑Cost Automation Pipeline

*Demo of a fully‑automated, free‑tier pipeline that turns demo‑call recordings (or transcripts) into a preliminary Retell‑Agent config, then updates it with onboarding data.*

## TL;DR

1. **Run n8n** (`docker‑compose up -d`) – it orchestrates the whole flow.  
2. **Drop your demo/onboarding files** into `data/demo/` and `data/onboard/`.  
3. **Execute the batch script** (`./run_all.sh`).  
4. **Check `outputs/`** – you’ll see a `v1` and `v2` folder for each account, plus a `changes.md`.  

More details below → **Setup → Usage → Architecture** (fill in later).

