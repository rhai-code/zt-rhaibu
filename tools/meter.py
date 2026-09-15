#!/usr/bin/env python3
"""Token meter for the zt-rhaibu OODA workshop-factory skill collection.

Two cost axes, both measured without running any LLM:

1. SKILL REGISTRY (always-on cost): for every SKILL.md, the frontmatter
   (name + description + triggers) is what skill-indexing runtimes (Claude
   Code, etc.) inject into the system prompt on EVERY session, whether the
   skill is used or not. Trimmed descriptions save tokens on every run.

2. SKILL BODIES (on-demand cost): the SKILL.md body + its linked
   references/templates/examples load the first time the skill is invoked
   in a session. The full-pipeline cost is the sum of each phase's bundle
   (which skills a phase loads), computed from an explicit phase map.

Usage:
    python3 meter.py [repo_root]

Output: per-skill table, per-phase bundles, and pipeline totals, in bytes
and estimated tokens (1 token ~= 4 bytes for markdown/YAML; code is ~3.5,
prose ~4.5 — 4 is the right middle estimate for this mix).
"""
import os
import re
import sys

ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Phase -> (skill, [extra linked files loaded in that phase])
# Mirrors the skill-coordination sections of each SKILL.md.
PHASES = {
    "workshop-observe": (
        "workshop-observe",
        ["skills/docs/WORKSHOP-COMMON-RULES.md"],
    ),
    "workshop-orient": (
        "workshop-orient",
        [
            "skills/workshop-orient/references/decided-quickref.md",
            "skills/docs/WORKSHOP-COMMON-RULES.md",
        ],
    ),
    "workshop-do": (
        "workshop-do",
        [
            "skills/workshop-do/references/infra-patterns.md",
            "skills/openshift-workshop-builder/SKILL.md",
            "skills/openshift-workshop-builder/references/prose-style.md",
            "skills/openshift-workshop-builder/references/yaml-callouts.md",
            "skills/docs/WORKSHOP-COMMON-RULES.md",
        ],
    ),
    "workshop-act": (
        "workshop-act",
        [
            "skills/workshop-act/references/test-patterns.md",
            "skills/verify-content/SKILL.md",
            "skills/workshop-screenshot/SKILL.md",
            "skills/workshop-screenshot/references/capture-patterns.md",
            "skills/playwright-cli/SKILL.md",
            "skills/docs/WORKSHOP-COMMON-RULES.md",
        ],
    ),
    "workshop-act:fixloop(x5 worst case)": (
        "workshop-act",
        [
            # fix-loop iterations re-load the quality gate + browser skills
            "skills/verify-content/SKILL.md",
            "skills/playwright-cli/SKILL.md",
        ],
    ),
    "catalog-builder (publish)": (
        "catalog-builder",
        [
            "skills/catalog-builder/references/mode-2-description.md",
            "skills/catalog-builder/references/mode-3-info-message.md",
            "skills/catalog-builder/references/mode-4-virtual-ci.md",
            "skills/catalog-builder/references/developer-guidelines.md",
            "skills/catalog-builder/templates/common.yaml.template",
            "skills/catalog-builder/examples/ocp-demo/common.yaml",
        ],
    ),
}


def split_frontmatter(text: str):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def linked_files(skill_md_path: str):
    """Paths referenced from a SKILL.md that exist in the repo."""
    text = open(skill_md_path).read()
    refs = set()
    for m in re.finditer(r"`?((?:references|templates|examples|docs)/[\w./-]+\.\w+)`?", text):
        p = m.group(1)
        cand = os.path.join(os.path.dirname(skill_md_path), p)
        if os.path.exists(cand):
            refs.add(os.path.normpath(cand))
    return refs


def size(p):
    return os.path.getsize(p) if os.path.exists(p) else 0


def main():
    skills_dir = os.path.join(ROOT, "skills")
    skills = {}
    for name in sorted(os.listdir(skills_dir)):
        md = os.path.join(skills_dir, name, "SKILL.md")
        if os.path.exists(md):
            text = open(md).read()
            fm, body = split_frontmatter(text)
            linked = sorted(linked_files(md))
            skills[name] = {
                "fm": len(fm) + 10,  # frontmatter fences
                "body": len(body),
                "linked": linked,
            }

    reg_fm = sum(s["fm"] for s in skills.values())
    reg_body = sum(s["body"] for s in skills.values())

    print("=" * 78)
    print("1. SKILL REGISTRY  (frontmatter injected on EVERY session)")
    print("=" * 78)
    print(f"{'skill':34} {'frontmatter':>12} {'~tokens':>9}")
    print("-" * 58)
    for name, s in sorted(skills.items(), key=lambda kv: -kv[1]["fm"]):
        print(f"{name:34} {s['fm']:>12,} {s['fm']/4:>9,.0f}")
    print("-" * 58)
    print(f"{'TOTAL (always-on cost)':34} {reg_fm:>12,} {reg_fm/4:>9,.0f}")

    print()
    print("=" * 78)
    print("2. SKILL BODIES  (loaded on first invocation per session)")
    print("=" * 78)
    print(f"{'skill':34} {'SKILL.md':>10} {'linked':>10} {'~tokens':>9}")
    print("-" * 66)
    tot_body = 0
    tot_linked = 0
    for name, s in skills.items():
        lk = sum(size(p) for p in s["linked"])
        tot_body += s["body"]
        tot_linked += lk
        print(f"{name:34} {s['body']:>10,} {lk:>10,} {(s['body']+lk)/4:>9,.0f}")
    print("-" * 66)
    print(f"{'TOTAL (all skills + all links)':34} {tot_body+tot_linked:>10,} {'' :>10} {(tot_body+tot_linked)/4:>9,.0f}")

    print()
    print("=" * 78)
    print("3. PIPELINE BUNDLES  (one full Observe->Orient->Do->Act->Publish)")
    print("=" * 78)
    loaded_once = {}  # path -> bytes (dedupe within a single session)
    print(f"{'phase':42} {'fresh-load':>11} {'session-cum':>12}")
    print("-" * 68)
    grand = 0
    for phase, (skill, extras) in PHASES.items():
        md = os.path.join(skills_dir, skill, "SKILL.md")
        files = [md] + [os.path.join(ROOT, e) for e in extras]
        fresh = 0
        for f in files:
            b = size(f)
            fresh += b
            loaded_once[f] = loaded_once.get(f, 0) + b
        grand += fresh
        print(f"{phase:42} {fresh/4:>10,.0f} {grand/4:>12,.0f}")
    print("-" * 68)
    print(f"{'ONE-FULL-PIPELINE fresh skill-load total':42} {grand/4:>11,.0f}")
    print()
    print("NOTE: session-cumulative column approximates how much skill text has")
    print("entered the context by that phase if every phase ran in ONE session")
    print("(it does not count conversation/tool history, which is the dominant")
    print("term — see docs/TOKEN-OPTIMIZATION.md).")


if __name__ == "__main__":
    main()
