"""ThesisScore scoring and gate tests."""

from __future__ import annotations

import json

import pytest

from fixtures.theses import AUDIT_DATETIME, SCORED_RESPONSE, build_fingerprint
from tests.direct.test_registration import register

LLM_PATTERN = r"independent multi-clause forecast scorer"


def mock(direct_vm, response):
    direct_vm.mock_llm(LLM_PATTERN, json.dumps(response))


def test_deadline_blocks_early_score(thesisscore, direct_vm):
    thesis_id = register(thesisscore)
    mock(direct_vm, SCORED_RESPONSE)
    with direct_vm.expect_revert("thesis_deadline_not_reached"):
        thesisscore.score_thesis(thesis_id)
    assert direct_vm._captured_validators == []


def test_complete_score_and_gate(thesisscore, direct_vm):
    thesis_id = register(thesisscore)
    direct_vm.warp(AUDIT_DATETIME)
    mock(direct_vm, SCORED_RESPONSE)
    thesisscore.score_thesis(thesis_id)
    thesis = thesisscore.get_thesis(thesis_id)
    audit = thesisscore.get_audit(thesis_id)
    assert audit["status"] == "SCORED"
    assert audit["satisfied_mask"] == 5
    assert audit["failed_mask"] == 2
    assert audit["indeterminate_mask"] == 0
    assert audit["score_bps"] == 7_500
    assert thesisscore.matches_complete_score(
        thesis_id, thesis["thesis_fingerprint"], 7_500
    ) is True


def test_partial_score_partition(thesisscore, direct_vm):
    thesis_id = register(thesisscore, thesis_key="PARTIAL")
    direct_vm.warp(AUDIT_DATETIME)
    mock(
        direct_vm,
        {
            "satisfied_clause_ids": ["INFLATION"],
            "failed_clause_ids": ["JOBS"],
            "indeterminate_clause_ids": ["RATE-CUT"],
            "issue_codes": ["INSUFFICIENT_EVIDENCE"],
        },
    )
    thesisscore.score_thesis(thesis_id)
    audit = thesisscore.get_audit(thesis_id)
    assert audit["status"] == "PARTIAL"
    assert audit["score_bps"] == 4_000
    assert audit["issue_mask"] == 1


@pytest.mark.parametrize(
    ("code", "mask"),
    [
        ("INSUFFICIENT_EVIDENCE", 1),
        ("CONFLICTING_EVIDENCE", 2),
        ("AMBIGUOUS_CLAUSE", 4),
        ("DEADLINE_MISMATCH", 8),
        ("SOURCE_AUTHORITY_UNCLEAR", 16),
        ("ADVERSARIAL_INSTRUCTION", 32),
    ],
)
def test_each_issue_bit(thesisscore, direct_vm, code, mask):
    thesis_id = register(thesisscore, thesis_key=f"ISSUE-{mask}")
    direct_vm.warp(AUDIT_DATETIME)
    mock(
        direct_vm,
        {
            "satisfied_clause_ids": ["INFLATION", "RATE-CUT"],
            "failed_clause_ids": [],
            "indeterminate_clause_ids": ["JOBS"],
            "issue_codes": [code],
        },
    )
    thesisscore.score_thesis(thesis_id)
    assert thesisscore.get_audit(thesis_id)["issue_mask"] == mask


@pytest.mark.parametrize(
    "response",
    [
        {},
        [],
        {**SCORED_RESPONSE, "extra": 1},
        {**SCORED_RESPONSE, "satisfied_clause_ids": ["UNKNOWN"]},
        {**SCORED_RESPONSE, "failed_clause_ids": ["JOBS", "JOBS"]},
        {**SCORED_RESPONSE, "indeterminate_clause_ids": ["JOBS"]},
        {**SCORED_RESPONSE, "failed_clause_ids": []},
        {**SCORED_RESPONSE, "issue_codes": ["UNKNOWN"]},
        {"satisfied_clause_ids": ["INFLATION"], "failed_clause_ids": ["JOBS"], "indeterminate_clause_ids": ["RATE-CUT"], "issue_codes": []},
    ],
)
def test_malformed_output_no_state(thesisscore, direct_vm, response):
    thesis_id = register(thesisscore)
    direct_vm.warp(AUDIT_DATETIME)
    mock(direct_vm, response)
    with direct_vm.expect_revert("[LLM_ERROR]"):
        thesisscore.score_thesis(thesis_id)
    assert thesisscore.is_scored(thesis_id) is False


def test_creator_only_and_immutable(thesisscore, direct_vm, direct_alice, direct_bob):
    thesis_id = register(thesisscore)
    direct_vm.warp(AUDIT_DATETIME)
    direct_vm.sender = direct_bob
    mock(direct_vm, SCORED_RESPONSE)
    with direct_vm.expect_revert("only_creator_may_score"):
        thesisscore.score_thesis(thesis_id)
    direct_vm.sender = direct_alice
    thesisscore.score_thesis(thesis_id)
    with direct_vm.expect_revert("thesis_already_scored"):
        thesisscore.score_thesis(thesis_id)


def test_gate_fails_closed_on_tampering(thesisscore, direct_vm):
    thesis_id = register(thesisscore)
    direct_vm.warp(AUDIT_DATETIME)
    mock(direct_vm, SCORED_RESPONSE)
    thesisscore.score_thesis(thesis_id)
    thesis = thesisscore.get_thesis(thesis_id)
    fingerprint = thesis["thesis_fingerprint"]
    assert fingerprint == build_fingerprint(thesis["creator"])
    altered = fingerprint[:-1] + ("0" if fingerprint[-1] != "0" else "1")
    assert thesisscore.matches_complete_score(thesis_id, altered, 7_500) is False
    audit = json.loads(thesisscore.audits[thesis_id])
    audit["satisfied_mask"] = False
    thesisscore.audits[thesis_id] = json.dumps(audit, sort_keys=True, separators=(",", ":"))
    assert thesisscore.matches_complete_score(thesis_id, fingerprint, 7_500) is False

