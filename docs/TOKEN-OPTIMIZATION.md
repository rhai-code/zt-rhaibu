# Token Optimization — zt-rhaibu OODA Pipeline

Initiative started 2026-09-15. Goal: cut token burn for a full auto-accept
Observe → Orient → Do → Act → Publish run **without changing the pipeline,
phases, gates, or outputs**.

Baseline anchor: a prior full run took a context reset at **≥1M tokens**.

## Cost model

Three independent cost axes. A full run's total ≈ sum of all three:

1. **Always-on registry** — frontmatter (name + description + triggers) of every
   SKILL.md, injected into the system prompt of every session in the repo.
2. **Per-phase skill loads** — SKILL.md bodies + linked references/templates
   loaded on first invocation in a session.
3. **Session history (dominant term)** — with auto-accept, *every* tool call
   re-sends the full conversation. Phases chained in one session re-pay for
   Observe/Orient/Do transcript (RAC files, schemas, scaffold output, build
   logs) on every subsequent Act step and fix-loop iteration. This is what
   takes a run from ~80K to >1M.

Measure any change with:

```bash
python3 tools/meter.py            # prints registry / bodies / per-phase bundles
```

Baseline snapshot: `/tmp/zt-rhaibu-baseline` (pre-optimization copy).
Compare with `diff -r /tmp/zt-rhaibu-baseline <repo> --exclude=.git`.

## What was done (round 1)

| Change | Files | Effect |
|---|---|---|
| Trim always-on descriptions to one-liners (triggers.keywords already carry trigger words) | all 5 workshop-* + openshift-workshop-builder SKILL.md | registry 8.4K → 6.0K bytes (**-29%**), every session |
| Single-source P.1–P.4 / C.1 rules in openshift-workshop-builder (pointers to WORKSHOP-COMMON-RULES + prose-style.md, kept as one-liners so verify-content check IDs still resolve) | openshift-workshop-builder/SKILL.md | Do bundle -~1K tokens |
| Extract catalog-builder `#include` boilerplate + full `__meta__` template into `references/common-yaml-rules.md` (content-verified verbatim move; question logic stays in SKILL.md) | catalog-builder/SKILL.md | -3.8K bytes; loads only when generating common.yaml |
| Reference-reading budget: ≤1 real catalog, structure sections only; bundled examples — read only the one matching the infra type, never all | catalog-builder/SKILL.md step 9.1 | cuts the 87KB examples/ reads to one ~2–16KB file |
| Fix-loop delta re-test: content fixes re-test only failed requirements + changed module pages (verify-content invoked with `modules:[...]`); infra fixes still re-run the full suite (they invalidate all evidence) | workshop-act/SKILL.md step 5b/6 | per-iteration Act cost now proportional to change size, not suite size |
| **Subagent isolation rule** (WORKSHOP-COMMON-RULES v1.3 §7a): high-traffic steps run in subagents, structured results only; per-phase hooks in observe/orient/do/act/screenshot/catalog-builder | WORKSHOP-COMMON-RULES.md + 6 SKILL.md files | removes browser/build/schema/catalog tool traffic from the main conversation — attacks the dominant cumulative-history cost term |
| Meter + this doc | tools/meter.py, docs/TOKEN-OPTIMIZATION.md | measurable iteration from here on |

## What remains (the big levers, in order)

### 1. Subagent isolation (biggest win, implemented — WORKSHOP-COMMON-RULES §7a)

Auto-accept + one session = every tool call re-sends all prior tool traffic,
which is what takes a run from ~80K to >1M. The fix is to keep that traffic
*out* of the main conversation via subagents, which get isolated contexts and
return only their final structured result:

- Canonical rule added to `WORKSHOP-COMMON-RULES.md` §7a (REQUIRED): delegate
  high-traffic steps (browser runs, screenshot capture, per-module drafting,
  cluster diagnostics, reference/catalog reads, schema dumps); pass the
  subagent everything it needs; return structured summaries only (tables,
  paths, ≤10-line error excerpts); never delegate decisions (RAC
  ratification, fix-loop categorization, publish) — the main agent re-reads a
  subagent's output files before acting on its claims.
- Per-phase hooks added in all four workshop-* skills + workshop-screenshot +
  catalog-builder naming each phase's specific delegable steps and return
  contract.
- No phase boundaries, handoffs, or gates changed — same pipeline, same
  outputs; only *where* the verbose work executes.

Expected effect: the main conversation per phase shrinks to ~skill bundle +
RAC files + structured results (low tens of K tokens), regardless of how many
playwright snapshots or build logs the subagents chew through. Combined with
the round-1 trims, this is the 1M → low-hundreds-of-K path.

### 2. catalog-builder mode split (if publish stays in-session)

MODE 1's sequential flow (steps 1–12) still lives inline; MODE 2/3/4 are
already references. If the 48KB→40KB SKILL.md still loads whole in a publish
step, split MODE 1 steps 3–8 (infra question branches) into
`references/mode-1-full-catalog.md` and keep only the routing + headless +
orchestrator paths inline. Defer until a real publish-step run is metered —
catalog-builder is *not* invoked by workshop-act step 8 (publish is a plain
PR); it's a separate post-publish step, so its cost only hits runs that build
a catalog too.

### 3. Screenshot budget in workshop-act

Step 5 captures a screenshot per requirement *per iteration*. Under delta
re-test (done), iterations are cheaper; a further cap (only re-capture
screenshots whose page changed) is the next knob if Act still dominates.

## Verification protocol

1. `python3 tools/meter.py` before and after any edit (numbers must only go
   down unless a change is explicitly adding behavior).
2. For any content moved to a reference file: diff the moved text against the
   baseline copy to prove it is verbatim (see the round-1 verification for
   `common-yaml-rules.md`).
3. The real proof is one full pipeline run with phase-isolated invocation and
   per-session token accounting. Ask Sawyer for a run with usage output
   (e.g. Claude Code `/cost` or a metering proxy) so we can A/B the 1M
   baseline against the optimized launch pattern.

## Constraints (Sawyer)

- No pipeline or structural changes: same 5 phases, same handoffs, same RAC
  contract, same gates, same outputs.
- All changes are prose/skill-text: trims, pointers, budgets, delta semantics.
