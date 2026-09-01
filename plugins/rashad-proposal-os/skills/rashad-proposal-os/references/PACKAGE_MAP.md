# Rashad OS v7.3.3 — Package Map

Orientation map for the byte-identical payload.
Read this when you need to know **where something lives**; read the files themselves for
governance. `Rashad/Skill/ACTIVE_AUTHORITY_MANIFEST.json` is the only global-routing truth —
this map never overrides it.

> **In this build the payload ships as `references/Rashad_OS.tar.gz`, not as a loose tree.**
> Run SKILL.md Step 0.0 (`scripts/bootstrap_corpus.py --verify`) first; every path below is then
> relative to the `OS_ROOT` it prints (`$RASHAD_OS_ROOT`), i.e. the extracted `Rashad_OS/`
> directory. Layout, names and bytes are unchanged.

```
$RASHAD_OS_ROOT/                     (= the unpacked Rashad_OS/)
├── Rashad/
│   ├── README.md                    ← canonical layer overview (start of any audit)
│   ├── OS_STATUS.json               ← live status authority: versions, gates, known gaps
│   ├── Docs/                        ← architecture & handoff docs (HANDOFF.md, Brain architecture)
│   ├── Certification/               ← Council-of-Councils reports, certifications, Lineage/
│   ├── Skill/                       ← THE AUTHORITY SET (v7.3.x) — see below
│   └── Brain/                       ← Consulting Brain Runtime v3.5 (config/ + runtime/ Python)
└── QA/
    ├── README.md, FINAL_VERIFY.py   ← QA layer entry
    ├── Runtime/                     ← QA Runtime v4.4 (rashad_qa.py, contracts/, fixtures/, schemas/)
    ├── Brain/                       ← QA Brain v1.4.0 (14 councils)
    ├── Certification/               ← QA certification results incl. package manifest
    └── lib/
```

## `Rashad/Skill/` — the authority set

| Path | What it is / when to open |
|---|---|
| `SKILL.md` | The OS's own root skill instructions (v7.3.0 + overlays). Read at boot. |
| `PROJECT_INSTRUCTIONS.md` | 28 numbered current project laws. Read at boot. |
| `00_START_HERE.md` | Startup route + artifact-mode 13-stage pipeline. Read at boot. |
| `ACTIVE_AUTHORITY_MANIFEST.json` | Sole machine global-routing authority (74 global authorities). |
| `RETRIEVAL_EXCLUSION_REGISTRY.json` | Apply before any in-corpus keyword/semantic retrieval. |
| `GLOBAL_AUTHORITY_HASHES.json` | SHA-256 ledger of the current authority set. |
| `PROTECTED_CORPUS_HASHES.json` | SHA-256 ledger of the immutable v6.2.2 protected corpus. |
| `AUTHORITY_BINDING_CHECK.json`, `CURRENT_SKILL_STATUS.json`, `CERTIFICATION_REQUIREMENTS.json`, `V7_RELEASE_SCOPE.json`, `VERSION.md` | Binding/version/status ledgers. |
| `MANIFEST.md` | Human-readable registry mirror (large; use for lookups, not routing). |
| `00_CHAT_MIRROR_KERNEL/` | Boot authorities: `00_RASHAD_BOOTSTRAP.md`, owner policy, version-retirement ledger, kernel mirrors. |
| `01_ACTIVE_RUNTIME/` | Current execution authorities (numbered ≈00–86): councils & roles, artifact engine/orchestrators, language/RTL law (`04`), RFP ingestion (`05`), proposal skeleton (`08`), Rubix deck & brand (`13`), host-native law (`80`), composition law (`82`), **authority preflight law (`84`)**, purpose & time-to-value law (`86`); plus live registries: `rfp_summary_role_registry_v7.json` (24 roles), `council_lens_registry_v7.json`, `authority_required_sets_v7_3_3.json` (4 products), `AUTHORITY_ROUTING_REGISTRY_V7_3_2.json`, `VISUAL_PRODUCTION_RECIPE_INDEX_V7_3.json`, `BRAND/` (design tokens, deck authority, verified assets), `PROMPTS/PROMPT_INDEX.md`. |
| `02_IMMUTABLE_AUTHORITIES/` | Protected v6.2.2 corpus (hash-locked, 591 files): `FINAL_CANONICAL_PROPOSAL_SKELETON_{AR,EN}.md`, `Rashad_Prompts_Master_Document.md` (7.3 MB master), and `RETRIEVAL/` → `PROMPTS/` (388 R-codes), `SCOPES/` (96), `MAPPINGS/` (96), `R_CODE_INDEX.md`, `SCOPE_INDEX.md`, `SCOPE_TO_PROMPT_INDEX.md`. **Never edit.** |
| `03_ARTIFACT_ENGINE/` | Artifact/exhibit engine specialist authorities (182 files). |
| `04_REASONING_ENGINE/` | Evaluator-question engine, win strategy, claim–evidence, section contracts, dependency change, commercial value, assumptions/clarifications. |
| `05_WORKFLOW_ENGINE/` | 30 workflows. Current spine: `23_V7_0_1_RFP_SUMMARY_DECISION_WORKFLOW.md`, `24_V7_1_…ARTIFACT_DELIVERY…`, `25_V7_2_HOST_NATIVE_…`, `26_V7_3_COMPOSITION_TO_PRODUCTION_AND_ENGAGEMENT_ACCEPTANCE_WORKFLOW.md`; plus end-to-end, section generation, council review, bid workstreams/calendar. |
| `06_SERVICE_LINE_PLAYBOOKS/` | 18 service lines (`00_INDEX.md` → strategy, ops, digital, data/AI, cyber, finance, human capital, ESG, PPP, public sector…). |
| `07_GOVERNANCE_AND_QA/` | Total-Quality governance: 233-case failure taxonomy (`73_…FAILURE_TAXONOMY.json`), actual-pixel QA closed loop & golden acceptance (`81_…`), stress/chaos matrices, detector contracts. |
| `08_BRAND_CURRENT/` | Current brand knowledge (tokens, rules). Approved brand **fonts are an external prerequisite** — production blocks when absent. |
| `09_APPENDIX_EVIDENCE/` | Evidence appendix authorities. |
| `10_PROVENANCE/` | Provenance/lineage records (non-governing history). |
| `11_RUBIX_FIRM_KNOWLEDGE/` | Firm knowledge slots (credentials/case studies/CV/rate cards are populated per engagement from approved sources — never invented). |
| `schemas/` | 19 JSON schemas (cognitive packet, ingestion/execution state, decision evidence, delivery, pixel review…). |
| `tests/skill_certification/` | verify/red-team harnesses per version (`verify_skill_v7_3.py`, `red_team_skill_v7_3.py`, …). |

## `Rashad/Brain/` — executable consulting runtime (v3.5)

| Path | Purpose |
|---|---|
| `config/` | Brain/provider configuration (execution modes, council config). |
| `runtime/brain/` | Cognition engines: **`authority_preflight.py` (v7.3.3 ledger tool)**, coverage, concept-quality judge, execution proof… |
| `runtime/production/` | Composer → build → native_pptx → gates → repair → pack (the production organ). |
| `runtime/validation/` | Schema validator, execution dossiers, R-code reachability, route audit, proof integrity. |
| `runtime/rfp_summary_runtime.py` | Machine-gated 15-step RFP Summary decision pipeline. |
| `runtime/artifact_delivery_orchestrator.py`, `runtime/exact_artifact_handoff_guard.py` | User-visible delivery + exact-handoff enforcement. |

## `QA/` — independent QA layer

| Path | Purpose |
|---|---|
| `Runtime/rashad_qa.py`, `run_certification_v4.py`, `run_regression_v3*.py` | Format-neutral engagement-file inspection, certification & regression harnesses. |
| `Runtime/contracts/`, `schemas/`, `config/` | Detector contracts (incl. v7 failure taxonomy), QA schemas. |
| `Runtime/fixtures/` | Golden/negative baselines & incident fixtures (e.g. `I16_WRONG_ARTIFACT_HANDOFF_20260817/`). |
| `Brain/` | QA Brain v1.4.0 — 14 council supervision of engagement acceptance & repair. |
| `Certification/` | QA-side certification results + `RASHAD_OS_V7_3_2_PACKAGE_MANIFEST.json`. |

## Version pins (from `OS_STATUS.json`, certified 2026-08-17)

Skill v7.3.0 (+7.3.2 remediation candidate, +7.3.3 preflight law) · Brain v3.5.0 ·
Artifact Brain v4.0.0 · QA Runtime v4.4 · QA Brain v1.4.0 · Release authority:
`RASHAD_BRAIN_RELEASE_CHAIR` · Protected corpus: immutable v6.2.2 hash lock.

## Known remaining production requirements (do not paper over)

1. Approved brand fonts must exist on the production render host — block, never substitute.
2. Firm-specific governed knowledge packs (credentials, case studies, CV/capacity, rate cards)
   are populated per engagement from approved sources.
3. Every client deliverable needs a current-engagement Brain/SME/Council/Artifact/QA run and
   actual final-file certification.
4. `RELEASED` needs external independence + Release Chair proof beyond host-native drafting.
