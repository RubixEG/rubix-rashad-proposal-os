#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bridge self-test — proves, on THIS host, that the corpus gate accepts what the bridge builds.

Run it once after installing the plugin:

    python3 "${CLAUDE_PLUGIN_ROOT}/bridge/selftest.py"

It builds a PageCompositionSpec with `spec_adapter`, composes a master with the corpus
instrumentation vocabulary from `instrumentation`, and invokes the corpus's own
`brain/semantic_master_gate.inspect_semantic_html_master`. A PASS means specs, hashes and
markers line up on this machine. A FAIL prints the corpus's blocker codes verbatim — those
are the real contract, not this script's opinion.

Exit 0 = PASS, 2 = FAIL.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import instrumentation as I  # noqa: E402
import rashad_bridge as B  # noqa: E402
import spec_adapter as S  # noqa: E402

ROWS = [
    ("مدة العقد", "٣٦ شهرًا", "البند ٥١"),
    ("وزن التقييم الفني", "٧٠٪", "البند ٦٥"),
    ("حد الاجتياز", "٧٠٪", "البند ٦٥"),
]


def build_master(spec: dict) -> str:
    """A minimal but genuinely content-bearing TABLE master in the corpus vocabulary."""
    head = "<tr><th>البند</th><th>القيمة</th><th>المصدر</th></tr>"
    body = "".join(
        f"<tr>{I.node(f'n{i}', 'TABLE_ROW', f'<td>{k}</td><td>{v}</td><td>{src}</td>')}</tr>"
        for i, (k, v, src) in enumerate(ROWS, 1)
    )
    table = f'<table dir="rtl"><thead>{head}</thead><tbody>{body}</tbody></table>'
    dominant = I.region("DOMINANT", I.slot("BODY", table))
    supporting = I.region(
        "SUPPORTING",
        I.slot("TITLE", "<h1>شروط التعاقد الجوهرية</h1>")
        + I.slot("SOURCE", "<p>المصدر: كراسة الشروط والمواصفات، البنود ٥١ و٦٥.</p>"),
    )
    return (
        "<!doctype html><html lang='ar' dir='rtl'><head><meta charset='utf-8'>"
        "<style>body{font-family:sans-serif;font-size:16pt}td,th{font-size:14pt;padding:8px}</style>"
        "</head><body>"
        + I.page_open(spec["page_id"], spec["page_mode"], spec["spec_sha256"])
        + supporting + dominant
        + "</div></body></html>"
    )


def main() -> int:
    os_root = B.resolve_os_root(None)
    gate = B.import_corpus(os_root).get("semantic_master_gate")
    if gate is None:
        print("FAIL: brain.semantic_master_gate is not importable from", os_root)
        return 2

    spec = S.build_spec(
        "selftest-p01", "MATRIX", "TABLE",
        role="SELFTEST", page_mode="ANALYTICAL", dominant_mass_target=0.52,
        topology_nodes=[S.node_spec(f"n{i}", "TABLE_ROW", k) for i, (k, _, _) in enumerate(ROWS, 1)],
        gate_module=gate,
    )
    markup = build_master(spec)

    local = I.preflight_markup(markup, spec)
    tmp = Path(tempfile.mkdtemp(prefix="rashad-selftest-"))
    master = tmp / "selftest-p01.html"
    master.write_text(markup, encoding="utf-8")

    result = gate.inspect_semantic_html_master(str(master), spec)
    ok = result.get("status") == "PASS"

    print(json.dumps({
        "os_root": str(os_root),
        "corpus_gate": getattr(gate, "__file__", None),
        "spec_sha256": spec["spec_sha256"],
        "local_preflight_blockers": local,
        "corpus_status": result.get("status"),
        "corpus_blockers": result.get("blockers"),
        "measured_object_count": result.get("measured_object_count"),
        "node_count": result.get("node_count"),
        "artifact_count": result.get("artifact_count"),
        "visible_content_char_count": result.get("visible_content_char_count"),
        "verdict": "PASS — corpus gate accepts bridge-built masters on this host"
                   if ok else "FAIL — see corpus_blockers",
    }, ensure_ascii=False, indent=1))
    return 0 if ok and not local else 2


if __name__ == "__main__":
    raise SystemExit(main())
