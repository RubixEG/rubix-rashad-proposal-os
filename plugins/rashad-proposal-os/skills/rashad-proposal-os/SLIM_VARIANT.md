# SLIM variant — what is and is not in this package

This is a size-reduced build of the Rashad Proposal OS v7.3.3 skill, made so it can be
uploaded as a personal skill where the full package is too large. **The governed corpus is
untouched.**

## Verified after slimming

```
PROTECTED_CORPUS_HASHES.json : PASS  (599/599)
GLOBAL_AUTHORITY_HASHES.json : PASS  (69/69)
OVERALL: PASS

Authority Preflight --init RFP_SUMMARY_ARTIFACT  ->  74/74 required authorities resolve on disk
Gate USER_VISIBLE_ARTIFACT at 0 attested         ->  BLOCK_PRODUCTION (fail-closed, as designed)
```

Nothing declared in either hash ledger was removed. The removal script treated both ledgers as a
protect-list: 8 files that sit inside otherwise-removed trees were kept precisely because they are
hash-declared.

## Removed (574 files, 45 MB -> 26 MB)

| Removed | Files | What it was |
|---|---|---|
| `QA/Certification/COMPOSER_FAMILY_V7_3_2/` | 144 | v7.3.2 composer-family certification evidence pack |
| `QA/Runtime/certification/` | 352 | browser-render certification screenshots (clean + negative cases) |
| `QA/Runtime/fixtures/` | 49 | engagement/incident fixtures, incl. the negative-baseline `.pptx` decks |
| `QA/Runtime/_probe_clean_current/`, `_parity_fixture/` | 7 | probe and parity render fixtures |
| `Rashad/Skill/tests/` | 18 | version-pinned certification + red-team harnesses (v7.0-v7.3) |
| stray `.png` / `.pptx` / `.pdf` elsewhere | 4 | undeclared render artifacts |

All of these are **test evidence and reproduction fixtures**, not authorities. No `.md` or `.json`
authority file, no Brain runtime module, and no manifest was removed.

## What this costs you

The four products — `RFP_SUMMARY_ARTIFACT`, `PROPOSAL_SECTION_ARTIFACT`, `ADVISORY_ANSWER`,
`CORPUS_MAINTENANCE` — all run normally, and every QA *law*, contract, taxonomy and checklist is
still packaged. What you cannot do from this build:

- re-run the packaged certification / red-team harnesses (`Rashad/Skill/tests/`)
- diff a new render against the packaged visual baselines
- reproduce the v7.3.2 COMPOSER_FAMILY certification run

For any of that, use the full package (the GitHub plugin `rashad-os@rubix-rashad`), which remains
the certified article of record. Do not treat this slim build as the certified package for
re-certification purposes.

## Depth reduction (2026-08-31)

Skill uploads reject archives with paths more than 10 folders deep. One tree exceeded that:

| Removed | Files | Depth | What it was |
|---|---|---|---|
| `Rashad/Brain/runtime/fixtures/proof_valid/` | 11 | 10-11 | Brain proof-of-validity page fixtures (`pages/P01/...`) |

11 KB total, none hash-declared, and none of the 74 required authorities live there. Maximum
path depth in the archive is now **8 folders**, leaving headroom if the archive is extracted
inside another folder.

---

## File-count reduction — nested corpus (2026-08-31)

Skill uploads also reject archives containing more than **200 files**. The slim tree was 1,699.

Deleting files could never solve this: the two hash ledgers *declare* 599 + 69 paths, and the
RETRIEVAL corpus alone (388 R-code prompts + 96 scopes + 96 mappings) is 580 files. Any build
that reaches 200 loose files has, by definition, broken the hash lock and forfeited
certification. So **nothing further was removed.**

Instead the corpus is now packaged as a single nested archive:

| Before | After |
|---|---|
| `references/Rashad_OS/` — 1,692 loose files | `references/Rashad_OS.tar.gz` — 1 file, 2.1 MB |
| 1,699 files in the package | **8 files in the package** |
| max path depth 8 | max path depth 2 |

### Why this preserves certification

`tar` restores bytes exactly. The archive is built deterministically (`--sort=name`,
`--owner=0 --group=0 --numeric-owner`, fixed mtime, `gzip -9n`), so the same tree always yields
the same archive SHA-256. Extraction is not editing — the preservation law applies to the
unpacked tree exactly as before, and `verify_integrity.py` re-proves the hash lock **on every
boot** rather than once at packaging time. That is strictly stronger than the loose build,
where a corrupted file could sit unnoticed until someone happened to run the verifier.

### Boot change (the only behavioural difference)

`references/Rashad_OS/` no longer exists on disk until Step 0.0 runs:

```bash
python3 "$SKILL_DIR/scripts/bootstrap_corpus.py" --verify
export RASHAD_OS_ROOT="$(python3 "$SKILL_DIR/scripts/bootstrap_corpus.py" --print-root)"
```

Extraction target is `$RASHAD_OS_HOME/<archive-sha12>/Rashad_OS` (default `~/.rashad_os`, temp
dir fallback). The sha-keyed directory means two package builds never collide and a stale tree is
never silently reused. The unpack is idempotent, so re-running at a context-resume boundary is
near-free. Both packaged scripts already honoured `$RASHAD_OS_ROOT`, so **no packaged script,
manifest, ledger, or retrieval path changed.**

### Verified after nesting

```
bootstrap_corpus.py --verify   ->  UNPACKED 1692 files
PROTECTED_CORPUS_HASHES.json   ->  PASS  (599/599)
GLOBAL_AUTHORITY_HASHES.json   ->  PASS  (69/69)
OVERALL: PASS

bootstrap_corpus.py (re-run)   ->  REUSED 1692 files  (idempotent)
verify_integrity.py --quick 40 ->  PASS  (40/40 per ledger)

preflight --init RFP_SUMMARY_ARTIFACT     ->  74/74 required authorities resolve on disk
preflight --gate USER_VISIBLE_ARTIFACT    ->  BLOCK_PRODUCTION at 0 attested (fail-closed)
```

### New host prerequisite

The OS now requires `python3` and code execution **to read anything at all**, not just to run
preflight. On a host without them, the correct behaviour is `BLOCK_PRODUCTION` — never a
model-memory answer. This is recorded in SKILL.md §8.

### Frontmatter limit (2026-08-31)

Skill uploads also cap the SKILL.md `description` field at **1024 characters**; it was 1454.

Rewritten to 1012 (12 spare). Nothing was dropped that drives routing — the cut fell on the
capability prose, which is documented at length in the body anyway. Preserved in full: the
`USE WHENEVER` trigger list (EN + AR), Etimad / اعتماد, the "trigger even when they never say
'Rashad' or 'skill'" clause, and the "this OS governs — never improvise a format or answer from
model memory" instruction. Removed as redundant: `ملخص كراسة الشروط` (covered by كراسة الشروط +
ملخص الطرح), `عرض كامل` (covered by عرض), the two Egyptian example phrases (covered by their
component terms), and the version/count detail (`Brain v3.5`, `QA Runtime v4.4`, `388 R-codes,
96 scopes, 96 mappings`, the 5-strategy artifact chain), which never triggered anything.

The layer/version table now shows paths relative to `OS_ROOT` rather than the pre-unpack
`references/Rashad_OS/`, which does not exist in this build.
