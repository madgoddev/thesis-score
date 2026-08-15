# ThesisScore

ThesisScore is a standalone, frontend-free GenLayer Intelligent Contract for scoring an immutable multi-clause prediction thesis after its deadline. A thesis contains 2–8 normalized clauses whose integer weights sum to exactly 10,000 basis points, a scoring policy, deadline, and registered evidence.

Validators partition every clause exactly once into satisfied, failed, or indeterminate sets. The contract normalizes those sets to masks and derives the weighted score deterministically. `matches_complete_score(id, independently_precommitted_fingerprint, exact_score_bps)` opens only for a complete score with no indeterminate clause or issue.

It is not a prediction market, does not custody positions, does not authenticate evidence, and does not claim that a thesis is economically wise. Registration must finalize before the deadline; scoring is creator-only after the deadline; the first successful score is immutable.

## Safe integration

Pin the network, finalized address, policy version, exact clauses/weights/deadline/evidence, and independently computed fingerprint. Never fetch and echo the stored fingerprint. Use `matches_complete_score`, not `is_scored`, for downstream settlement.

## Verification

```powershell
python -m pytest -p no:cacheprovider tests/direct
& .\node_modules\.bin\tsc.cmd -p tsconfig.json
```

See `AUDIT.md`, `SECURITY.md`, and `HANDOFF.md` for the test matrix, limitations, live evidence, and deployment workflow. No frontend is included.

## Live deployments

- StudioNet: `0xD0Ad6e6d0B18A950eE211F79e1C8dc99C2766d03`
- Bradbury: `0x694467f2BD659A0cd50Ca45Af1B47100790098f4`

Both deployed sources exactly match the frozen 33,934-byte contract. Both deadline-bound smoke tests finalized with a complete 7,500-bps score, masks `5/2/0/0`, exact fingerprint gate true, and altered-fingerprint gate false. The LLM supplies only the clause partition and closed issue codes; IDs, masks, completeness, and score are contract-derived.

MIT licensed; see `LICENSE`.
