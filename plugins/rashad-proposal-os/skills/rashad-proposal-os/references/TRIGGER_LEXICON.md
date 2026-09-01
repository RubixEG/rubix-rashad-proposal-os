# Trigger Lexicon — phrases → product routing

Use this table to resolve `<PRODUCT>` for the Authority Preflight (`scripts/preflight.py --init <PRODUCT>`)
and to keep the SKILL.md frontmatter description tuned. Users write in Egyptian/Gulf Arabic,
MSA, English, or a mix — match meaning, not exact strings. When a request spans products
(e.g. "summarize the tender then draft Section 3"), run them as separate governed products in
sequence, preflighting each.

## RFP_SUMMARY_ARTIFACT — bid-decision dossier (24 canonical roles)

| Arabic | English |
|---|---|
| ملخص الطرح / ملخص كراسة الشروط | RFP Summary / tender summary |
| حلّل الكراسة / حلل لي المنافسة | analyze this RFP / analyze the tender |
| ندخل ولا ما ندخلش؟ / نقدم ولا لأ؟ | should we bid? / go or no-go? / bid/no-bid |
| قرار الترسية / قرار الإدارة | management decision / bid decision dossier |
| منافسة على اعتماد / منصة اعتماد | Etimad tender (Saudi government procurement) |
| كراسة شروط ومواصفات | terms & specifications booklet |
| ملف المناقصة / وثائق الطرح | tender package / procurement documents |
| ملخص تنفيذي للطرح | executive pursuit brief |

Also trigger when tender PDFs/scans are uploaded with a bare «لخصلي دي» / "summarize this",
when the doc is clearly a government RFP. Output: the 24-role dossier ending in
`GO | GO_WITH_CONDITIONS | HOLD | NO_GO_RECOMMENDATION | INSUFFICIENT_INFORMATION`.

## PROPOSAL_SECTION_ARTIFACT — technical/full proposal content

| Arabic | English |
|---|---|
| عرض فني / عرض فني ومالي | technical proposal / technical & financial |
| العرض الكامل | full proposal |
| اكتب القسم الثالث / قسم منهجية العمل | write Section N / methodology section |
| مصفوفة الالتزام / مصفوفة المطابقة | compliance matrix |
| الملخص التنفيذي | executive summary (of a proposal) |
| خطاب المدير التنفيذي / خطاب التغطية | CEO letter / cover letter |
| نقاط التميز / لماذا روبيكس | win themes / why-us |
| خطة العمل والجدول الزمني | workplan & schedule section |
| نطاق العمل / نطاقات | scope(s) — routes to SCOPE-IDs |

Also: any explicit `R-…` code, `SCOPE-…` id, service-line playbook name, or "use the canonical
skeleton". Required authority set is `mode: ALL` — never scope down for client-visible output.

## ADVISORY_ANSWER — governed Q&A / strategy advice (no artifact gates)

| Arabic | English |
|---|---|
| إيه رأيك في الشرط ده؟ | what does clause X mean / imply? |
| إزاي نرد على المتطلب ده؟ | how should we respond to requirement Y? |
| مين المنافسين المتوقعين؟ | who are the likely competitors? |
| نسعّر إزاي تقريبًا؟ | pricing strategy question (advisory only) |

Evidence and truthfulness laws still apply; output is advisory text under the advisory-export
contract, clearly not a client-visible artifact.

## CORPUS_MAINTENANCE — working ON Rashad, not WITH it

Version bumps, audits, certification runs, adding knowledge packs / brand assets, hash-ledger
updates, red-team or verify harness runs, packaging a new ZIP. Triggers: "upgrade Rashad",
"run certification", "add these case studies to firm knowledge", "why did the gate block?",
«حدّث رشاد» / «شغّل الاختبارات».

## Anti-triggers (do NOT activate this skill)

- Generic Flutter/coding/work questions with no tender, proposal, or Rashad context.
- Translating an unrelated document (no procurement context).
- Questions *about* Anthropic skills/plugins in general.
When unsure, ask one clarifying question **only if** the product cannot be inferred from the
uploaded documents; an uploaded government tender defaults to `RFP_SUMMARY_ARTIFACT`.
