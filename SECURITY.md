# Security and limitations

- ThesisScore evaluates frozen clauses against supplied evidence; it does not authenticate sources, guarantee exhaustive evidence, or judge investment quality.
- Weighted scoring is deterministic only after semantic clause classification, which remains susceptible to common-mode LLM error and prompt injection.
- Complete disjoint masks, exact validator equivalence, bounds, and fail-closed disagreement reduce state ambiguity but may reduce liveness.
- Registration must precede and scoring follow the deadline. Transaction time is canonicalized to whole-second UTC.
- Creator-only first scoring is immutable. New evidence/correction requires a new key or policy deployment.
- Consumers pin chain/address/policy/deadline/clauses/evidence/fingerprint and finalized state. Never fetch-and-echo; do not gate on `is_scored` alone.
- Public inputs must contain no confidential predictions, positions, or credentials.
- StudioNet and Bradbury provide separate finalized deployment and smoke evidence. This is operational evidence, not proof against common-mode model error; consumers must still enforce the exact fingerprint-bound gate.
