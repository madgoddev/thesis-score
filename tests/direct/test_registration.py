"""ThesisScore registration tests."""

from __future__ import annotations

import json

import pytest

from fixtures.theses import (
    CLAUSES,
    CLAUSES_JSON,
    DEADLINE_UNIX,
    EVIDENCE_TEXT,
    POLICY_VERSION,
    REGISTERED_AT_UNIX,
    REGISTRATION_DATETIME,
    SCORING_POLICY,
    THESIS_KEY,
    TITLE,
    build_fingerprint,
)
from tests.conftest import CONTRACT_PATH, DIRECT_SDK_VERSION


def register(contract, **overrides):
    values = {
        "thesis_key": THESIS_KEY,
        "title": TITLE,
        "deadline_unix": DEADLINE_UNIX,
        "scoring_policy": SCORING_POLICY,
        "clauses_json": CLAUSES_JSON,
        "evidence_text": EVIDENCE_TEXT,
    }
    values.update(overrides)
    return contract.register_thesis(**values)


def test_policy_and_constructor(thesisscore, direct_alice):
    policy = thesisscore.get_policy()
    assert policy["owner"].lower() == f"0x{bytes(direct_alice).hex()}"
    assert policy["policy_version"] == POLICY_VERSION
    assert policy["total_weight_bps"] == 10_000
    assert policy["registration_before_deadline_required"] is True
    assert policy["score_derived_deterministically"] is True


def test_zero_policy_rejected(direct_vm, direct_deploy, direct_alice):
    direct_vm.sender = direct_alice
    with direct_vm.expect_revert("invalid_policy_version"):
        direct_deploy(str(CONTRACT_PATH), 0, sdk_version=DIRECT_SDK_VERSION)


def test_register_sort_fingerprint_and_time(thesisscore, direct_alice):
    thesis_id = register(thesisscore)
    thesis = thesisscore.get_thesis(thesis_id)
    creator = f"0x{bytes(direct_alice).hex()}"
    assert thesis_id == f"{creator}:{THESIS_KEY}"
    assert thesis["thesis_fingerprint"] == build_fingerprint(creator)
    assert thesis["registered_at"] == REGISTRATION_DATETIME
    assert thesis["registered_at_unix"] == REGISTERED_AT_UNIX
    assert [item["clause_id"] for item in thesis["clauses"]] == [
        "INFLATION",
        "JOBS",
        "RATE-CUT",
    ]


def test_clause_order_and_whitespace_are_idempotent(thesisscore):
    first = register(thesisscore)
    reordered = list(reversed(CLAUSES))
    second = register(
        thesisscore,
        thesis_key=f" {THESIS_KEY.lower()} ",
        clauses_json=json.dumps(reordered, indent=2),
    )
    assert first == second
    assert thesisscore.get_thesis_count() == 1


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("title", TITLE + " Changed."),
        ("deadline_unix", DEADLINE_UNIX + 1),
        ("scoring_policy", SCORING_POLICY + " Changed."),
        ("evidence_text", EVIDENCE_TEXT + " Changed."),
    ],
)
def test_same_key_changed_core_rejected(thesisscore, direct_vm, field, value):
    register(thesisscore)
    with direct_vm.expect_revert("thesis_registration_conflict"):
        register(thesisscore, **{field: value})


def test_creator_scoped_ids(thesisscore, direct_vm, direct_bob):
    first = register(thesisscore)
    direct_vm.sender = direct_bob
    second = register(thesisscore)
    assert first != second


@pytest.mark.parametrize(
    ("clauses", "message"),
    [
        ([], "invalid_clause_count"),
        (CLAUSES[:1], "invalid_clause_count"),
        (CLAUSES + [CLAUSES[0]], "duplicate_clause_id"),
        ([{**CLAUSES[0], "weight_bps": 3999}, CLAUSES[1], CLAUSES[2]], "weights_must_sum_to_10000"),
        ([{**CLAUSES[0], "weight_bps": True}, CLAUSES[1], CLAUSES[2]], "invalid_clause"),
        ([{**CLAUSES[0], "extra": 1}, CLAUSES[1], CLAUSES[2]], "invalid_clause"),
        ([{**CLAUSES[0], "prediction": "short"}, CLAUSES[1], CLAUSES[2]], "invalid_prediction"),
    ],
)
def test_invalid_clause_sets_rejected(thesisscore, direct_vm, clauses, message):
    with direct_vm.expect_revert(message):
        register(thesisscore, clauses_json=json.dumps(clauses))


def test_duplicate_json_key_and_malformed_json_rejected(thesisscore, direct_vm):
    duplicate = '[{"clause_id":"A","clause_id":"B","prediction":"A prediction long enough for the contract.","weight_bps":5000},{"clause_id":"C","prediction":"Another prediction long enough for the contract.","weight_bps":5000}]'
    with direct_vm.expect_revert("invalid_clauses_json"):
        register(thesisscore, clauses_json=duplicate)
    with direct_vm.expect_revert("invalid_clauses_json"):
        register(thesisscore, clauses_json="not json")


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"thesis_key": "BAD KEY"}, "invalid_thesis_key"),
        ({"title": "short"}, "invalid_title"),
        ({"deadline_unix": REGISTERED_AT_UNIX}, "deadline_must_be_future_at_registration"),
        ({"deadline_unix": 4_102_444_801}, "invalid_deadline_unix"),
        ({"scoring_policy": "short"}, "invalid_scoring_policy"),
        ({"evidence_text": "short"}, "invalid_evidence_text"),
    ],
)
def test_invalid_registration_rejected(thesisscore, direct_vm, overrides, message):
    with direct_vm.expect_revert(message):
        register(thesisscore, **overrides)


def test_fractional_transaction_time_canonicalized(thesisscore, direct_vm):
    direct_vm.warp("2026-08-12T10:00:00.123456Z")
    thesis_id = register(thesisscore, thesis_key="FRACTIONAL-TIME")
    thesis = thesisscore.get_thesis(thesis_id)
    assert thesis["registered_at"] == REGISTRATION_DATETIME
    assert thesis["registered_at_unix"] == REGISTERED_AT_UNIX

