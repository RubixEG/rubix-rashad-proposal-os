# Changelog

## 7.3.3 — first plugin release

Repackages the certified Rashad Proposal OS skill as an installable Claude Code plugin, and
adds the runtime bridge.

### Added
- `.claude-plugin/marketplace.json` + `plugins/rashad-proposal-os/.claude-plugin/plugin.json`
- `/rfp-summary` slash command running §0 → §12 in the mandated order
- **Runtime bridge** (`bridge/`):
  - `rashad_bridge.py` — CLI executing the corpus's own gates: `boot`, `execution-mode`,
    `scaffold-spec`, `gate-masters`, `gate-artifact`, `gate-binding`, `gate-delivery`, `certify`
  - `spec_adapter.py` — PageCompositionSpec builder reproducing the corpus self-hash exactly
    (`sort_keys=True`, `separators=(',',':')`, `spec_sha256`/`validation` excluded from the payload)
  - `instrumentation.py` — the corpus marker vocabulary, a local fail-fast preflight, and a
    drift check that compares its constants against the live corpus gate at boot
  - `selftest.py` — builds a spec + master and proves the corpus gate returns PASS on this host
- `RASHAD_BRIDGE_EXECUTION_CERTIFICATE_V1` — per-gate record of corpus module, source SHA-256,
  function invoked, verdict and blockers
- `SKILL.md` §0.A (plugin path resolution) and §12 (runtime bridge law)

### Changed
- Nothing inside the hash-locked corpus. Both ledgers still verify 599/599 and 69/69.
  The only edits are the two additive sections in the skill wrapper's `SKILL.md`.

### Known limitations
- `OFFLINE_VALIDATION_MODE` is the default: the Python runtime cannot call its host model, so
  the Tier 2 delivery gate reports `NOT_EXECUTED` until a cognition provider is configured.
  This is declared in the certificate, never hidden.
- Slim corpus build: QA evidence fixtures, browser-render screenshots, the COMPOSER_FAMILY
  certification pack and version-pinned harnesses are not packaged. See `SLIM_VARIANT.md`.
- The corpus's own 233 QA taxonomy cases remain `SPECIFIED_NOT_IMPLEMENTED` upstream.
