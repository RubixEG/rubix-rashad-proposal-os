#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rashad Runtime Bridge — execute the corpus's OWN production/QA runtimes.

The corpus ships executable gates. A host that reads the authorities and then writes its
own composer, its own geometry detectors and its own handoff guard produces an artifact
measured against *its* contract, not the OS's — which is why the same skill yields
different decks on different hosts. This bridge removes that freedom: every gate it
reports is a call into a corpus module, and the certificate records that module's path,
its source SHA-256, and the function invoked.

Three QA states exist: PASS, FAIL, NOT_EXECUTED. The bridge never promotes the third to
the first. Gates that need a cognition provider are reported as NOT_EXECUTED with the
reason, and `certify` still emits a certificate — one that says so out loud.

Usage
-----
    rashad_bridge.py boot                 # unpack + verify both ledgers + vocabulary drift check
    rashad_bridge.py execution-mode       # declare the cognition mode honestly
    rashad_bridge.py scaffold-spec --page-id p07 --family MATRIX --dominant-form TABLE --out s.json
    rashad_bridge.py gate-masters   --masters masters.json
    rashad_bridge.py gate-artifact  --artifact deck.pptx --masters masters.json
    rashad_bridge.py gate-binding   --artifact deck.pptx --renders renders.json
    rashad_bridge.py gate-delivery  --artifact deck.pptx --dossier dossier.json
    rashad_bridge.py certify        --artifact deck.pptx --masters masters.json \
                                    [--renders renders.json] [--dossier dossier.json] --out cert.json

masters.json
------------
    [{"page_id": "p01",
      "html_master_path": "out/p01.html",
      "composition_spec_path": "specs/p01.json"}]          # or "composition_spec": {...}

renders.json
------------
    ["<sha256 of page 1 png>", ...]                        # or [{"page_id":..., "render_sha256":...}]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_ROOT = HERE.parent
SKILL_DIR = PLUGIN_ROOT / "skills" / "rashad-proposal-os"
BOOTSTRAP = SKILL_DIR / "scripts" / "bootstrap_corpus.py"
VERIFY = SKILL_DIR / "scripts" / "verify_integrity.py"

sys.path.insert(0, str(HERE))
import instrumentation  # noqa: E402
import spec_adapter  # noqa: E402


# --------------------------------------------------------------------------- corpus
def resolve_os_root(explicit: str | None = None) -> Path:
    """RASHAD_OS_ROOT wins; otherwise ask the packaged bootstrap where the corpus is."""
    cand = explicit or os.environ.get("RASHAD_OS_ROOT")
    if cand and (Path(cand) / "Rashad").is_dir():
        return Path(cand)
    if not BOOTSTRAP.exists():
        raise SystemExit(f"BRIDGE_BLOCK: bootstrap not found at {BOOTSTRAP}")
    out = subprocess.run([sys.executable, str(BOOTSTRAP), "--print-root"],
                         capture_output=True, text=True)
    root = (out.stdout or "").strip().splitlines()[-1].strip() if out.stdout.strip() else ""
    if not root or not (Path(root) / "Rashad").is_dir():
        raise SystemExit("BRIDGE_BLOCK: could not resolve OS_ROOT — run bootstrap_corpus.py --verify")
    return Path(root)


def brain_path(os_root: Path) -> Path:
    return os_root / "Rashad" / "Brain" / "runtime"


def import_corpus(os_root: Path):
    """Put the corpus runtime on sys.path and import the gate modules we execute."""
    bp = str(brain_path(os_root))
    if bp not in sys.path:
        sys.path.insert(0, bp)
    mods = {}
    for alias, dotted in (
        ("semantic_master_gate", "brain.semantic_master_gate"),
        ("product_geometry", "brain.product_geometry"),
        ("execution_mode", "brain.execution_mode"),
        ("projector", "brain.production.projector"),
        ("pixel_truth", "brain.pixel_truth"),
    ):
        try:
            mods[alias] = __import__(dotted, fromlist=["*"])
        except Exception as exc:  # a slim build may omit an optional module
            mods[alias] = None
            mods.setdefault("_import_errors", {})[alias] = f"{type(exc).__name__}: {exc}"
    for alias, dotted in (("delivery_gate", "brain.delivery_gate"),
                          ("exact_handoff", "brain.exact_handoff")):
        try:
            mods[alias] = __import__(dotted, fromlist=["*"])
        except Exception as exc:
            mods[alias] = None
            mods.setdefault("_import_errors", {})[alias] = f"{type(exc).__name__}: {exc}"
    return mods


def _sha_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _provenance(mod, func: str) -> dict:
    """What was actually executed — module file, its source SHA, and the function name."""
    if mod is None:
        return {"module": None, "function": func, "module_sha256": None}
    f = getattr(mod, "__file__", None)
    return {
        "module": getattr(mod, "__name__", None),
        "module_file": f,
        "module_sha256": _sha_file(f) if f and Path(f).exists() else None,
        "function": func,
    }


def _not_executed(reason: str, mod=None, func: str = "") -> dict:
    return {"status": "NOT_EXECUTED", "reason": reason, "blockers": [],
            "executed": _provenance(mod, func)}


# ----------------------------------------------------------------------- input load
def load_masters(path) -> list[dict]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise SystemExit("BRIDGE_BLOCK: masters.json must be a JSON array")
    base = Path(path).resolve().parent
    out = []
    for i, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            raise SystemExit(f"BRIDGE_BLOCK: masters.json[{i-1}] is not an object")
        hp = item.get("html_master_path") or item.get("html")
        if not hp:
            raise SystemExit(f"BRIDGE_BLOCK: masters.json[{i-1}] has no html_master_path")
        hpp = Path(hp)
        if not hpp.is_absolute():
            hpp = (base / hpp).resolve()
        spec = item.get("composition_spec")
        if spec is None:
            sp = item.get("composition_spec_path")
            if not sp:
                raise SystemExit(f"BRIDGE_BLOCK: masters.json[{i-1}] has neither "
                                 f"composition_spec nor composition_spec_path")
            spp = Path(sp)
            if not spp.is_absolute():
                spp = (base / spp).resolve()
            spec = json.loads(spp.read_text(encoding="utf-8"))
        out.append({
            "page_id": item.get("page_id") or f"p{i:02d}",
            "html_master_path": str(hpp),
            "html_master_sha256": _sha_file(hpp) if hpp.exists() else None,
            "composition_spec": spec,
            "composition_spec_sha256": spec.get("spec_sha256"),
        })
    return out


def load_renders(path) -> list[str]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(raw, dict):
        raw = raw.get("renders") or raw.get("pages") or []
    out = []
    for item in raw:
        out.append(item if isinstance(item, str)
                   else (item.get("render_sha256") or item.get("selected_render_hash")))
    return out


# ---------------------------------------------------------------------------- gates
def cmd_boot(args) -> dict:
    os_root = resolve_os_root(args.os_root)
    res = {"os_root": str(os_root)}
    env = dict(os.environ, RASHAD_OS_ROOT=str(os_root))
    v = subprocess.run([sys.executable, str(VERIFY), "--root", str(os_root)],
                       capture_output=True, text=True, env=env)
    res["integrity"] = {
        "status": "PASS" if v.returncode == 0 else "VERSION_CONFLICT_BLOCK",
        "returncode": v.returncode,
        "tail": (v.stdout or v.stderr or "").strip().splitlines()[-6:],
    }
    mods = import_corpus(os_root)
    res["corpus_modules"] = {k: (getattr(m, "__file__", None) if m else None)
                             for k, m in mods.items() if not k.startswith("_")}
    if mods.get("_import_errors"):
        res["corpus_import_errors"] = mods["_import_errors"]
    gate = mods.get("semantic_master_gate")
    res["vocabulary_drift"] = (instrumentation.verify_vocabulary_against_corpus(gate)
                               if gate else {"status": "NOT_EXECUTED",
                                             "reason": "semantic_master_gate not importable"})
    res["status"] = ("PASS" if res["integrity"]["status"] == "PASS"
                     and res["vocabulary_drift"].get("status") == "ALIGNED" else "REVIEW_REQUIRED")
    return res


def cmd_execution_mode(args) -> dict:
    os_root = resolve_os_root(args.os_root)
    em = import_corpus(os_root).get("execution_mode")
    if em is None:
        return _not_executed("brain.execution_mode not importable")
    d = em.detect_execution_mode().to_dict()
    offline = d.get("mode") == "OFFLINE_VALIDATION_MODE"
    d["cognition_gates_reachable"] = not offline
    d["tier2_status"] = "NOT_EXECUTED" if offline else "REACHABLE"
    d["owner_note"] = (
        "Cognition is OFFLINE. Every council invocation returns NOT_EXECUTED, so the Tier 2 "
        "delivery gate cannot pass and MUST be reported as NOT_EXECUTED. Tier 1 gates are "
        "unaffected and remain mandatory. To reach Tier 2, set OPENAI_API_KEY and "
        "OPENAI_RASHAD_MODEL, or have the host inject host_invoke_fn (RASHAD_EXECUTION_MODE=HOST)."
        if offline else
        "Cognition provider configured. Tier 2 gates are reachable; run gate-delivery."
    )
    d["executed"] = _provenance(em, "detect_execution_mode")
    return d


def cmd_scaffold_spec(args) -> dict:
    os_root = resolve_os_root(args.os_root)
    gate = import_corpus(os_root).get("semantic_master_gate")
    nodes = [spec_adapter.node_spec(f"n{i}", args.node_kind) for i in range(1, args.nodes + 1)]
    spec = spec_adapter.build_spec(
        args.page_id, args.family, args.dominant_form,
        role=args.role or args.page_id, page_mode=args.page_mode,
        dominant_mass_target=args.mass, topology_nodes=nodes, gate_module=gate,
    )
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"status": "PASS", "spec_sha256": spec["spec_sha256"],
            "written": args.out, "spec": spec,
            "hash_source": "corpus._spec_hash" if gate else "bridge mirror"}


def cmd_gate_masters(args) -> dict:
    os_root = resolve_os_root(args.os_root)
    gate = import_corpus(os_root).get("semantic_master_gate")
    if gate is None:
        return _not_executed("brain.semantic_master_gate not importable")
    masters = load_masters(args.masters)
    pages, blockers = [], []
    for m in masters:
        r = gate.inspect_semantic_html_master(m["html_master_path"], m["composition_spec"])
        pages.append({"page_id": m["page_id"], "status": r.get("status"),
                      "measured_object_count": r.get("measured_object_count"),
                      "blockers": r.get("blockers", [])})
        blockers += [f'{m["page_id"]}::{b}' for b in r.get("blockers", [])]
    return {"gate": "SEMANTIC_MASTER_GATE",
            "status": "PASS" if not blockers else "FAIL",
            "pages": len(pages), "page_results": pages, "blockers": sorted(set(blockers)),
            "executed": _provenance(gate, "inspect_semantic_html_master")}


def cmd_gate_artifact(args) -> dict:
    os_root = resolve_os_root(args.os_root)
    pg = import_corpus(os_root).get("product_geometry")
    if pg is None:
        return _not_executed("brain.product_geometry not importable")
    # `expected_pages` is a LIST of per-page semantic-master descriptors, not a page count.
    # Passing an int raises TypeError inside _analyze_pages.
    expected = None
    if args.masters:
        expected = [{"page_id": m["page_id"],
                     "html_master_path": m["html_master_path"],
                     "html_master_sha256": m["html_master_sha256"],
                     "composition_spec": m["composition_spec"],
                     "composition_spec_sha256": m["composition_spec_sha256"]}
                    for m in load_masters(args.masters)]
    r = pg.inspect_artifact(args.artifact, expected_pages=expected)
    return {"gate": "PRODUCT_GEOMETRY",
            "status": "PASS" if r.get("status") not in ("BLOCKED",) and not r.get("blockers") else "FAIL",
            "corpus_status": r.get("status"),
            "page_count": r.get("page_count"),
            "diversity": r.get("diversity"),
            "stats": r.get("stats"),
            "blockers": r.get("blockers", []),
            "warnings": r.get("warnings", []),
            "expected_pages_supplied": bool(expected),
            "executed": _provenance(pg, "inspect_artifact")}


def cmd_gate_binding(args) -> dict:
    os_root = resolve_os_root(args.os_root)
    pr = import_corpus(os_root).get("projector")
    if pr is None:
        return _not_executed("brain.production.projector not importable")
    expected = load_renders(args.renders)
    r = pr.verify_projection_media_binding(Path(args.artifact), expected)
    return {"gate": "PROJECTION_MEDIA_BINDING",
            "status": "PASS" if r.get("status") == "PASS" else "FAIL",
            "corpus_status": r.get("status"),
            "expected_count": len(expected),
            "embedded_count": len(r.get("embedded_media_hashes") or []),
            "order_preserved": (r.get("embedded_media_hashes") or []) == expected,
            "blockers": r.get("blockers", []),
            "executed": _provenance(pr, "verify_projection_media_binding")}


def cmd_gate_delivery(args) -> dict:
    os_root = resolve_os_root(args.os_root)
    mods = import_corpus(os_root)
    dg, em = mods.get("delivery_gate"), mods.get("execution_mode")
    if dg is None:
        return _not_executed("brain.delivery_gate not importable "
                             f"({(mods.get('_import_errors') or {}).get('delivery_gate')})")
    mode = em.detect_execution_mode().to_dict() if em else {"mode": "UNKNOWN"}
    if mode.get("mode") == "OFFLINE_VALIDATION_MODE" and not args.force:
        out = _not_executed(
            "OFFLINE_VALIDATION_MODE — the delivery gate requires per-page "
            "brain_session_execution_evidence, expert_execution_ledger, artifact_council_execution, "
            "art_direction_execution and production_council_execution. No cognition provider is "
            "configured, so these ledgers do not exist and MUST NOT be fabricated.",
            dg, "validate_user_visible_delivery")
        out["execution_mode"] = mode
        out["missing_ledgers"] = ["brain_session_execution_evidence", "expert_execution_ledger",
                                 "artifact_council_execution", "art_direction_execution",
                                 "production_council_execution"]
        return out
    dossier = json.loads(Path(args.dossier).read_text(encoding="utf-8")) if args.dossier else {}
    try:
        r = dg.validate_user_visible_delivery(dossier, args.artifact, requested=args.level)
    except Exception as exc:
        out = _not_executed(f"delivery gate raised {type(exc).__name__}: {exc}",
                            dg, "validate_user_visible_delivery")
        out["execution_mode"] = mode
        return out
    return {"gate": "DELIVERY_GATE",
            "status": "PASS" if r.get("status") == "DELIVERY_ALLOWED" else "FAIL",
            "corpus_status": r.get("status"), "blockers": r.get("blockers", []),
            "deck_sha256": r.get("deck_sha256"),
            "handoff_certificate_status": (r.get("handoff_certificate") or {}).get("status"),
            "execution_mode": mode,
            "executed": _provenance(dg, "validate_user_visible_delivery")}


def cmd_certify(args) -> dict:
    """Run every reachable gate and emit the Bridge Execution Certificate."""
    os_root = resolve_os_root(args.os_root)
    gates: dict = {}
    gates["boot"] = cmd_boot(args)
    gates["execution_mode"] = cmd_execution_mode(args)
    gates["semantic_master_gate"] = (cmd_gate_masters(args) if args.masters
                                     else _not_executed("--masters not supplied"))
    gates["product_geometry"] = (cmd_gate_artifact(args) if args.artifact
                                 else _not_executed("--artifact not supplied"))
    gates["projection_media_binding"] = (cmd_gate_binding(args) if (args.artifact and args.renders)
                                         else _not_executed("--renders not supplied"))
    gates["delivery_gate"] = (cmd_gate_delivery(args) if args.artifact
                              else _not_executed("--artifact not supplied"))

    tier1 = ["semantic_master_gate", "product_geometry", "projection_media_binding"]
    t1 = {k: gates[k].get("status") for k in tier1}
    failed = [k for k, v in t1.items() if v == "FAIL"]
    skipped = [k for k, v in t1.items() if v == "NOT_EXECUTED"]

    if failed:
        verdict = "BLOCK_PRODUCTION"
    elif skipped:
        verdict = "TIER1_INCOMPLETE"
    elif gates["delivery_gate"].get("status") == "PASS":
        verdict = "CERTIFIED_FOR_HANDOFF"
    else:
        verdict = "TIER1_CERTIFIED_TIER2_NOT_EXECUTED"

    cert = {
        "certificate": "RASHAD_BRIDGE_EXECUTION_CERTIFICATE_V1",
        "os_root": str(os_root),
        "artifact": args.artifact,
        "artifact_sha256": _sha_file(args.artifact) if args.artifact and Path(args.artifact).exists() else None,
        "verdict": verdict,
        "tier1": t1,
        "tier1_failed": failed,
        "tier1_not_executed": skipped,
        "tier2": {"delivery_gate": gates["delivery_gate"].get("status")},
        "qa_states_used": ["PASS", "FAIL", "NOT_EXECUTED"],
        "declaration": {
            "CERTIFIED_FOR_HANDOFF":
                "Every gate, Tier 1 and Tier 2, executed and passed against the delivered bytes.",
            "TIER1_CERTIFIED_TIER2_NOT_EXECUTED":
                "Deterministic geometry, instrumentation and media-binding gates executed and passed "
                "against the delivered bytes. The council/expert execution layer did NOT execute; no "
                "Expert or Artifact Council Execution Ledger exists. Report this to the owner "
                "verbatim — the artifact is measured but not council-certified.",
            "TIER1_INCOMPLETE":
                "One or more mandatory Tier 1 gates did not run. The artifact carries no complete "
                "product evidence and must not be presented as QA-passed.",
            "BLOCK_PRODUCTION":
                "A mandatory Tier 1 gate FAILED. Do not deliver. Repair and re-run.",
        }[verdict],
        "gates": gates,
    }
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(cert, ensure_ascii=False, indent=1), encoding="utf-8")
    return cert


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(prog="rashad_bridge.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    # Shared flags are declared on a parent parser so they work before OR after the
    # subcommand — `bridge.py --quiet boot` and `bridge.py boot --quiet` both parse.
    # default=SUPPRESS on the parent means an unsupplied flag leaves the namespace alone,
    # so a value given before the subcommand is not clobbered by the subparser's default.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--os-root", default=argparse.SUPPRESS,
                        help="override OS_ROOT (default: $RASHAD_OS_ROOT or bootstrap)")
    common.add_argument("--quiet", action="store_true", default=argparse.SUPPRESS,
                        help="print only the status line")
    ap.add_argument("--os-root", default=None,
                    help="override OS_ROOT (default: $RASHAD_OS_ROOT or bootstrap)")
    ap.add_argument("--quiet", action="store_true", default=False,
                    help="print only the status line")
    sub = ap.add_subparsers(
        dest="cmd", required=True,
        parser_class=lambda **kw: argparse.ArgumentParser(parents=[common], **kw))

    sub.add_parser("boot", help="unpack + verify both ledgers + vocabulary drift check")
    sub.add_parser("execution-mode", help="declare the cognition execution mode")

    s = sub.add_parser("scaffold-spec", help="emit a gate-valid PageCompositionSpec")
    s.add_argument("--page-id", required=True)
    s.add_argument("--family", required=True, help="COVER | SECTION_OPENER | MATRIX | ...")
    s.add_argument("--dominant-form", required=True, choices=list(spec_adapter.DOMINANT_FORMS))
    s.add_argument("--role", default="")
    s.add_argument("--page-mode", default="ANALYTICAL")
    s.add_argument("--mass", type=float, default=None)
    s.add_argument("--nodes", type=int, default=3)
    s.add_argument("--node-kind", default="FACT")
    s.add_argument("--out")

    s = sub.add_parser("gate-masters", help="corpus semantic-master gate on every HTML master")
    s.add_argument("--masters", required=True)

    s = sub.add_parser("gate-artifact", help="corpus product-geometry inspection of the artifact")
    s.add_argument("--artifact", required=True)
    s.add_argument("--masters", help="strongly recommended: enables semantic-master proof")

    s = sub.add_parser("gate-binding", help="corpus projection media-binding proof")
    s.add_argument("--artifact", required=True)
    s.add_argument("--renders", required=True)

    s = sub.add_parser("gate-delivery", help="corpus delivery gate (Tier 2, needs cognition)")
    s.add_argument("--artifact", required=True)
    s.add_argument("--dossier")
    s.add_argument("--level", default="USER_VISIBLE_ARTIFACT_DRAFT")
    s.add_argument("--force", action="store_true",
                   help="attempt the gate even in OFFLINE_VALIDATION_MODE (it will report blockers)")

    s = sub.add_parser("certify", help="run all reachable gates and write the certificate")
    s.add_argument("--artifact", required=True)
    s.add_argument("--masters")
    s.add_argument("--renders")
    s.add_argument("--dossier")
    s.add_argument("--level", default="USER_VISIBLE_ARTIFACT_DRAFT")
    s.add_argument("--force", action="store_true")
    s.add_argument("--out")

    a = ap.parse_args()
    for attr, default in (("masters", None), ("renders", None), ("dossier", None),
                          ("artifact", None), ("level", "USER_VISIBLE_ARTIFACT_DRAFT"),
                          ("force", False), ("out", None)):
        if not hasattr(a, attr):
            setattr(a, attr, default)

    fn = {"boot": cmd_boot, "execution-mode": cmd_execution_mode,
          "scaffold-spec": cmd_scaffold_spec, "gate-masters": cmd_gate_masters,
          "gate-artifact": cmd_gate_artifact, "gate-binding": cmd_gate_binding,
          "gate-delivery": cmd_gate_delivery, "certify": cmd_certify}[a.cmd]
    try:
        res = fn(a)
    except ValueError as exc:
        # Spec-contract violations are owner-actionable, not stack traces.
        print(json.dumps({"status": "BLOCK_PRODUCTION", "reason": "SPEC_CONTRACT_VIOLATION",
                          "detail": str(exc)}, ensure_ascii=False, indent=1))
        return 2
    except FileNotFoundError as exc:
        print(json.dumps({"status": "BLOCK_PRODUCTION", "reason": "INPUT_NOT_FOUND",
                          "detail": str(exc)}, ensure_ascii=False, indent=1))
        return 2

    if a.quiet:
        print(res.get("verdict") or res.get("status") or res.get("mode") or "OK")
    else:
        print(json.dumps(res, ensure_ascii=False, indent=1))

    status = res.get("verdict") or res.get("status") or ""
    return 0 if status in ("PASS", "CERTIFIED_FOR_HANDOFF",
                           "TIER1_CERTIFIED_TIER2_NOT_EXECUTED",
                           "HOST_NATIVE_MODE", "API_PROVIDER_MODE",
                           "OFFLINE_VALIDATION_MODE", "REVIEW_REQUIRED") else 2


if __name__ == "__main__":
    raise SystemExit(main())
