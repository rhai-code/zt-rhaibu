# ⚠️ DEPRECATED — moved to `ph-rhaibu`

> **This repo is deprecated.** The OODA Workshop Factory now lives in
> **[`ph-rhaibu`](https://github.com/eformat/ph-rhaibu)** and produces
> **publishing-house format** workshops: ONE repo per workshop (`ph-<slug>/`) holding
> planning (`rac/` + `publishing-house/`), content (`content/`), automation
> (`automation/`), and QA (`qa-automation/`) — instead of the separate
> `zt-<slug>-rac` / `zt-<slug>-showroom` / `zt-<slug>-automation` repos this
> factory used to generate.
>
> **Do not run new workshops through this pipeline.** Use `/workshop-observe`,
> `/workshop-orient`, `/workshop-do`, `/workshop-act` from `ph-rhaibu`.
> Migrating an existing `zt-*` workshop: see `ph-rhaibu/skills/docs/PH-MIGRATION-RUNBOOK.md`.
> Reference publishing-house repos: `ph-deploy-configure-rhoai`, `ph-operations-rhoai`,
> `redhat-ai-inference`.

# zt-rhaibu

OODA Workshop Factory -- a skill-driven pipeline for building OpenShift/RHOAI workshops from demo observations through to deployed, tested content.

![OODA Workshop Factory Pipeline](images/ooda-workshop-factory.svg)

## How it works

Each workshop follows the OODA loop. Run the skills in order -- and loop back when things need fixing.

| Phase | Skill | What happens |
|-------|-------|-------------|
| **Capture** | _manual_ | Record a demo video, `ffmpeg` split to keyframes |
| **Observe** | `/workshop-observe` | Analyze screenshots, extract user flows, write observations to RAC repo |
| **Orient** | `/workshop-orient` | Interview for requirements, create RAC artifacts (requirements, decisions, designs), validate |
| **Do** | `/workshop-do` | Scaffold showroom content + automation infra repos, `make build`, `helm lint`, `decided validate` |
| **Act** | `/workshop-act` | Deploy to prelude cluster (`helm upgrade --install`), Playwright browser tests, fix-and-test loop |
| **Loop Back** | _team review_ | Gaps? Re-Observe. Scope change? Re-Orient. Content fix? Re-Do. All green? Ship it. |

Standalone skills.

| Phase | Skill | What happens |
|-------|-------|-------------|
| **Screenshot** | `/workshop-screenshot` | Capture live screenshots from cluster, embed `image::` refs in AsciiDoc, write RAC evidence |
| **Quality** | `/quality-enrichment` | Audit and uplift workshop quality: validate RAC coverage, audit screenshots, enrich with real code from companion repos, fix content defects |

## Quick start

Install [asdecided-core](https://github.com/asdecided/core/releases) and ensure `decided` is on your PATH.

```bash
git clone <this-repo>
cd zt-rhaibu
```

Record your demo video e.g. `zt-workbench-create.mkv`

Create screenshots from your demo video as keyframes:

```bash
ffmpeg -i ~/Videos/zt-workbench-create.mkv \
  -vf "thumbnail=120,setpts=N/TB" \
  -vsync vfr rac/assets/keyframe-%03d.png
```

Then open Claude Code and run:

```bash
/workshop-observe <path-to-screenshots>
```

The skills will guide you through each of the other skills. Each skill will stop for human in the loop check-fix and ask questions as needed.

## Three repos per workshop

3 repos are generated once you have been through the OODA loop.

```
~/git/zt-<slug>-rac/          # planning (Requirements As Code)
~/git/zt-<slug>-showroom/     # content (Antora/AsciiDoc)
~/git/zt-<slug>-automation/   # infrastructure (thin Helm wrapper: values-<slug>.yaml + Makefile)
```

This factory repo holds only skills and tooling -- no per-workshop state.

## Skills

Here are descriptions of the skills.

### Pipeline skills

Main pipeline

| Skill | Purpose |
|-------|---------|
| `workshop-observe` | Analyze demo screenshots into structured observations |
| `workshop-orient` | Plan the workshop with RAC artifacts |
| `workshop-do` | Scaffold content and infrastructure code |
| `workshop-act` | Deploy, test, and validate on a cluster |

Standalone skills

| Skill | Purpose |
|-------|---------|
| `workshop-screenshot` | Capture live screenshots from a cluster and embed them into AsciiDoc content |
| `quality-enrichment` | Audit and uplift workshop quality: validate RAC coverage, audit screenshots, enrich with code from companion repos, fix content defects (single-workshop or monorepo mode) |

### Domain skills

| Skill | Purpose |
|-------|---------|
| `openshift-workshop-builder` | Antora/showroom content scaffolding patterns |
| `openshift-4-21-expert` | OpenShift console flows and cluster admin |
| `openshift-ai-3-3-expert` | RHOAI workbenches, model serving, pipelines |
| `playwright-cli` | Browser automation for testing |
| `/verify-content` | Validate showroom content against Red Hat quality standards (vendored from RHDP marketplace) |
| `/catalog-builder` | Build an RHDP AgnosticV catalog entry when ready to publish (vendored from RHDP marketplace) |

`verify-content` and `catalog-builder` are vendored into this repo and registered as
slash commands (`/verify-content`, `/catalog-builder`); the other domain skills are
reference-only patterns invoked by the pipeline skills.

## Diagram source

The pipeline diagram is a Mermaid journey chart: [`docs/ooda-workshop-factory.mdd`](docs/ooda-workshop-factory.mdd)

Rebuild with:

```bash
npx @mermaid-js/mermaid-cli -i docs/ooda-workshop-factory.mdd -o images/ooda-workshop-factory.svg -b white
```
