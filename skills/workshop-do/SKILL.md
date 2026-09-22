---
name: workshop-do
description: >
  Phase 3 of the OODA workshop pipeline (Do): scaffold zt-<slug>-showroom (Antora/AsciiDoc
  content) and zt-<slug>-automation (thin Helm wrapper) from RAC requirements. Triggers:
  "workshop do", "scaffold workshop", "showroom scaffold", "workshop implementation".
  Do NOT use for demos (workshop-observe), planning (workshop-orient), deploy/test (workshop-act).
triggers:
  keywords:
    - "workshop do"
    - "scaffold workshop"
    - "workshop content"
    - "workshop infrastructure"
    - "showroom scaffold"
    - "workshop implementation"
    - "ooda do"
    - "generate workshop"
  matchMode: any
enabled: true
---

# Workshop Do

Scaffold two codebases from RAC requirements: a content repo and an infrastructure repo.

## Skill coordination

- **Delegate content scaffolding** to the `openshift-workshop-builder` skill (Antora/showroom
  structure, templates, AsciiDoc patterns, build); use **openshift-4-21-expert** for
  OpenShift lab steps and **openshift-ai-3-3-expert** for RHOAI lab steps.
- Reference `https://github.com/rhpds/ai-lightning-wordswarm-showroom` as the content exemplar.
- The infrastructure repo is a thin **Helm CLI wrapper** around the reusable
  `zt-showroom-deployer` chart (source at `~/git/zt-showroom-deployer/`). The chart value
  contract, showroom pod anatomy, and wrapper layout are documented in
  `${CLAUDE_SKILL_DIR}/references/infra-patterns.md`.
- See `skills/docs/WORKSHOP-COMMON-RULES.md` for shared AsciiDoc, image, security,
  and quality rules — including §7a subagent isolation: delegate the high-traffic
  steps here (per-module content drafting with the expert skills, exemplar-repo
  reads, `npm install`/`make build` output) to subagents and keep only file
  lists + build pass/fail in the main conversation.

## Prerequisites

Check these before starting. If any are missing, print what's needed and stop.

**Required tools:**
- `git` — `git --version`
- `node` / `npm` — `node --version && npm --version` (for Antora build)
- `helm` — `helm version --short` (for chart validation)
- `decided` CLI — `decided --version` ([install](https://github.com/asdecided/core/releases))

**Required exemplar repos** (clone if missing):
- Content exemplar: `https://github.com/rhpds/ai-lightning-wordswarm-showroom`
  ```bash
  git clone https://github.com/rhpds/ai-lightning-wordswarm-showroom.git https://github.com/rhpds/ai-lightning-wordswarm-showroom
  ```

**Required chart:**
- The reusable `zt-showroom-deployer` Helm chart. The infra repo references it either from
  a published Helm repo (the user's chart repo) or a local path fallback to
  `~/git/zt-showroom-deployer/`. Have the published chart repo URL ready; if unknown, fall
  back to the local path.

**Required state:**
- A workshop RAC repo at `~/git/zt-<slug>-rac/` (from workshop-orient) containing:
  requirements with acceptance criteria, decisions, and at least one design with a
  parameter inventory

## Workflow

### 1. Read RAC requirements

Accept `$ARGUMENTS` as a workshop slug. If no argument is provided, discover
existing RAC repos:

```bash
ls -d ~/git/zt-*-rac/ 2>/dev/null
```

If exactly one exists, use it. If multiple exist, list them and ask the user to
choose. If none exist, stop — workshop-orient must be run first.

The RAC repo is at `~/git/zt-<slug>-rac/`.
Read all requirement artifacts from `~/git/zt-<slug>-rac/requirements/`. Extract:
- Module list with ordering
- Acceptance criteria per module
- Parameter inventory from the design artifact
- Infrastructure requirements (operators, CRDs, GPUs, storage)

### 2. Determine output locations

Create two sibling repos in `~/git/`:
- Content: `~/git/zt-<slug>-showroom/`
- Infra: `~/git/zt-<slug>-automation/`

Confirm the slug and output paths with the user before creating directories.

### 3. Scaffold the content repo

Follow the `openshift-workshop-builder` workflow to create the showroom structure:

**Required files** (all must exist for `make build` to succeed):

- `package.json` — Antora dependencies (`@antora/cli`, `@antora/site-generator`)
- `Makefile` — use this exact template (matches `zt-workbench-create-showroom`):
    ```makefile
    PORT ?= 8887
    DOCS_DIR := $(shell pwd)
    SITE_DIR := $(DOCS_DIR)/www

    .PHONY: install build serve clean

    install:
    	cd $(DOCS_DIR) && npm install

    build: install
    	rm -rf $(SITE_DIR)
    	cd $(DOCS_DIR) && npx antora site.yml --stacktrace
    	touch $(SITE_DIR)/.nojekyll

    serve: build
    	@echo "Serving at http://localhost:$(PORT)"
    	python3 -m http.server $(PORT) --directory $(SITE_DIR)

    clean:
    	rm -rf $(SITE_DIR)
    ```
    Key rules: port 8887 (not 8080), output to `www/` (not `docs/`), call `npx antora`
    directly (not via `npm run`), `rm -rf` before each build for clean output,
    `python3 -m http.server` for serve, `.nojekyll` required for GitHub Pages.
- `site.yml` — Antora playbook. MUST use the RHDP theme bundle — never the Antora
    default. Copy this block exactly:
    ```yaml
    ui:
      bundle:
        url: https://github.com/rhpds/rhdp_showroom_theme/releases/download/summit-2026/ui-bundle.zip
        snapshot: true
      supplemental_files: ./content/supplemental-ui
    asciidoc:
      attributes:
        showroom-collection-version: v1.5.2
    antora:
      extensions:
        - require: ./content/lib/inject-buttons.js
    output:
      dir: ./www
    ```
    Output MUST be `./www` — the gh-pages workflow uploads `path: www`, and the
    Makefile `SITE_DIR` must match.
- `content/antora.yml` — component descriptor with all `{attribute}` defaults from
  the RAC parameter inventory. MUST include these three attributes or the RHDP theme
  will not generate Prev/Next pagination:
  ```yaml
  asciidoc:
    attributes:
      source-highlighter: highlight.js
      experimental: true
      page-pagination: true
  ```
  Also MUST use `version: ~` (not a pinned version like `'1.0'`) — a versioned
  component disables the theme's pagination nav.
- `content/modules/ROOT/nav.adoc` — navigation tree with entries for each module
- `.gitignore` — exclude `node_modules/`, `www/`, `.cache/` (not `docs/` — output is `www/`)
- `content/supplemental-ui/css/site-extra.css` — image shadow + send-to button styles
- `content/supplemental-ui/js/buttons.js` — send-to-terminal JS
- `content/supplemental-ui/img/favicon.svg` — Red Hat favicon
- `content/supplemental-ui/partials/head-meta.hbs` — injects CSS + Font Awesome
- `content/supplemental-ui/partials/head-icons.hbs` — favicon link
- `content/lib/inject-buttons.js` — Antora extension (inlines CSS/JS per page)

  **Copy** `content/supplemental-ui/` and `content/lib/` from an existing workshop
  showroom (e.g., `~/git/zt-workbench-create-showroom/`) — do not recreate from
  scratch and do not use a generic Antora UI bundle.

**Content pages** under `content/modules/ROOT/pages/`:

- `index.adoc` — welcome page with: title, what you'll learn, who this is for,
  prerequisites, estimated time, link to first module
- `getting-connected.adoc` — login steps using `{user}` / `{password}` attributes,
  project setup, environment verification
- `NN-module-MM-<slug>.adoc` — one page per module requirement, with:
  - `:navtitle:` and `:toc: macro` attributes
  - `== Learning objectives` section (bulleted list from RAC requirement)
  - Numbered `== Exercise N: Title` sections with `[source,role="execute"]` code blocks
  - `=== Verify` section after each exercise
  - `== Module summary` with key takeaways
- `NN-conclusion.adoc` — wrap-up with per-module summary, resources, thank you

**AsciiDoc rules:**
- Every command uses `[source,role="execute"]` for the Showroom copy/execute button
- Use `[source,bash,role="execute",subs="attributes"]` for blocks containing `{attribute}` values
- Use `{attribute}` substitution for all environment-specific values — never hardcode
- Page naming: `NN-descriptive-name.adoc` with 2-digit prefix for ordering

**Optional files** (add if the workshop needs interactive features):
- `ui-config.yml` — showroom tabs and terminal configuration

**Always include** (copy from exemplar `gpu-resource-mgmt-showroom`):
- `.github/workflows/gh-pages.yml` — GitHub Pages CI/CD. Triggers on pushes to
  `content/**`, `site.yml`, or the workflow file itself. Builds with Antora (Node 22),
  overrides the UI bundle to the `showroom-template` release for gh-pages rendering,
  uploads `www/` as the pages artifact, and deploys on merge to `main`. PRs run the
  build step only (no deploy). Copy verbatim — do not recreate.

### 4. Initialize content repo and test build

```bash
cd ../zt-<slug>-showroom
git init && git add -A && git commit -m "Initial workshop scaffold"
npm install
make build
```

Verify the build succeeds. Antora requires at least one git commit — without it the
site builds but contains zero pages. If the build fails, fix errors and retry.

### 5. Scaffold the infrastructure repo

Read `${CLAUDE_SKILL_DIR}/references/infra-patterns.md` for the chart value contract and
wrapper layout.

The infra repo is a **thin Helm CLI wrapper** around the published `zt-showroom-deployer`
chart — no ArgoCD, no app-of-apps, no operator/DataScienceCluster/tenant layers. Scope is
**showroom-only**: it deploys the showroom content pod onto an already-provisioned cluster.

```
zt-<slug>-automation/
  README.md
  Makefile              ← helm repo add + helm upgrade --install ... -f values-<slug>.yaml
  values-<slug>.yaml    ← per-workshop values for the showroom-deployer chart
  .gitignore
```

**`Makefile`** — targets driving `helm` against the chart. `CHART` selects the published
repo (default) or a local path fallback to `~/git/zt-showroom-deployer`:

```makefile
SLUG        ?= <slug>
NAMESPACE   ?= showroom-$(SLUG)
RELEASE     ?= showroom
VALUES      ?= values-$(SLUG).yaml
# Published chart ref; override CHART=~/git/zt-showroom-deployer for local source.
CHART_REPO_NAME ?= eformat
CHART_REPO  ?= https://eformat.github.io/helm-charts
CHART       ?= $(CHART_REPO_NAME)/showroom-deployer

.PHONY: repo template deploy status uninstall

repo:
	helm repo add $(CHART_REPO_NAME) $(CHART_REPO) || true
	helm repo update $(CHART_REPO_NAME)

template:
	helm template $(RELEASE) $(CHART) -n $(NAMESPACE) -f $(VALUES)

deploy:
	helm upgrade --install $(RELEASE) $(CHART) \
	  -n $(NAMESPACE) --create-namespace -f $(VALUES)

status:
	helm status $(RELEASE) -n $(NAMESPACE)

uninstall:
	helm uninstall $(RELEASE) -n $(NAMESPACE)
```

**`.gitignore`** — exclude `*.tgz`, `charts/`, and any rendered output.

### 6. Populate values-<slug>.yaml

Fill the per-workshop values for the `zt-showroom-deployer` chart. Everything not set here
inherits the chart defaults. Set at least:

- `showroom.gitRepoUrl` — the GitHub URL of the `zt-<slug>-showroom` content repo created in
  Step 3/4 (and `showroom.gitRepoRef`, usually `main`).
- `deployer.domain` / `deployer.apiUrl` — the target cluster's apps domain and API URL.
- `showroom.namespace` — target namespace (matches the Makefile `NAMESPACE`).
- `showroom.guid` / `showroom.user` / `showroom.password` / `showroom.projectName` — lab identity.
- `showroom.wetty.sshHost` / `sshPort` / `sshUser` / `sshAuth` / `sshPass` — web terminal SSH
  coordinates (these are cluster/environment-specific; leave placeholders if unknown at
  scaffold time and fill during workshop-act).
- `showroom.images.*` and `showroom.ztBundle` — pin the runtime image and bundle versions.

Do **not** hardcode cluster values in the chart — they live only in `values-<slug>.yaml`.

### 7. Validate and report

```bash
decided validate ~/git/zt-<slug>-rac/

# Render the infra wrapper against the chart (no cluster needed):
cd ~/git/zt-<slug>-automation && make template CHART=~/git/zt-showroom-deployer
```

Confirm requirements still pass and the chart renders cleanly. Print a summary:
- Files created in content repo (count by type: .adoc, .yaml, .json, .yml)
- Files created in infra repo (`Makefile`, `values-<slug>.yaml`, `README.md`, `.gitignore`)
- Content build status (pass/fail)
- `helm template` render status against `zt-showroom-deployer` (pass/fail)

Prompt: "Workshop scaffolded. Run `/workshop-act` to deploy and test on the prelude cluster."

## Guardrails

- Never hardcode cluster-specific values in content. Use `{attribute}` substitution.
- Never hardcode cluster-specific values in infra. They live only in `values-<slug>.yaml`,
  fed to the `zt-showroom-deployer` chart.
- Follow the `openshift-workshop-builder` patterns exactly for content structure.
- Keep the infra repo a thin Helm wrapper — do not re-scaffold operators, DataScienceCluster,
  tenant layers, or an ArgoCD app-of-apps. The chart owns what gets deployed.
- Every command in a module must use `[source,role="execute"]` blocks.
- Initialize git before running `make build` — Antora requires at least one commit.
- Do not create screenshots — that requires a running cluster and is deferred to
  `workshop-act`.

## Out of scope

- Screenshot capture (requires a running cluster — deferred to workshop-act)
- Deployment to a cluster (workshop-act)
- Workshop planning or requirement gathering (workshop-orient)
- Analyzing demo applications (workshop-observe)

## Related Skills

- `/workshop-orient` — Plan the workshop and create RAC requirements
- `/workshop-act` — Deploy and test the workshop end-to-end
- `/workshop-screenshot` — Capture and embed screenshots into content
- `/openshift-workshop-builder` — AsciiDoc/Antora scaffolding patterns
- `/verify-content` — Validate content against Red Hat quality standards
