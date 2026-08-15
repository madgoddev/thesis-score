"""ThesisScore validator tests."""

from __future__ import annotations

import json

import pytest

from fixtures.theses import AUDIT_DATETIME, SCORED_RESPONSE
from tests.direct.test_registration import register

LLM_PATTERN = r"independent multi-clause forecast scorer"


def capture(thesisscore, direct_vm):
    thesis_id = register(thesisscore)
    direct_vm.warp(AUDIT_DATETIME)
    direct_vm.mock_llm(LLM_PATTERN, json.dumps(SCORED_RESPONSE))
    thesisscore.score_thesis(thesis_id)
    return direct_vm._captured_validators[-1][0]


def test_validator_repeats_partition(thesisscore, direct_vm):
    leader = capture(thesisscore, direct_vm)
    assert direct_vm.run_validator(leader_result=leader) is True
    direct_vm.clear_mocks()
    changed = dict(SCORED_RESPONSE)
    changed["satisfied_clause_ids"] = ["INFLATION"]
    changed["failed_clause_ids"] = ["JOBS", "RATE-CUT"]
    direct_vm.mock_llm(LLM_PATTERN, json.dumps(changed))
    assert direct_vm.run_validator(leader_result=leader) is False


@pytest.mark.parametrize(
    "tampered",
    [
        {},
        {"satisfied_mask": 5, "failed_mask": 2, "indeterminate_mask": 0},
        {"satisfied_mask": False, "failed_mask": 2, "indeterminate_mask": 0, "issue_mask": 0},
        {"satisfied_mask": 5, "failed_mask": 2, "indeterminate_mask": 0, "issue_mask": 1},
        {"satisfied_mask": 5, "failed_mask": 3, "indeterminate_mask": 0, "issue_mask": 0},
        {"satisfied_mask": 1, "failed_mask": 2, "indeterminate_mask": 0, "issue_mask": 0},
        {"satisfied_mask": 5, "failed_mask": 2, "indeterminate_mask": 0, "issue_mask": 0, "extra": 0},
    ],
)
def test_validator_rejects_tampering(thesisscore, direct_vm, tampered):
    capture(thesisscore, direct_vm)
    assert direct_vm.run_validator(leader_result=tampered) is False


def test_validator_rejects_error(thesisscore, direct_vm):
    capture(thesisscore, direct_vm)
    assert direct_vm.run_validator(leader_error=RuntimeError("broken")) is False
