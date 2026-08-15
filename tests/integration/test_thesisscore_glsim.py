"""Five-validator GLSim tests for ThesisScore."""

from __future__ import annotations

import json
from pathlib import Path

from gltest import get_contract_factory, get_validator_factory
from gltest.assertions import tx_execution_failed, tx_execution_succeeded
from gltest.types import TransactionStatus
from gltest.utils import extract_contract_address

from fixtures.theses import (
    AUDIT_DATETIME,
    CLAUSES_JSON,
    DEADLINE_UNIX,
    EVIDENCE_TEXT,
    POLICY_VERSION,
    REGISTRATION_DATETIME,
    SCORED_RESPONSE,
    SCORING_POLICY,
    THESIS_KEY,
    TITLE,
)

PROMPT_KEY = "independent multi-clause forecast scorer"


def context(response, when=AUDIT_DATETIME):
    validators = get_validator_factory().batch_create_mock_validators(
        5, mock_llm_response={"nondet_exec_prompt": {PROMPT_KEY: json.dumps(response)}}
    )
    return {
        "validators": [validator.to_dict() for validator in validators],
        "genvm_datetime": when,
    }


def deploy():
    path = Path(__file__).resolve().parents[2] / "contracts" / "thesis_score.py"
    factory = get_contract_factory(contract_file_path=path)
    receipt = factory.deploy_contract_tx(
        args=[POLICY_VERSION], wait_transaction_status=TransactionStatus.FINALIZED
    )
    assert tx_execution_succeeded(receipt)
    return factory.build_contract(extract_contract_address(receipt))


def register(contract, key=THESIS_KEY):
    receipt = contract.register_thesis(
        args=[key, TITLE, DEADLINE_UNIX, SCORING_POLICY, CLAUSES_JSON, EVIDENCE_TEXT]
    ).transact(
        transaction_context={"genvm_datetime": REGISTRATION_DATETIME},
        wait_transaction_status=TransactionStatus.FINALIZED,
    )
    assert tx_execution_succeeded(receipt)
    return contract.get_thesis_id(args=[0]).call()


def score(contract, thesis_id, response, when=AUDIT_DATETIME):
    return contract.score_thesis(args=[thesis_id]).transact(
        transaction_context=context(response, when),
        wait_transaction_status=TransactionStatus.FINALIZED,
    )


def test_glsim_complete_score_and_gate():
    contract = deploy()
    thesis_id = register(contract)
    assert tx_execution_succeeded(score(contract, thesis_id, SCORED_RESPONSE))
    thesis = contract.get_thesis(args=[thesis_id]).call()
    audit = contract.get_audit(args=[thesis_id]).call()
    assert audit["score_bps"] == 7_500
    assert contract.matches_complete_score(
        args=[thesis_id, thesis["thesis_fingerprint"], 7_500]
    ).call() is True


def test_glsim_partial_score():
    contract = deploy()
    thesis_id = register(contract, "PARTIAL")
    response = {
        "satisfied_clause_ids": ["INFLATION"],
        "failed_clause_ids": ["JOBS"],
        "indeterminate_clause_ids": ["RATE-CUT"],
        "issue_codes": ["INSUFFICIENT_EVIDENCE"],
    }
    assert tx_execution_succeeded(score(contract, thesis_id, response))
    assert contract.get_audit(args=[thesis_id]).call()["status"] == "PARTIAL"


def test_glsim_early_score_fails_before_nondeterminism():
    contract = deploy()
    thesis_id = register(contract)
    receipt = score(contract, thesis_id, SCORED_RESPONSE, REGISTRATION_DATETIME)
    assert tx_execution_failed(receipt)
    assert contract.is_scored(args=[thesis_id]).call() is False


def test_glsim_malformed_fails_without_state():
    contract = deploy()
    thesis_id = register(contract)
    malformed = {**SCORED_RESPONSE, "satisfied_clause_ids": ["UNKNOWN"]}
    assert tx_execution_failed(score(contract, thesis_id, malformed))
    assert contract.is_scored(args=[thesis_id]).call() is False
