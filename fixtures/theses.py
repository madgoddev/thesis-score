"""Canonical ThesisScore fixtures and fingerprint helper."""

from __future__ import annotations

import hashlib
import json

POLICY_VERSION = 1
REGISTRATION_DATETIME = "2026-08-12T10:00:00Z"
AUDIT_DATETIME = "2026-08-12T10:20:00Z"
REGISTERED_AT_UNIX = 1_786_528_800
DEADLINE_UNIX = 1_786_529_400
THESIS_KEY = "MACRO-THESIS"
TITLE = "Three-clause macroeconomic forecast for the registered evidence window."
SCORING_POLICY = (
    "A clause is satisfied only when the registered evidence explicitly meets its "
    "stated threshold by the deadline. Otherwise it is failed, or indeterminate "
    "when the supplied evidence cannot safely decide it."
)
CLAUSES = [
    {
        "clause_id": "INFLATION",
        "prediction": "Headline inflation will be below three percent by the deadline.",
        "weight_bps": 4_000,
    },
    {
        "clause_id": "JOBS",
        "prediction": "The unemployment rate will remain below five percent at the deadline.",
        "weight_bps": 2_500,
    },
    {
        "clause_id": "RATE-CUT",
        "prediction": "The central bank will announce at least one policy rate cut by the deadline.",
        "weight_bps": 3_500,
    },
]
CLAUSES_JSON = json.dumps(CLAUSES, separators=(",", ":"))
EVIDENCE_TEXT = (
    "At the registered deadline the official release reports headline inflation 2.8 "
    "percent and unemployment 5.4 percent. The official decision record reports a "
    "policy rate cut before the deadline."
)
SCORED_RESPONSE = {
    "satisfied_clause_ids": ["INFLATION", "RATE-CUT"],
    "failed_clause_ids": ["JOBS"],
    "indeterminate_clause_ids": [],
    "issue_codes": [],
}


def canonical_json(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def build_fingerprint(
    creator: str,
    *,
    policy_version: int = POLICY_VERSION,
    thesis_key: str = THESIS_KEY,
    title: str = TITLE,
    deadline_unix: int = DEADLINE_UNIX,
    scoring_policy: str = SCORING_POLICY,
    clauses=CLAUSES,
    evidence_text: str = EVIDENCE_TEXT,
) -> str:
    key = thesis_key.strip().upper()
    normalized_clauses = sorted(clauses, key=lambda item: item["clause_id"])
    binding = {
        "schema": "thesisscore/fingerprint/v1",
        "policy_version": policy_version,
        "thesis_id": f"{creator.lower()}:{key}",
        "creator": creator.lower(),
        "thesis_key": key,
        "title": title.strip(),
        "deadline_unix": deadline_unix,
        "scoring_policy": scoring_policy.strip(),
        "clauses": normalized_clauses,
        "evidence_text": evidence_text.strip(),
    }
    return "sha256:" + hashlib.sha256(canonical_json(binding).encode("ascii")).hexdigest()

