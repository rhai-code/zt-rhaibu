---
name: workshop-orient
description: >
  Phase 2 of the OODA workshop pipeline (Orient): plan a workshop as RAC artifacts
  (requirements, decisions, designs) via the decided CLI. Triggers: "workshop orient",
  "workshop plan", "workshop requirements", "workshop design", "rac workshop".
  Do NOT use for writing content (workshop-do) or deploying (workshop-act).
triggers:
  keywords:
    - "workshop orient"
    - "workshop plan"
    - "workshop requirements"
    - "workshop design"
    - "orient workshop"
    - "ooda orient"
    - "rac workshop"
    - "workshop scope"
  matchMode: any
enabled: true
---

# Workshop Orient

Plan a workshop by producing machine-validatable RAC artifacts that serve as the
contract between planning and implementation.

## Skill coordination

- Follow the **`decided-capture`** skill's approach for artifact creation — interview the
  user and propose, the human ratifies, `decided validate` closes.
- Follow the **`decided-review`** skill's approach for validation — work findings
  worst-first until validation and relationship checks pass. (`decided-artifacts` covers
  authoring/linking conventions.)
- Use `decided schema <type>` to get real artifact schemas. Never invent fields or sections.
- **Subagent isolation (WORKSHOP-COMMON-RULES §7a):** schema dumps and long
  `decided validate`/`review` output are high-traffic — run them in a subagent and
  keep only the finding list in the main conversation. Never delegate the
  ratification interview itself.
- See `skills/docs/WORKSHOP-COMMON-RULES.md` for shared AsciiDoc, image, security,
  and quality rules.

## Prerequisites

Check these before starting. If any are missing, print what's needed and stop.

**Required tools:**
- `git` — for RAC repo management
- `decided` CLI — `decided --version` ([install](https://github.com/asdecided/core/releases))

**Optional helper skills:** `decided-capture` / `decided-review` / `decided-artifacts` live
in asdecided-core (`~/git/asdecided-core/.claude/skills/`). They're convenience wrappers over
the same `decided` CLI — this workflow works with just the `decided` CLI on PATH if they
aren't loaded.

**Required state:**
- A workshop RAC repo at `~/git/zt-<slug>-rac/` with `.decided/config.yaml`
  (created by workshop-observe, or run `decided init --key RHAIBU` if not)
- An observation document in the RAC repo's `assets/` directory (from workshop-observe)
  or freeform input

## Workflow

### 1. Initialize RAC (if needed)

Determine the workshop slug from `$ARGUMENTS`. If no argument is provided, discover
existing RAC repos:

```bash
ls -d ~/git/zt-*-rac/ 2>/dev/null
```

If exactly one exists, use it. If multiple exist, list them and ask the user to
choose. If none exist, ask the user for the slug.

The RAC repo lives at `~/git/zt-<slug>-rac/`. All `decided` commands in this workflow
run from that directory.

If the RAC repo does not exist (workshop-observe was not run first):

```bash
mkdir -p ~/git/zt-<slug>-rac/assets
cd ~/git/zt-<slug>-rac
git init
decided init --key RHAIBU
```

If the repo exists, check for `.decided/config.yaml` and initialize if missing.

### 2. Read observations

Look for observation documents in `~/git/zt-<slug>-rac/assets/observations-*.md`.
If found, read and extract: user flows, features, concepts, target audience,
estimated module count. If no observation document exists, accept `$ARGUMENTS` as
inline text describing the workshop concept and interview the user to establish the same.

### 3. Read the real schemas

Before creating any artifact, read the schema for each type you will use:

```bash
decided schema requirement
decided schema decision
decided schema design
```

Use only the section names, frontmatter fields, and controlled values these schemas
define. Never guess or hard-code a field the schema does not list.

**Frontmatter restriction:** `decided new` scaffolds the correct frontmatter fields
(`schema_version`, `id`, `type`). Do not add extra fields like `status` or `category`
to the YAML frontmatter — those are body-level metadata sections (e.g., `## Status`),
not frontmatter keys. The only supported frontmatter fields are: `schema_version`,
`id`, `type`, `relationships`, `tags`.

### 4. Create the workshop-level requirement

Scaffold with `decided new`, then Read the scaffold, then Write the populated content:

```bash
cd ~/git/zt-<slug>-rac
decided new requirement requirements/<workshop-slug>.md
```

After `decided new` creates the file, you MUST Read it before Writing content into it.
`decided new` writes a TODO-placeholder file to disk — Read it to satisfy the
Read-before-Write requirement, then Write the full content.

Fill in:
- **Title**: the workshop name
- **Description**: what the workshop teaches and who it is for
- **Requirements section**: testable acceptance criteria using MUST/SHOULD/MAY:
  - `[REQ-001] Learner MUST be able to log into the OpenShift console`
  - `[REQ-002] Learner MUST deploy a model to RHOAI model serving`
  - `[REQ-003] Learner SHOULD query the model via REST API`
- **Dependencies**: prerequisite knowledge, cluster requirements, operator versions

### 5. Create per-module requirements

For each workshop module identified in observations, scaffold a requirement:

```bash
cd ~/git/zt-<slug>-rac
decided new requirement requirements/<workshop-slug>-module-<N>.md
```

Each module requirement includes:
- Learning objectives (3-5 testable outcomes)
- Hands-on steps outline (ordered list of user actions)
- Estimated duration
- Required cluster state (what must be deployed/running before this module)
- Verification criteria (what the learner checks to confirm success)

Link each module to the parent workshop requirement using a `## Related Requirements`
section. Use bare artifact IDs only — one per line with a list marker. The relationship
resolver matches the full line text against the identifier index, so descriptive
suffixes break resolution:

```markdown
## Related Requirements

- RHAIBU-KXYZ1234ABCD
```

Do NOT write `- RHAIBU-KXYZ1234ABCD: Human Readable Title` — the title suffix
prevents asdecided-core from resolving the reference.

### 6. Create architectural decisions

For each significant technology choice, scaffold a decision:

```bash
cd ~/git/zt-<slug>-rac
decided new decision decisions/<topic-slug>.md
```

At minimum, create decisions for:
- **Content format** — Antora/AsciiDoc showroom (status: decided). Reference the exemplar at `https://github.com/rhpds/ai-lightning-wordswarm-showroom`.
- **Infrastructure approach** — deploy the showroom via the reusable `zt-showroom-deployer`
  Helm chart, wrapped per-workshop by a thin `values-<slug>.yaml` + `Makefile` in
  `zt-<slug>-automation` (status: decided). Showroom-only — no ArgoCD app-of-apps or
  operator/tenant layers. Chart source: `~/git/zt-showroom-deployer/` (published as
  `eformat/showroom-deployer`).

Add additional decisions only when the workshop requires them (e.g., model serving,
authentication, GPU allocation). Not every workshop needs all decision types.

Include `## Context`, `## Decision`, and `## Consequences` sections per the schema.
Link decisions to the requirements they satisfy using `## Related Requirements`
with bare artifact IDs (same format as requirement links — no descriptive suffixes).

### 7. Create the workshop design

```bash
cd ~/git/zt-<slug>-rac
decided new design designs/<workshop-slug>-architecture.md
```

Document:
- **Module flow** — which modules depend on which (ordered list or diagram)
- **Content repo structure** — mapping to the showroom exemplar (site.yml, antora.yml, pages)
- **Infrastructure requirements** — the showroom-deployer chart values (namespace, git repo,
  domain/apiUrl, wetty), plus any cluster-side resources the *content* assumes already exist
  (e.g. RHOAI operator, GPUs, storage) — the workshop infra deploys only the showroom, not
  those operators
- **Parameter inventory** — all `{attribute}` values needed in `content/antora.yml`:
  - `lab_name`, `user`, `password`, `guid`
  - `openshift_api_url`, `openshift_console_url`, `openshift_cluster_ingress_domain`
  - Workshop-specific URLs (model endpoints, dashboards, etc.)
- **Two-repo strategy** — content in `zt-<slug>-showroom/`, infra in `zt-<slug>-automation/`

Link the design to requirements and decisions using `## Related Requirements` and
`## Related Decisions` sections with bare artifact IDs.

### 8. Validate the corpus

Run validation and fix any findings:

```bash
decided validate ~/git/zt-<slug>-rac/
decided review ~/git/zt-<slug>-rac/
decided relationships ~/git/zt-<slug>-rac/ --validate
```

Work findings in priority order (blocking first, then advisory). Re-validate after
each fix. The work is done only when `decided validate` and
`decided relationships --validate` both exit 0.

### 9. Report and handoff

Print a summary table:

| ID | Type | Title | Path |
|----|------|-------|------|
| RHAIBU-REQ-001 | requirement | Workshop Overview | rac/requirements/... |
| RHAIBU-REQ-002 | requirement | Module 1: ... | rac/requirements/... |
| RHAIBU-DEC-001 | decision | Content Format | rac/decisions/... |
| RHAIBU-DES-001 | design | Workshop Architecture | rac/designs/... |

Prompt: "Workshop planning complete. Run `/workshop-do` to scaffold the content and
infrastructure code from these requirements."

## Guardrails

- Follow the asdecided-core artifact schemas exactly. Run `decided validate` after every artifact creation.
- Keep acceptance criteria testable and specific. "User understands X" is not testable. "User can run `oc get inferenceservice` and see a READY status" is testable.
- Do not skip decision artifacts — they capture tooling rationale and prevent re-litigation later.
- Reference exemplar repos by path when documenting decisions.
- Use the RHAIBU namespace prefix for all artifact IDs (handled by `decided new`).
- Human ratification is mandatory — present drafts and confirm type, title, and relationships with the user before writing to disk.
- Do not invent requirements the user did not express. Interview to fill gaps.

## Out of scope

- Writing workshop content or AsciiDoc pages — use `workshop-do`
- Analyzing screenshots — use `workshop-observe`
- Deploying or testing — use `workshop-act`
- Recording ownership, sprints, priorities, or due dates — those belong in a work tracker

## Related Skills

- `/workshop-observe` — Analyze demo screenshots for observations
- `/workshop-do` — Scaffold content and infrastructure from these requirements
