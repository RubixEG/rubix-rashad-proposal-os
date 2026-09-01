# Rashad Proposal OS — Claude Code plugin

Rubix Consulting's governed RFP-to-proposal operating system, packaged as an installable
Claude Code plugin.

## Install

```bash
/plugin marketplace add RubixEG/rubix-rashad-proposal-os
/plugin install rashad-proposal-os@rubix-plugins
```

Then verify the corpus actually loaded on this machine — do this once per host:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bridge/rashad_bridge.py" boot
python3 "${CLAUDE_PLUGIN_ROOT}/bridge/selftest.py"
```

`boot` must print `"status": "PASS"` with both ledgers at `599/599` and `69/69` and
`vocabulary_drift: ALIGNED`. `selftest` must end in
`PASS — corpus gate accepts bridge-built masters on this host`. If either fails, stop and
fix it before producing anything client-facing.

## Use

```
/rfp-summary ~/tenders/PR-IC-2026-037 as pptx
```

Or just describe the work — the skill's trigger lexicon fires on RFP, tender, bid, proposal,
كراسة الشروط, ملخص الطرح, مناقصة, معايير التقييم, Etimad, go/no-go and friends, in Arabic or
English, without anyone naming the skill.

## What is in here

| Path | What it is |
|---|---|
| `.claude-plugin/marketplace.json` | Marketplace manifest — makes this repo installable |
| `plugins/rashad-proposal-os/.claude-plugin/plugin.json` | Plugin manifest |
| `plugins/rashad-proposal-os/skills/rashad-proposal-os/` | The skill: `SKILL.md`, the hash-locked corpus archive, the governance scripts |
| `plugins/rashad-proposal-os/commands/rfp-summary.md` | `/rfp-summary` slash command |
| `plugins/rashad-proposal-os/bridge/` | **The runtime bridge** — see below |

The 1692-file authority corpus ships as one nested archive,
`skills/rashad-proposal-os/references/Rashad_OS.tar.gz` (2.1 MB), to stay under host
file-count limits. `scripts/bootstrap_corpus.py` unpacks it to a sha-keyed workspace and
verifies both SHA-256 ledgers. The archive is byte-identical to the certified tree.

## Why the bridge exists

The corpus ships executable production and QA runtimes. Before this plugin, a host would read
the authorities and then write *its own* composer, *its own* geometry detectors and *its own*
handoff guard. The resulting deck was measured — but against that host's contract, not the
OS's. Two hosts, two different decks, two incomparable QA reports.

The corpus's verifiers are **hash- and vocabulary-bound** to `brain/production/composer.py`.
A master composed with a private attribute scheme scores `measured_object_count = 0` and the
corpus gate answers:

```
SEMANTIC_MASTER_INSTRUMENTATION_MISSING: data-page-id
SEMANTIC_MASTER_INSTRUMENTATION_MISSING: data-page-mode
SEMANTIC_MASTER_INSTRUMENTATION_MISSING: data-region-id
SEMANTIC_MASTER_SPEC_HASH_BINDING_MISMATCH
SEMANTIC_MASTER_CONTENT_BEARING_FLOOR_NOT_MET
…
```

That failure is invisible unless someone actually runs the gate. The bridge runs it.

### Two tiers, and the law about the boundary

**Tier 1 — deterministic, always executable, mandatory.**

| Bridge command | Corpus runtime executed |
|---|---|
| `gate-masters` | `brain/semantic_master_gate.inspect_semantic_html_master` |
| `gate-artifact` | `brain/product_geometry.inspect_artifact` |
| `gate-binding` | `production/projector.verify_projection_media_binding` |

**Tier 2 — needs a cognition provider.** `brain/delivery_gate` demands per-page expert and
council execution ledgers. `brain/execution_mode` resolves to `OFFLINE_VALIDATION_MODE`
unless the host injects `host_invoke_fn` or `OPENAI_API_KEY` **and** `OPENAI_RASHAD_MODEL`
are both set — and in that mode every council invocation returns `NOT_EXECUTED`.

> Three QA states exist: `PASS`, `FAIL`, `NOT_EXECUTED`. The bridge never promotes the third
> to the first. Fabricating a ledger or stubbing a provider to make a gate pass is a
> governance breach, not a workaround.

### The certificate

`certify` writes a `RASHAD_BRIDGE_EXECUTION_CERTIFICATE_V1` recording, per gate: the corpus
module, its **source SHA-256**, the function invoked, the verdict, and the blockers. Verdicts:

| Verdict | Meaning |
|---|---|
| `CERTIFIED_FOR_HANDOFF` | Every gate executed and passed |
| `TIER1_CERTIFIED_TIER2_NOT_EXECUTED` | Measured against the delivered bytes; council layer did not run — say so to the owner |
| `TIER1_INCOMPLETE` | A mandatory gate did not run; no complete product evidence |
| `BLOCK_PRODUCTION` | A mandatory gate failed; do not deliver |

## Bridge CLI

```bash
B="${CLAUDE_PLUGIN_ROOT}/bridge/rashad_bridge.py"

python3 $B boot                                  # unpack, verify ledgers, vocabulary drift check
python3 $B execution-mode                        # declare cognition mode honestly
python3 $B scaffold-spec --page-id p07 --family MATRIX --dominant-form TABLE --out specs/p07.json
python3 $B gate-masters  --masters masters.json
python3 $B gate-artifact --artifact deck.pptx --masters masters.json
python3 $B gate-binding  --artifact deck.pptx --renders renders.json
python3 $B gate-delivery --artifact deck.pptx --dossier dossier.json
python3 $B certify       --artifact deck.pptx --masters masters.json --renders renders.json --out cert.json
```

`masters.json`

```json
[{"page_id": "p01",
  "html_master_path": "out/p01.html",
  "composition_spec_path": "specs/p01.json"}]
```

`renders.json` — the SHA-256 of each certified page render, in slide order.

## Requirements

Python 3.10+. `jsonschema` for the corpus's own state validator; `python-pptx` and `Pillow`
for artifact inspection; Playwright/Chromium if you render pages on this host. The bridge
degrades honestly: a module it cannot import is reported `NOT_EXECUTED` with the import error,
never silently skipped.

## Enabling Tier 2

```bash
export OPENAI_API_KEY=…
export OPENAI_RASHAD_MODEL=…
# or, when the host can inject a callback:
export RASHAD_EXECUTION_MODE=HOST
```

Re-run `execution-mode` to confirm, then `gate-delivery`.

## Licence

Proprietary — Rubix Consulting. Not for redistribution.
