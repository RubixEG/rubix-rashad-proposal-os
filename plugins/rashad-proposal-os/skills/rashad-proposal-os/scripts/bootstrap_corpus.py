#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rashad Proposal OS — corpus bootstrap (skill-wrapper utility).

This wrapper ships the governed corpus as ONE nested archive
(`references/Rashad_OS.tar.gz`, 1692 members) instead of 1692 loose files, so the
skill package stays under host file-count limits. The archive is byte-identical to
the certified tree: extraction restores exactly the bytes the two SHA-256 hash
ledgers declare, and `verify_integrity.py` re-proves that on every boot.

This script is STEP 0.0 of the mandatory startup sequence. Nothing in the OS can be
read, routed, or attested before it has run.

Behaviour
  * Extracts to  $RASHAD_OS_HOME/<archive-sha12>/Rashad_OS   (default
    $RASHAD_OS_HOME = ~/.rashad_os; falls back to the temp dir if $HOME is
    unwritable). The sha-keyed directory means two package versions never collide
    and a stale tree is never silently reused.
  * Idempotent: a completed extraction is detected via `.rashad_unpack_ok` and
    reused, so re-running mid-session costs nothing.
  * Fail-closed: refuses absolute paths, `..` traversal, symlinks, hardlinks and
    device entries in the archive; a partial extraction never gets a marker and is
    therefore never reused.
  * Prints the resolved OS root and an `export RASHAD_OS_ROOT=...` line. Both
    `verify_integrity.py` and `preflight.py` already honour $RASHAD_OS_ROOT, so no
    other packaged script or path changes.

Usage
  python3 bootstrap_corpus.py                 # unpack (or reuse) + report the root
  python3 bootstrap_corpus.py --verify        # unpack, then run the full integrity check
  python3 bootstrap_corpus.py --print-root    # resolve only, no extraction, no output noise
  python3 bootstrap_corpus.py --force         # re-extract even if a good marker exists
  python3 bootstrap_corpus.py --dest <path>   # explicit destination root

Exit codes
  0  corpus available at the reported root
  1  integrity verification failed (--verify)  -> VERSION_CONFLICT_BLOCK
  2  environment / archive error               -> stop, report to the owner, do not produce

Stdlib only. Never writes inside the extracted corpus after extraction completes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tarfile
import tempfile

ARCHIVE_NAME = "Rashad_OS.tar.gz"
MARKER_NAME = ".rashad_unpack_ok"
ANCHOR = pathlib.Path("Rashad") / "Skill" / "ACTIVE_AUTHORITY_MANIFEST.json"


def die(msg: str, code: int = 2) -> "typing.NoReturn":  # noqa: F821
    sys.stderr.write(f"ERROR: {msg}\n")
    sys.exit(code)


def find_archive(cli: str | None) -> pathlib.Path:
    if cli:
        p = pathlib.Path(cli).expanduser().resolve()
        if not p.is_file():
            die(f"archive not found: {p}")
        return p
    here = pathlib.Path(__file__).resolve()
    for cand in (here.parent.parent / "references" / ARCHIVE_NAME,
                 here.parent / ARCHIVE_NAME):
        if cand.is_file():
            return cand.resolve()
    die(f"could not locate {ARCHIVE_NAME} next to this wrapper "
        "(expected <skill>/references/). Pass --archive.")


def sha256_of(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def writable_dir(path: pathlib.Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / ".rashad_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        return True
    except Exception:
        return False


def resolve_dest(cli_dest: str | None, digest: str) -> pathlib.Path:
    """Sha-keyed destination so distinct package builds never share a tree."""
    if cli_dest:
        base = pathlib.Path(cli_dest).expanduser()
    else:
        env = os.environ.get("RASHAD_OS_HOME")
        base = pathlib.Path(env).expanduser() if env else pathlib.Path.home() / ".rashad_os"
        if not writable_dir(base):
            base = pathlib.Path(tempfile.gettempdir()) / "rashad_os"
    if not writable_dir(base):
        die(f"no writable location for the corpus (tried {base}). Pass --dest.")
    return (base / digest[:12]).resolve()


def is_safe_member(member: tarfile.TarInfo, root: pathlib.Path) -> bool:
    """Fail-closed member filter: regular files and directories, contained paths only."""
    if member.issym() or member.islnk() or member.isdev() or member.isfifo():
        return False
    if not (member.isfile() or member.isdir()):
        return False
    name = member.name
    if name.startswith("/") or ".." in pathlib.PurePosixPath(name).parts:
        return False
    target = (root / name).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return False
    return True


def marker_is_good(dest: pathlib.Path, digest: str) -> bool:
    marker = dest / MARKER_NAME
    if not marker.is_file():
        return False
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except Exception:
        return False
    if data.get("archive_sha256") != digest:
        return False
    return (dest / "Rashad_OS" / ANCHOR).is_file()


def extract(archive: pathlib.Path, dest: pathlib.Path, digest: str) -> int:
    staging = dest.parent / f".staging-{digest[:12]}"
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)
    count = 0
    try:
        with tarfile.open(archive, "r:gz") as tf:
            members = []
            for m in tf:
                if not is_safe_member(m, staging.resolve()):
                    die(f"unsafe archive member refused: {m.name!r} — "
                        "the package is corrupt or tampered with. Do not produce.")
                members.append(m)
                if m.isfile():
                    count += 1
            tf.extractall(staging, members=members)
        root = staging / "Rashad_OS"
        if not (root / ANCHOR).is_file():
            die(f"extraction did not yield {ANCHOR} — archive layout is wrong.")
        if dest.exists():
            shutil.rmtree(dest, ignore_errors=True)
        dest.parent.mkdir(parents=True, exist_ok=True)
        staging.rename(dest)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    # Marker is written LAST: a partial extraction can never be mistaken for a good one.
    (dest / MARKER_NAME).write_text(json.dumps({
        "archive": archive.name,
        "archive_sha256": digest,
        "files": count,
        "os_root": str(dest / "Rashad_OS"),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    return count


def main() -> int:
    ap = argparse.ArgumentParser(description="Unpack the governed Rashad OS corpus.")
    ap.add_argument("--archive", help=f"Path to {ARCHIVE_NAME}")
    ap.add_argument("--dest", help="Destination base directory")
    ap.add_argument("--force", action="store_true", help="Re-extract even if already unpacked")
    ap.add_argument("--verify", action="store_true",
                    help="Run the full integrity check after unpacking")
    ap.add_argument("--print-root", action="store_true",
                    help="Print only the OS root path (extracts if needed)")
    args = ap.parse_args()

    archive = find_archive(args.archive)
    digest = sha256_of(archive)
    dest = resolve_dest(args.dest, digest)
    os_root = dest / "Rashad_OS"

    quiet = args.print_root
    if args.force or not marker_is_good(dest, digest):
        n = extract(archive, dest, digest)
        if not quiet:
            print(f"Rashad OS corpus :: UNPACKED  {n} files")
    elif not quiet:
        n = json.loads((dest / MARKER_NAME).read_text(encoding="utf-8")).get("files", "?")
        print(f"Rashad OS corpus :: REUSED    {n} files (already unpacked, archive sha matches)")

    if args.print_root:
        print(os_root)
        return 0

    print(f"  archive : {archive.name}  sha256={digest[:16]}…")
    print(f"  OS_ROOT : {os_root}")
    print(f"export RASHAD_OS_ROOT={os_root}")

    if args.verify:
        verifier = pathlib.Path(__file__).resolve().parent / "verify_integrity.py"
        if not verifier.is_file():
            die(f"verifier not found at {verifier}")
        env = dict(os.environ, RASHAD_OS_ROOT=str(os_root))
        rc = subprocess.run([sys.executable, str(verifier)], env=env).returncode
        if rc != 0:
            sys.stderr.write("VERSION_CONFLICT_BLOCK: integrity check failed. "
                             "Stop, report to the owner, do not produce.\n")
        return rc
    return 0


if __name__ == "__main__":
    sys.exit(main())
