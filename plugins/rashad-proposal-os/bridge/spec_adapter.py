# -*- coding: utf-8 -*-
"""PageCompositionSpec builder that satisfies the corpus's own self-hash contract.

`brain/semantic_master_gate._spec_hash` computes the spec's identity as:

    payload = {k: v for k, v in spec.items() if k not in {'spec_sha256', 'validation'}}
    sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')))

Get that wrong by one separator and every page returns COMPOSITION_SPEC_SELF_HASH_INVALID.
This module reproduces it exactly and — in `spec_hash()` — prefers the corpus function
itself when the corpus is importable, so the two can never drift apart.
"""
from __future__ import annotations

import hashlib
import json

# Bands enforced by the corpus gate. Do not widen them here; widen them in the corpus.
HERO_MASS_BAND = (0.90, 1.00)     # page_family COVER/SECTION_OPENER with dominant_form HERO_IMAGE
BODY_MASS_BAND = (0.32, 0.68)     # every other page
MIN_TYPE_LEVELS = 3
DEFAULT_MAX_TOPOLOGY_NODES = 8

DOMINANT_FORMS = ("TABLE", "CHART", "STATEMENT_BLOCK", "HERO_IMAGE", "DIAGRAM", "MATRIX", "TIMELINE")
HERO_FAMILIES = ("COVER", "SECTION_OPENER")

# Arabic-first type floors in points (STRENGTH_FLOOR_PT). Levels are emitted largest-first.
DEFAULT_TYPE_LEVELS = [
    {"level": "TITLE", "size_pt": 24.0, "role": "executive title"},
    {"level": "LEAD", "size_pt": 17.0, "role": "lead statement"},
    {"level": "BODY", "size_pt": 16.0, "role": "Arabic body prose"},
    {"level": "TABLE_BODY", "size_pt": 14.0, "role": "table body"},
    {"level": "LABEL", "size_pt": 12.0, "role": "label / axis"},
    {"level": "SOURCE", "size_pt": 10.0, "role": "source locator"},
]

DEFAULT_NEGATIVE_SPACE = [
    {"zone": "OUTER_MARGIN", "kind": "STRUCTURAL", "min_px": 64},
    {"zone": "HEADER_TO_BODY", "kind": "SEPARATION", "min_px": 32},
    {"zone": "BODY_TO_SOURCE", "kind": "SEPARATION", "min_px": 24},
]


def _canonical(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def spec_hash(spec: dict, gate_module=None) -> str:
    """Self-hash of a spec. Delegates to the corpus when available."""
    if gate_module is not None and hasattr(gate_module, "_spec_hash"):
        return gate_module._spec_hash(spec)
    payload = {k: v for k, v in dict(spec or {}).items() if k not in {"spec_sha256", "validation"}}
    return hashlib.sha256(_canonical(payload).encode()).hexdigest()


def build_spec(
    page_id: str,
    page_family: str,
    dominant_form: str,
    *,
    role: str = "",
    page_mode: str = "ANALYTICAL",
    dominant_mass_target: float | None = None,
    topology_nodes: list | None = None,
    type_levels: list | None = None,
    negative_space_zones: list | None = None,
    max_topology_nodes: int = DEFAULT_MAX_TOPOLOGY_NODES,
    language: str = "ar",
    direction: str = "rtl",
    extra: dict | None = None,
    gate_module=None,
) -> dict:
    """Build a gate-valid PageCompositionSpec.

    Raises ValueError on anything the corpus gate would reject, so the failure lands here
    with a readable message rather than 33 pages later as an opaque blocker code.
    """
    family = str(page_family).upper()
    form = str(dominant_form).upper()
    hero = family in HERO_FAMILIES and form == "HERO_IMAGE"

    lo, hi = HERO_MASS_BAND if hero else BODY_MASS_BAND
    if dominant_mass_target is None:
        dominant_mass_target = 0.95 if hero else 0.50
    mass = round(float(dominant_mass_target), 4)
    if not (lo <= mass <= hi):
        raise ValueError(
            f"{page_id}: dominant_mass_target {mass} outside the corpus band [{lo}, {hi}] "
            f"for page_family={family} dominant_form={form}"
        )

    levels = list(type_levels or DEFAULT_TYPE_LEVELS)
    if len(levels) < MIN_TYPE_LEVELS:
        raise ValueError(f"{page_id}: typographic_hierarchy needs >= {MIN_TYPE_LEVELS} levels, got {len(levels)}")

    zones = list(negative_space_zones or DEFAULT_NEGATIVE_SPACE)
    if not zones:
        raise ValueError(f"{page_id}: negative_space_zones must not be empty")

    nodes = list(topology_nodes or [])
    if len(nodes) > int(max_topology_nodes):
        raise ValueError(
            f"{page_id}: {len(nodes)} topology nodes exceeds acceptance."
            f"max_topology_nodes_per_page={max_topology_nodes}"
        )

    spec: dict = {
        "page_id": str(page_id),
        "role": str(role or page_id),
        "page_family": family,
        "page_mode": str(page_mode).upper(),
        "dominant_form": form,
        "dominant_mass_target": mass,
        "language": language,
        "direction": direction,
        "typographic_hierarchy": {"levels": levels},
        "negative_space_zones": zones,
        "topology": {"nodes": nodes},
        "acceptance": {"max_topology_nodes_per_page": int(max_topology_nodes)},
    }
    if extra:
        for key in ("spec_sha256", "validation"):
            extra.pop(key, None)
        spec.update(extra)

    # validation is excluded from the hash payload, so it is set before hashing.
    spec["validation"] = {"status": "PASS", "validator": "rashad-bridge/spec_adapter"}
    spec["spec_sha256"] = spec_hash(spec, gate_module=gate_module)
    return spec


def node_spec(node_id: str, kind: str, label: str = "", evidence_ref: str | None = None) -> dict:
    """One topology node. `node_id` must be the same string used in the HTML data-node-id."""
    out = {"id": str(node_id), "kind": str(kind).upper(), "label": str(label or node_id)}
    if evidence_ref:
        out["evidence_ref"] = str(evidence_ref)
    return out


def rehash(spec: dict, gate_module=None) -> dict:
    """Recompute spec_sha256 after an edit. Call this or the binding check fails."""
    spec = dict(spec)
    spec.setdefault("validation", {"status": "PASS", "validator": "rashad-bridge/spec_adapter"})
    spec["spec_sha256"] = spec_hash(spec, gate_module=gate_module)
    return spec
