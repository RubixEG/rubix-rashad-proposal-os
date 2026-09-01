# assets/ — brand & template asset policy

This wrapper intentionally ships **no loose templates, icons, or fonts** here, because in
Rashad OS those are governed inside the hash-locked tree and must never be forked:

| Asset class | Governed location (inside `../references/Rashad_OS/`) |
|---|---|
| Design tokens & deck rules | `Rashad/Skill/01_ACTIVE_RUNTIME/BRAND/DESIGN_TOKENS.md`, `BRAND/DECK_AUTHORITY.md` |
| Verified visual assets | `Rashad/Skill/01_ACTIVE_RUNTIME/BRAND/VERIFIED_ASSETS/` |
| Current brand knowledge | `Rashad/Skill/08_BRAND_CURRENT/` |
| Canonical proposal skeletons (AR/EN) | `Rashad/Skill/02_IMMUTABLE_AUTHORITIES/FINAL_CANONICAL_PROPOSAL_SKELETON_{AR,EN}.md` |

**Approved brand fonts are an external prerequisite** (see `Rashad/OS_STATUS.json`). They are
licensed binaries and are deliberately not committed to this repository. Install them on the
production render host; per OS law, production **blocks** when they are absent — silent
fallback fonts are forbidden.

If the firm later approves committing font binaries or engagement templates, place them here
in subfolders (`assets/fonts/`, `assets/templates/`) and register them through
`CORPUS_MAINTENANCE` — never by editing the hash-locked tree directly.
