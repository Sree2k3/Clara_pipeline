#!/usr/bin/env python3
import re
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, Field, ValidationError


# ----------------------------------------------------
# 1️⃣  Define the schema (Pydantic will validate & give us defaults)
# ----------------------------------------------------
class BusinessHours(BaseModel):
    days: List[str] = Field(default_factory=list)  # e.g. ["Mon","Tue","Wed"]
    start: str = ""  # e.g. "08:00"
    end: str = ""  # e.g. "17:00"
    timezone: str = ""  # e.g. "America/New_York"


class AccountMemo(BaseModel):
    account_id: str
    company_name: str = ""
    business_hours: BusinessHours = BusinessHours()
    office_address: str = ""
    services_supported: List[str] = Field(default_factory=list)
    emergency_definition: List[str] = Field(default_factory=list)
    emergency_routing_rules: List[Dict[str, Any]] = Field(default_factory=list)
    non_emergency_routing_rules: List[Dict[str, Any]] = Field(default_factory=list)
    call_transfer_rules: List[Dict[str, Any]] = Field(default_factory=list)
    integration_constraints: List[str] = Field(default_factory=list)
    after_hours_flow_summary: str = ""
    office_hours_flow_summary: str = ""
    questions_or_unknowns: List[str] = Field(default_factory=list)
    notes: str = ""


# ----------------------------------------------------
# 2️⃣  Helper regexes – adjust/extend as you see the real data
# ----------------------------------------------------
PATTERNS = {
    "company_name": re.compile(
        r"(?:company|business|organization)\s*[:\-]?\s*([A-Za-z0-9 &]+)", re.I
    ),
    "office_address": re.compile(r"address\s*[:\-]?\s*(.+)", re.I),
    "services_supported": re.compile(r"services?\s*[:\-]?\s*(.+)", re.I),
    "emergency_definition": re.compile(r"emergency\s*[:\-]?\s*(.+)", re.I),
    "integration_constraints": re.compile(r"constraint[s]?\s*[:\-]?\s*(.+)", re.I),
    # Business hours – e.g. "Mon‑Fri 8 am‑5 pm PST"
    "business_hours": re.compile(
        r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)[\s,\-–to]+(?:\s*(Mon|Tue|Wed|Thu|Fri|Sat|Sun))*\s*([0-9]{1,2}[:\.]?[0-9]{0,2}\s*(am|pm)?)\s*[-–]\s*([0-9]{1,2}[:\.]?[0-9]{0,2}\s*(am|pm)?)\s*([A-Z]{2,4})?",
        re.I,
    ),
}


def _find_match(pattern: re.Pattern, text: str) -> str | None:
    m = pattern.search(text)
    return m.group(1).strip() if m else None


def extract_from_transcript(text: str, account_id: str) -> AccountMemo:
    # Lower‑case version for simple contains checks
    lowered = text.lower()

    # Helper to capture missing items
    unknowns = []

    # 1️⃣ Company name
    company = _find_match(PATTERNS["company_name"], text) or ""
    if not company:
        unknowns.append("company_name")

    # 2️⃣ Office address
    address = _find_match(PATTERNS["office_address"], text) or ""
    if not address:
        unknowns.append("office_address")

    # 3️⃣ Services supported – split by comma/and/or
    services_raw = _find_match(PATTERNS["services_supported"], text) or ""
    services = [s.strip() for s in re.split(r",|and|/|;", services_raw) if s.strip()]
    if not services:
        unknowns.append("services_supported")

    # 4️⃣ Emergency definition
    emergency_raw = _find_match(PATTERNS["emergency_definition"], text) or ""
    emergency = [e.strip() for e in re.split(r",|and|/|;", emergency_raw) if e.strip()]
    if not emergency:
        unknowns.append("emergency_definition")

    # 5️⃣ Integration constraints
    constraints_raw = _find_match(PATTERNS["integration_constraints"], text) or ""
    constraints = [
        c.strip() for c in re.split(r",|and|/|;", constraints_raw) if c.strip()
    ]
    if not constraints:
        unknowns.append("integration_constraints")

    # 6️⃣ Business hours – this is a *best‑effort* extraction
    bh_match = PATTERNS["business_hours"].search(text)
    bh = {}
    if bh_match:
        days = [
            d.title()
            for d in re.findall(r"(Mon|Tue|Wed|Thu|Fri|Sat|Sun)", bh_match.group(0))
        ]
        start_time = bh_match.group(3)
        end_time = bh_match.group(5)
        tz = bh_match.group(7) if bh_match.lastindex >= 7 else ""
        bh = {"days": days, "start": start_time, "end": end_time, "timezone": tz}
    else:
        unknowns.append("business_hours")

    # Build the memo
    memo = AccountMemo(
        account_id=account_id,
        company_name=company,
        office_address=address,
        services_supported=services,
        emergency_definition=emergency,
        integration_constraints=constraints,
        business_hours=BusinessHours(**bh) if bh else BusinessHours(),
        questions_or_unknowns=unknowns,
        notes="Extracted by rule‑based parser (no LLM).",
    )
    return memo


# ----------------------------------------------------
# CLI entry point (used by n8n)
# ----------------------------------------------------
def main():
    if len(sys.argv) != 3:
        print("Usage: extract_memo.py <transcript.txt> <account_id>")
        sys.exit(1)

    transcript_path = Path(sys.argv[1])
    account_id = sys.argv[2]

    text = transcript_path.read_text(encoding="utf-8")
    memo = extract_from_transcript(text, account_id)

    # Validate & pretty‑print JSON
    try:
        json_out = memo.model_dump(exclude_none=True, by_alias=True)
        print(json.dumps(json_out, indent=2))
    except ValidationError as e:
        print("❌ Validation error:", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
