---
name: workshop-observe
description: >
  Phase 1 of the OODA workshop pipeline (Observe): analyze demo screenshots/keyframes
  into a factual observation document in the RAC repo. Triggers: "workshop observe",
  "observe demo", "analyze screenshots", "keyframes", "extract features".
  Do NOT use for general image analysis unrelated to workshop planning.
triggers:
  keywords:
    - "workshop observe"
    - "observe demo"
    - "analyze screenshots"
    - "keyframes"
    - "demo analysis"
    - "workshop observation"
    - "extract features"
    - "ooda observe"
  matchMode: any
enabled: true
---

# Workshop Observe

Analyze demo application visuals to produce a structured observation document that
feeds the Orient step of the OODA workshop pipeline.

See `skills/docs/WORKSHOP-COMMON-RULES.md` for shared AsciiDoc, image, security,
and quality rules — including §7a subagent isolation: for large screenshot sets,
batch per-image analysis in a subagent that returns only the "Screenshots
Analyzed" table (one row per image); the main agent does the flow reconstruction
and writes the observation document itself.

## Goal

Turn a set of demo screenshots or keyframes into a factual observation document in
the workshop's RAC repo that captures what the demo does, what technologies it uses,
what user flows it demonstrates, and what concepts it could teach.

## Prerequisites

Check these before starting. If any are missing, print what's needed and stop.

**Required tools:**
- `git` — for initializing the RAC repo
- `decided` CLI — `decided --version` ([install](https://github.com/asdecided/core/releases))

**Required inputs:**
- Images provided by the user — file paths, a directory of screenshots, or inline images
- A workshop slug (ask the user if not provided) — used to derive the RAC repo path

## Workflow

### 1. Collect inputs

Accept `$ARGUMENTS` as either:
- A space-separated list of image file paths
- A directory path containing screenshots (scan for `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`)
- If no arguments provided, ask the user for image paths

Sort images alphabetically or by any numeric prefix to establish viewing order.

### 1a. Initialize the RAC repo

Each workshop gets its own RAC repo at `~/git/zt-<slug>-rac/`. If it does not exist:

```bash
mkdir -p ~/git/zt-<slug>-rac/assets
cd ~/git/zt-<slug>-rac
git init
decided init --key RHAIBU
```

Copy input images into `~/git/zt-<slug>-rac/assets/` so observations and source
images live together.

### 2. Analyze each image

Read each image file. For every screenshot, extract:

- **Page identity** — what screen is this? (login page, dashboard, settings panel, terminal, notebook, model serving page, etc.)
- **Product indicators** — which product/technology is shown? Look for: OpenShift console chrome, RHOAI dashboard, Jupyter notebook interface, VS Code, terminal prompts, ArgoCD UI, Grafana, specific logos or branding
- **UI components** — forms, tables, charts, navigation elements, modals, sidebars, code editors, terminal output
- **Data visible** — model names, metrics, API endpoints, code snippets, configuration values, status indicators
- **User action implied** — what was the user doing or about to do? (deploying a model, running inference, configuring a pipeline, viewing results)

### 3. Reconstruct user flows

Order the screenshots into logical sequences. Identify:

- The **primary happy path** — the main flow from start to finish
- **Branch points** — where different choices lead to different screens
- **Prerequisites** for each step (must be logged in, must have model deployed, etc.)
- **Gaps** — missing steps where a screenshot would be expected but is absent

Number each flow step and reference the source screenshot filename.

### 4. Identify teachable concepts

Map observations to concepts grouped by domain:

- **OpenShift platform** — routes, deployments, operators, security context constraints, projects/namespaces, RBAC
- **RHOAI / AI platform** — workbenches, model serving (KServe, ModelMesh), data science pipelines, model registry, accelerator profiles
- **AI/ML fundamentals** — inference, fine-tuning, prompt engineering, benchmarking, guardrails, RAG
- **Developer workflows** — git operations, CI/CD, container builds, API testing, CLI tools

Only list concepts that are directly evidenced in the screenshots.

### 5. Write the observation document

Create `~/git/zt-<slug>-rac/assets/observations-<slug>.md`. Use this structure:

```markdown
# Observations: <Demo Name>

## Summary

One paragraph describing what the demo application does, based on the screenshots.

## Screenshots Analyzed

| # | Filename | Page Identity | Key Observations |
|---|----------|---------------|------------------|
| 1 | screenshot-01.png | Login page | OpenShift console login with ... |
| 2 | screenshot-02.png | Dashboard | RHOAI dashboard showing ... |

## User Flows

### Flow 1: <Primary Flow Name>

1. **Login** (screenshot-01.png) — User logs into OpenShift console
2. **Navigate to RHOAI** (screenshot-02.png) — Opens the AI dashboard
3. ...

### Flow 2: <Secondary Flow Name> (if applicable)

1. ...

## Features and Concepts

### OpenShift Platform
- ...

### RHOAI / AI Platform
- ...

### AI/ML Fundamentals
- ...

### Developer Workflows
- ...

## Workshop Potential

- **Estimated modules**: N (based on flow complexity)
- **Target audience**: <role and experience level>
- **Prerequisite knowledge**: <what learners should already know>
- **Estimated duration**: <total workshop time>
- **Cluster requirements**: <operators, GPUs, storage, etc.>

## Open Questions

- <things that could not be determined from screenshots alone>
- <ambiguous UI states or missing context>
```

### 6. Report and handoff

Print a summary:
- Number of screenshots analyzed
- Number of user flows identified
- Number of teachable concepts extracted
- Path to the observation document

Prompt: "Observations complete. Run `/workshop-orient` to plan the workshop from these observations."

## Guardrails

- Do not invent features not visible in the screenshots. If something is ambiguous, list it under Open Questions.
- Do not assume the technology stack — identify it from visual cues (logos, console chrome, URL patterns, page layouts).
- If screenshots are low quality or unreadable, ask the user for better versions rather than guessing.
- Keep the observation document factual and descriptive. Save opinions, recommendations, and workshop structure decisions for the Orient step.
- Never embed base64 image data in the observation document. Reference images by file path only.
- If the screenshots show multiple unrelated demos, ask the user to clarify scope before proceeding.

## Out of scope

- Writing workshop content or AsciiDoc pages — that is `workshop-do`
- Planning the workshop structure or creating RAC requirements — that is `workshop-orient`
- Deploying or testing anything — that is `workshop-act`
- General image analysis unrelated to workshop creation

## Related Skills

- `/workshop-orient` — Plan the workshop from these observations
- `/workshop-screenshot` — Capture screenshots from a live cluster
