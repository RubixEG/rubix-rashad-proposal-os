#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rashad Proposal OS — Authority Preflight launcher (skill-wrapper utility).

Locates the packaged executable ledger tool

    references/Rashad_OS/Rashad/Brain/runtime/brain/authority_preflight.py

sets RASHAD_SKILL_ROOT for it, and forwards all arguments verbatim. The
packaged tool is the authority; this wrapper only solves path resolution so it
can be launched identically from any working directory.

Forwarded commands (see the packaged tool's --help):
  --init <PRODUCT> [engagement]   open the Authority Load Ledger (FIRST action)
                                  PRODUCT ∈ RFP_SUMMARY_ARTIFACT |
                                            PROPOSAL_SECTION_ARTIFACT |
                                            ADVISORY_ANSWER | CORPUS_MAINTENANCE
  --status                        coverage summary (emit this line to the owner)
  --list-unattested               what still blocks production
  --attest <rel_path> <binding> <governs>
  --gate <STAGE>                  PASS | BLOCK_PRODUCTION   (exit 2 on block)

The ledger is written to $RASHAD_LEDGER_DIR, defaulting to ./.rashad in the
current working directory — run from your engagement workspace.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys


def find_os_root() -> pathlib.Path:
    env = os.environ.get("RASHAD_OS_ROOT")
    candidates = [pathlib.Path(env)] if env else []
    here = pathlib.Path(__file__).resolve()
    candidates.append(here.parent.parent / "references" / "Rashad_OS")
    for p in here.parents:
        candidates.append(p / "references" / "Rashad_OS")
        candidates.append(p / "Rashad_OS")
    for c in candidates:
        if (c / "Rashad" / "Skill" / "ACTIVE_AUTHORITY_MANIFEST.json").exists():
            return c.resolve()
    sys.stderr.write("ERROR: could not locate Rashad_OS root. Set RASHAD_OS_ROOT.\n")
    sys.exit(2)


def main() -> int:
    os_root = find_os_root()
    tool = os_root / "Rashad" / "Brain" / "runtime" / "brain" / "authority_preflight.py"
    if not tool.exists():
        sys.stderr.write(f"ERROR: packaged preflight tool not found at {tool}\n")
        return 2

    env = dict(os.environ)
    env.setdefault("RASHAD_SKILL_ROOT", str(os_root / "Rashad" / "Skill"))
    # Ledger location: keep the packaged default (CWD/.rashad) unless overridden.
    env.setdefault("RASHAD_LEDGER_DIR", str(pathlib.Path.cwd() / ".rashad"))

    proc = subprocess.run([sys.executable, str(tool), *sys.argv[1:]], env=env)
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
