# zt-rhaibu — OODA Workshop Factory

> **DEPRECATED (2026-11-10):** this factory is superseded by `~/git/ph-rhaibu/`,
> which produces publishing-house format workshops (one `ph-<slug>/` repo per
> workshop instead of separate rac/showroom/automation repos). Migration runbook:
> `ph-rhaibu/skills/docs/PH-MIGRATION-RUNBOOK.md`. Keep this repo for reference only.

Workshop creation pipeline based on the OODA loop. Each phase is a skill in `skills/`.

## Pipeline

```
Observe → Orient → Do → Quality → Act → Publish
(images)   (RAC)   (code) (enrich)  (deploy+test)  (PR to p-zero-lessons)
```

**Each workshop gets its own RAC repo** at `~/git/zt-<slug>-rac/` — the planning contract between phases.

| Phase | Skill | Input | Output |
|-------|-------|-------|--------|
| Observe | `workshop-observe` | Demo screenshots/keyframes | `~/git/zt-<slug>-rac/assets/observations-<slug>.md` |
| Orient | `workshop-orient` | Observation doc or freeform | `~/git/zt-<slug>-rac/requirements/`, `decisions/`, `designs/` |
| Do | `workshop-do` | RAC artifacts | `~/git/zt-<slug>-showroom/` + `~/git/zt-<slug>-automation/` |
| Act | `workshop-act` | Scaffolded repos + RAC requirements | Deployed workshop on prelude cluster |
| Publish | `workshop-act` (step 8) | Validated showroom content | PR into `p-zero-lessons/lessons/<slug>/` |
| Quality | `quality-enrichment` | Enriched workshops + RAC + code repos | Per-workshop quality report + content fixes |

Two working repos per workshop: `zt-<slug>-rac/` and `zt-<slug>-showroom/`.
Finished content is contributed to **`https://github.com/red-hat-ai-dev/p-zero-lessons`** as `lessons/<slug>/`.
The `zt-<slug>-automation/` deploy repo is used during Act for cluster testing only — it is not the publish target.

### p-zero-lessons repo structure

```
p-zero-lessons/
  antora-playbook.yml   ← global build; add a content source per lesson
  home/                 ← hub landing page (nav.adoc + index.adoc); update per lesson
  supplemental-ui/      ← shared RHDP theme assets
  lib/inject-buttons.js ← shared Antora extension
  lessons/<slug>/       ← one directory per workshop
    content/
      antora.yml        ← name: <slug>  (NOT "modules")
      ...
```

Merging to `main` auto-triggers `.github/workflows/gh-pages.yml` → deploys to
`https://red-hat-ai-dev.github.io/p-zero-lessons/`. Each lesson is a named Antora
component; the hub `home` component links them all in the sidebar.
This factory repo (`zt-rhaibu`) holds only skills and tooling — no per-workshop state. Pipeline changes are developed in branches of this repo.

## Exemplar Repos

- **Content**: https://github.com/rhpds/ai-lightning-wordswarm-showroom — Antora/AsciiDoc showroom pattern
- **Infra**: `zt-showroom-deployer` Helm chart (source at `~/git/zt-showroom-deployer/`, published as `eformat/showroom-deployer` at https://eformat.github.io/helm-charts) — the per-workshop `zt-<slug>-automation` repo is a thin `values-<slug>.yaml` + `Makefile` wrapper around it (no ArgoCD app-of-apps)

## Skill Coordination

- **openshift-workshop-builder** — handles Antora/showroom content scaffolding (called by workshop-do)
- **playwright-cli** — browser automation for testing (called by workshop-act)
- **openshift-4-21-expert** — OpenShift console flows and cluster admin steps
- **openshift-ai-3-3-expert** — RHOAI workbenches, model serving, pipelines
- **verify-content** (`/verify-content`) — validates showroom content against Red Hat quality standards; quality gate in workshop-act. Vendored from the RHDP skills marketplace and registered as a slash command.
- **catalog-builder** (`/catalog-builder`) — builds an RHDP AgnosticV catalog entry at publish time. Vendored from the RHDP skills marketplace and registered as a slash command.
- **quality-enrichment** (`/quality-enrichment`) — audits and uplifts bulk-scaffolded workshops in the ralf-wiggum monorepo. Validates RAC coverage, audits screenshots, enriches with code from companion repos (`red-hat-ai-examples`, `trustyai-llm-demo`, etc.), and fixes content quality defects. Operates post-enrichment, before Act.

## RAC

Requirements As Code via [`asdecided-core`](https://github.com/asdecided/core/releases). Assumes `decided` is on PATH.

Artifact ID prefix: `RHAIBU-`. Key CLI commands: `decided schema`, `decided new`, `decided validate`, `decided review`, `decided relationships`.

Each workshop's RAC lives in its own repo (`~/git/zt-<slug>-rac/`), not in this factory repo.
Skills scaffold the RAC repo with `decided init --key RHAIBU` during Observe/Orient.

In the workshop RAC a full set of folders could include:

```bash
mkdir -p ~/git/zt-<slug>-rac/assets rac/decisions ~/git/zt-<slug>-rac/designs ~/git/zt-<slug>-rac/prompts ~/git/zt-<slug>-rac/requirements ~/git/zt-<slug>-rac/roadmaps
```

## Future

Skills will integrate with hermes kanban for independent step/stage processing with LLM-as-judge validation.
