# Audit receipt

Frozen local candidate: 33,934 bytes; SHA-256 `642C4672AA8E8A29674C50BE03822131B0CF03517EB3C05FB86332DE52DF7046`.

- GenVM lint/semantic validation: pass, 12 methods (10 view/2 write), one constructor.
- Strict typecheck: zero diagnostics.
- Direct mode: 53/53 passed.
- Five-validator GLSim: 4/4 passed.
- Deploy-helper TypeScript: zero diagnostics.

Coverage includes exact clause schema/order/weights, registration and scoring deadline boundaries, complete partitions, derived masks/score, partial results, malformed output/no state, creator authorization, stored corruption, fingerprint binding, and exact/altered gates.

## StudioNet live evidence

- Contract `0xD0Ad6e6d0B18A950eE211F79e1C8dc99C2766d03`; deployment `0xcc4289acf4aa6dd3c0bec6181016463491018bf5e8fbff09cce33382f865ac62`, FINALIZED/AGREE/FINISHED_WITH_RETURN with five agreeing deployment votes.
- Deployed source is byte-identical to the 33,934-byte frozen source and hash above.
- Registration `0xa77356eaadd6200b54bb5710e7295d910ba1ad1bdb35dcbafc626b93e0f19d7e` finalized with five agreeing votes. Score transaction `0xfe275ebb62006de27b784f6e1ab2fdc4f5f7101656c810876a68db0122a37051` finalized AGREE; the three completed validator executions agreed and two were idle after quorum cancellation.
- Final state: `SCORED`, masks `5/2/0/0`, score `7500` bps; fingerprint `sha256:e626b6ad97ca8072c39777ca052754d8f92c89d3808a84ccb7c7e8de2a4b8ee5`; exact gate true and altered gate false.

## Bradbury live evidence

- Contract `0x694467f2BD659A0cd50Ca45Af1B47100790098f4`; deployment `0xd1080e0282627b95bcc4e5e623e5f5e54b6d83088aad562e1b80df7062e66754`, FINALIZED/AGREE/FINISHED_WITH_RETURN.
- Finalized source readback is 33,934 bytes with exact SHA-256 `642C4672AA8E8A29674C50BE03822131B0CF03517EB3C05FB86332DE52DF7046` and is byte-identical to local source.
- Registration `0x6312ac5974dd6fd43f510d392b095e1407e844658cf65c607a6f8fc23e7f8dbd` and score `0xe436cb8c3d359259f69f48cc7c6fc9f0f97751ccee2394b28da825e16b61353d` are FINALIZED/AGREE/FINISHED_WITH_RETURN. The score round had four agreeing executions and one deterministic-violation vote; the overall result was AGREE.
- Final `LATEST_FINAL` state has one thesis and one audit: `SCORED`, masks `5/2/0/0`, score `7500` bps, satisfied `INFLATION` and `RATE-CUT`, failed `JOBS`, no indeterminate clause or issue.
- Thesis deadline is Unix `1786564210`; fingerprint is `sha256:8ca41e1768b7db00437522f94f3fe175df96d2ec634ec94a43000101e8e3ccf3`; exact gate true and one-nibble-altered gate false.
