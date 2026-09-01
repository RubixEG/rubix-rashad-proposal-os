# -*- coding: utf-8 -*-
"""Corpus instrumentation vocabulary — the exact attribute set
`brain/semantic_master_gate.inspect_semantic_html_master` measures.

This module does not invent a contract. Every constant here is read back out of the
corpus's own gate at runtime by `verify_vocabulary_against_corpus()`, so if the corpus
changes, the drift is reported instead of silently diverging.

Why it exists: a host that composes HTML with a private attribute scheme (`data-m`,
`data-box`, …) scores `measured_object_count = 0` and the corpus gate returns
SEMANTIC_MASTER_INSTRUMENTATION_MISSING + SEMANTIC_MASTER_CONTENT_BEARING_FLOOR_NOT_MET.
The deck still renders; it simply cannot be certified. That is the divergence this
plugin exists to close.
"""
from __future__ import annotations

import html as _html
import re

# --- page-level markers: every master must carry all four -------------------------
REQUIRED_PAGE_MARKERS = (
    "data-page-id",
    "data-page-mode",
    'data-region-id="DOMINANT"',
    "data-composition-spec-sha256",
)

# --- content-bearing markers: these are what `measured_object_count` counts --------
# measured = count(data-node-id) + count(data-content-slot="...") + count(data-artifact-type)
# NOTE: data-region-id is page chrome. It is deliberately NOT counted as content proof.
NODE_MARKER = "data-node-id"
SLOT_MARKER = "data-content-slot"
ARTIFACT_MARKER = "data-artifact-type"

# --- form-specific requirements ---------------------------------------------------
EVIDENCE_MARKER = "data-evidence-ref"           # CHART: >= max(1, min(nodes, 3))
HERO_ASSET_MARKER = 'data-asset-id="PRIMARY_VISUAL"'   # HERO_IMAGE: required
STATEMENT_PROOF_CLASS = "proof-strip"           # STATEMENT_BLOCK: required

# --- tokens that must never appear in visible text --------------------------------
FORBIDDEN_VISIBLE = (
    "READY", "NEXT", "BLOCKED", "NEXT_STEP=",
    "Compliance Register v0", "P0 Proposal Control Layer",
    "v7.7 Test", "EVIDENCE-BOUND",
)

_TAG = re.compile(r"<[^>]+>")
_SCRIPT_STYLE = re.compile(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", re.I)


def visible_text(markup: str) -> str:
    """Reproduce the gate's own notion of 'visible text' so leakage can be caught early."""
    stripped = _SCRIPT_STYLE.sub(" ", markup)
    return " ".join(_TAG.sub(" ", stripped).split())


def measured_object_count(markup: str) -> int:
    """Mirror of the gate's arithmetic. Use it to fail fast before invoking the gate."""
    slots = len(re.findall(r'data-content-slot=["\'][^"\']+["\']', markup))
    return markup.count(NODE_MARKER + "=") + slots + markup.count(ARTIFACT_MARKER + "=")


def page_open(page_id: str, page_mode: str, spec_sha256: str, *, lang="ar", direction="rtl") -> str:
    """Opening tag carrying all four required page markers."""
    return (
        f'<div class="page" dir="{direction}" lang="{lang}"'
        f' data-page-id="{_html.escape(str(page_id), quote=True)}"'
        f' data-page-mode="{_html.escape(str(page_mode), quote=True)}"'
        f' data-composition-spec-sha256="{_html.escape(str(spec_sha256), quote=True)}">'
    )


def region(region_id: str, inner: str, *, style: str = "") -> str:
    """A composition region. Exactly one region per page must be DOMINANT."""
    st = f' style="{style}"' if style else ""
    return f'<section data-region-id="{_html.escape(str(region_id), quote=True)}"{st}>{inner}</section>'


def node(node_id: str, artifact_type: str, inner: str, *, evidence_ref: str | None = None) -> str:
    """A content-bearing topology node. `node_id` must match a spec topology node id."""
    ev = f' data-evidence-ref="{_html.escape(str(evidence_ref), quote=True)}"' if evidence_ref else ""
    return (
        f'<div {NODE_MARKER}="{_html.escape(str(node_id), quote=True)}"'
        f' {ARTIFACT_MARKER}="{_html.escape(str(artifact_type), quote=True)}"{ev}>{inner}</div>'
    )


def slot(slot_name: str, inner: str, *, tag: str = "div") -> str:
    """A named content slot. At least two are required on every non-cover page."""
    return f'<{tag} {SLOT_MARKER}="{_html.escape(str(slot_name), quote=True)}">{inner}</{tag}>'


def preflight_markup(markup: str, spec: dict) -> list[str]:
    """Cheap local check with the same rules as the corpus gate.

    Returns a list of blocker codes. An empty list does NOT certify anything — it only
    means the corpus gate is worth invoking. `rashad_bridge.py gate-masters` is the
    authority; this is the fast fail so you do not render 33 pages before finding out.
    """
    out: list[str] = []
    for marker in REQUIRED_PAGE_MARKERS:
        if marker not in markup:
            out.append("SEMANTIC_MASTER_INSTRUMENTATION_MISSING:" + marker.split("=")[0])

    declared = (spec or {}).get("spec_sha256")
    found = re.search(r'data-composition-spec-sha256=["\']([^"\']+)', markup)
    if not declared or not found or found.group(1) != declared:
        out.append("SEMANTIC_MASTER_SPEC_HASH_BINDING_MISMATCH")

    family = str((spec or {}).get("page_family") or "")
    form = str((spec or {}).get("dominant_form") or "")
    vis = visible_text(markup)
    vis_chars = len(re.sub(r"\s+", "", vis))
    slots = len(re.findall(r'data-content-slot=["\'][^"\']+["\']', markup))
    artifacts = markup.count(ARTIFACT_MARKER + "=")

    if family not in ("COVER", "SECTION_OPENER") and (artifacts < 1 or slots < 2 or vis_chars < 40):
        out.append("SEMANTIC_MASTER_CONTENT_BEARING_FLOOR_NOT_MET")

    for token in FORBIDDEN_VISIBLE:
        if token.lower() in vis.lower():
            out.append("SEMANTIC_MASTER_INTERNAL_VOCAB_VISIBLE:" + token)

    nodes = len(((spec or {}).get("topology") or {}).get("nodes") or [])
    node_count = markup.count(NODE_MARKER + "=")
    if form not in {"TABLE", "CHART", "STATEMENT_BLOCK", "HERO_IMAGE"} and nodes and node_count != nodes:
        out.append("SEMANTIC_MASTER_TOPOLOGY_NODE_COUNT_MISMATCH")
    floor = max(1, min(nodes or 1, 3))
    if form == "TABLE" and len(re.findall(r"<tr(?:\s|>)", markup, re.I)) < floor:
        out.append("SEMANTIC_MASTER_TABLE_ROW_FLOOR_NOT_MET")
    if form == "CHART" and markup.count(EVIDENCE_MARKER + "=") < floor:
        out.append("SEMANTIC_MASTER_CHART_EVIDENCE_BAR_FLOOR_NOT_MET")
    if form == "STATEMENT_BLOCK" and (STATEMENT_PROOF_CLASS not in markup or vis_chars < 60):
        out.append("SEMANTIC_MASTER_STATEMENT_PROOF_FLOOR_NOT_MET")
    if form == "HERO_IMAGE" and HERO_ASSET_MARKER not in markup:
        out.append("SEMANTIC_MASTER_HERO_ASSET_REQUIRED")
    return sorted(set(out))


def verify_vocabulary_against_corpus(gate_module) -> dict:
    """Drift check: compare this module's constants to the live corpus gate.

    Returns {'status': 'ALIGNED'|'DRIFT', 'missing_here': [...], 'extra_here': [...]}.
    Run it in `boot`; a DRIFT result means the corpus was upgraded and this bridge must
    be updated before it may be trusted.
    """
    corpus_markers = tuple(getattr(gate_module, "REQUIRED_MARKERS", ()))
    # Both sides are normalised the same way: a bare attribute may be written with or without
    # its trailing '=', while a value-bearing marker such as data-region-id="DOMINANT" is
    # compared whole, because the value is part of the requirement.
    normalized = tuple(m.rstrip("=") for m in corpus_markers)
    mine_norm = tuple(m.rstrip("=") for m in REQUIRED_PAGE_MARKERS)
    missing = [m for m in normalized if m not in mine_norm]
    extra = [m for m in mine_norm if m not in normalized]
    corpus_forbidden = tuple(getattr(gate_module, "FORBIDDEN_VISIBLE", ()))
    forbidden_drift = sorted(set(corpus_forbidden) ^ set(FORBIDDEN_VISIBLE))
    return {
        "status": "ALIGNED" if not (missing or extra or forbidden_drift) else "DRIFT",
        "corpus_required_markers": list(corpus_markers),
        "missing_here": missing,
        "extra_here": extra,
        "forbidden_visible_drift": forbidden_drift,
    }
