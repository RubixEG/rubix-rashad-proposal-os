#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rashad Proposal OS — package integrity verifier (skill-wrapper utility).

Recomputes SHA-256 for every file listed in the two authoritative hash ledgers
and compares against the packaged tree:

  Rashad/Skill/PROTECTED_CORPUS_HASHES.json   (v6.2.2 protected corpus — immutable)
  Rashad/Skill/GLOBAL_AUTHORITY_HASHES.json   (current global authority set)

Ledger format: { ..., "files": { "<path relative to Rashad/Skill>": "<sha256>" } }

Exit codes:
  0  all verified files match
  1  one or more MISMATCH / MISSING files  -> treat as VERSION_CONFLICT_BLOCK
  2  environment error (OS root or ledgers not found)

Usage:
  python3 verify_integrity.py                 # full verification (both ledgers)
  python3 verify_integrity.py --quick 40      # random spot-check of 40 files/ledger
  python3 verify_integrity.py --json          # machine-readable report
  python3 verify_integrity.py --root <path>   # explicit OS root (contains Rashad/, QA/)

OS root resolution order: --root, $RASHAD_OS_ROOT, <script>/../references/Rashad_OS.
Stdlib only. Read-only: this script never modifies the tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import random
import sys

LEDGERS = ("PROTECTED_CORPUS_HASHES.json", "GLOBAL_AUTHORITY_HASHES.json")


def find_os_root(cli_root: str | None) -> pathlib.Path:
    candidates: list[pathlib.Path] = []
    if cli_root:
        candidates.append(pathlib.Path(cli_root))
    env = os.environ.get("RASHAD_OS_ROOT")
    if env:
        candidates.append(pathlib.Path(env))
    here = pathlib.Path(__file__).resolve()
    candidates.append(here.parent.parent / "references" / "Rashad_OS")
    # Also walk upward in case the wrapper layout was moved.
    for p in here.parents:
        candidates.append(p / "references" / "Rashad_OS")
        candidates.append(p / "Rashad_OS")
    for c in candidates:
        if (c / "Rashad" / "Skill" / "ACTIVE_AUTHORITY_MANIFEST.json").exists():
            return c.resolve()
    sys.stderr.write("ERROR: could not locate Rashad_OS root "
                     "(looked for Rashad/Skill/ACTIVE_AUTHORITY_MANIFEST.json). "
                     "Pass --root or set RASHAD_OS_ROOT.\n")
    sys.exit(2)


def sha256_of(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_ledger(skill_root: pathlib.Path, ledger_name: str,
                  quick: int | None, rng: random.Random) -> dict:
    ledger_path = skill_root / ledger_name
    if not ledger_path.exists():
        return {"ledger": ledger_name, "status": "LEDGER_MISSING",
                "checked": 0, "ok": 0, "mismatch": [], "missing": []}
    data = json.loads(ledger_path.read_text(encoding="utf-8"))
    files: dict[str, str] = data.get("files", {})
    items = sorted(files.items())
    sampled = False
    if quick is not None and quick < len(items):
        items = rng.sample(items, quick)
        sampled = True

    ok = 0
    mismatch: list[str] = []
    missing: list[str] = []
    for rel, expected in items:
        p = skill_root / rel
        if not p.exists():
            missing.append(rel)
            continue
        if sha256_of(p) == expected:
            ok += 1
        else:
            mismatch.append(rel)

    status = "PASS" if not mismatch and not missing else "VERSION_CONFLICT_BLOCK"
    return {"ledger": ledger_name, "status": status, "declared": len(files),
            "checked": len(items), "sampled": sampled, "ok": ok,
            "mismatch": mismatch, "missing": missing}


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify Rashad OS package integrity.")
    ap.add_argument("--root", help="Path to Rashad_OS root (contains Rashad/ and QA/)")
    ap.add_argument("--quick", type=int, metavar="N",
                    help="Spot-check N random files per ledger instead of all")
    ap.add_argument("--json", action="store_true", help="Emit JSON report")
    ap.add_argument("--seed", type=int, default=None, help="Seed for --quick sampling")
    args = ap.parse_args()

    os_root = find_os_root(args.root)
    skill_root = os_root / "Rashad" / "Skill"
    rng = random.Random(args.seed)

    reports = [verify_ledger(skill_root, name, args.quick, rng) for name in LEDGERS]
    overall = "PASS" if all(r["status"] == "PASS" for r in reports) else "VERSION_CONFLICT_BLOCK"

    if args.json:
        print(json.dumps({"os_root": str(os_root), "overall": overall,
                          "ledgers": reports}, ensure_ascii=False, indent=1))
    else:
        print(f"Rashad OS integrity :: root={os_root}")
        for r in reports:
            mode = "quick" if r.get("sampled") else "full"
            print(f"  {r['ledger']}: {r['status']}  "
                  f"({r['ok']}/{r['checked']} ok, mode={mode}, declared={r.get('declared', 0)})")
            for rel in r["mismatch"][:20]:
                print(f"    MISMATCH {rel}")
            for rel in r["missing"][:20]:
                print(f"    MISSING  {rel}")
            hidden = max(0, len(r["mismatch"]) + len(r["missing"]) - 40)
            if hidden:
                print(f"    ... and {hidden} more problems (use --json for the full list)")
        print(f"OVERALL: {overall}")

    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
