# Handoff

Local audit and finalized StudioNet and Bradbury deployment/smoke evidence are complete. Addresses are `0xD0Ad6e6d0B18A950eE211F79e1C8dc99C2766d03` and `0x694467f2BD659A0cd50Ca45Af1B47100790098f4`; both deployed source hashes match the frozen contract.

Use project-local `pnpm run deploy`, prefix `THESISSCORE_`, and explicitly set/verify the network. Operations are `deploy-finalized`, `submit-bradbury`, `smoke-studionet`, and `smoke-bradbury`; smoke requires `THESISSCORE_CONTRACT_ADDRESS`. The smoke registers a short future deadline, waits through finalized registration and the deadline, then scores and verifies 7,500 bps plus exact/altered gates. Never store credentials.

Do not resubmit either deployment or immutable smoke. `THESISSCORE_SMOKE_RESUME=1` is a Bradbury-only recovery switch: it must be used only after independently confirming the exact finalized registration, and the helper revalidates that stored fixture before it can skip registration. Treat this repository, its deployment records, and the linked explorer state as the release evidence.
