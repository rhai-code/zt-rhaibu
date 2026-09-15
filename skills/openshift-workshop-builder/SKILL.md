---
id: openshift-workshop-builder
name: OpenShift Workshop Builder
description: >
  Antora/AsciiDoc Showroom scaffolding patterns: directory structure, config templates,
  AsciiDoc authoring rules, build process. Invoked by workshop-do; not a pipeline phase
  itself. Triggers: "showroom", "antora scaffold", "lab module", "screenshot manifest".
triggers:
  keywords:
    - "workshop"
    - "lab steps"
    - "workshop builder"
    - "screenshot manifest"
    - "workshop scaffold"
    - "showroom"
    - "antora"
    - "lab module"
  matchMode: any
enabled: true
---

# OpenShift Workshop Builder

Build workshop content in **Red Hat Showroom** format — an Antora + AsciiDoc site with interactive features like copy-paste code blocks, send-to-terminal buttons, and split-screen console tabs.

Reference implementation: `https://github.com/rhpds/ai-lightning-wordswarm-showroom` — clone this repo and reference it for bootstrapping.

## Skill Coordination

- Use the **OpenShift 4.21 Expert** skill for OpenShift Container Platform 4.21 flows, console paths, cluster-admin steps, and version-specific product behavior.
- Use the **OpenShift AI 3.3 Expert** skill for Red Hat OpenShift AI 3.3 flows, workbenches, model serving, pipelines, and AI-specific administration.
- Use the **Playwright CLI** skill to log in, navigate the console, capture screenshots, and save debugging artifacts.
- See `skills/docs/WORKSHOP-COMMON-RULES.md` for shared AsciiDoc, image, security,
  and quality rules.

## Default Workflow

1. Identify the workshop product and persona.
2. Use the relevant OpenShift domain skill to draft the exact user flow and expected state for each step.
3. Scaffold the Showroom directory structure (see Showroom Structure below).
4. Write content as numbered AsciiDoc module pages under `content/modules/ROOT/pages/`.
5. Wire up navigation in `nav.adoc`.
6. Set workshop-specific attributes in `content/antora.yml`.
7. **Initialize the git repo and create an initial commit before building.** Antora uses git to discover content sources — a repo with no commits produces an empty site with no error (only a warn-level log: `No matching references found for content source entry`).
8. Capture screenshots with `playwright-cli` and place them in `content/modules/ROOT/assets/images/`.
9. Build and preview with `make serve`.

## Workshop Rules

- One Showroom repo per workshop. The repo root contains `site.yml`, `ui-config.yml`, `Makefile`, and a `content/` Antora component.
- All content is AsciiDoc (`.adoc`), never Markdown.
- Keep prose instructional and testable. Every lab step should map to a user action or a visible expected result.
- Use `[source,role="execute"]` for every command the learner should run. This enables the Showroom UI copy/execute button.
- Use `{attribute}` substitution for environment-specific values (URLs, usernames, passwords, cluster domains). Define defaults in `content/antora.yml` — the Showroom platform overrides them at deploy time.
- Use real screenshots only from the target product/version, not stock images or copied docs screenshots.
- Keep screenshot filenames deterministic so re-captures replace the same files.
- Store auth state and temporary browser artifacts outside version control.

### Prose Style Rules

Canonical text with AsciiDoc examples: `skills/docs/WORKSHOP-COMMON-RULES.md` §8
and `${CLAUDE_SKILL_DIR}/references/prose-style.md`. In one line each (check IDs
P.1–P.4 are used by verify-content):

**P.1 — Module summary** (REQUIRED): `== Module summary` with bold labels `**What you accomplished:**` (3 past-tense bullets), `**Key takeaways:**` (3 present-tense bullets), `**Next steps:**` (prose only).
**P.2 — Exercise transitions** (REQUIRED): ≥1 bridging sentence after `=== Verify` before the next `== Exercise`.
**P.3 — Workaround handling** (REQUIRED): NOTE/WARNING before the command → "This is expected." → one sentence why → command. Depth goes in `[%collapsible]`.
**P.4 — Admonition type** (REQUIRED): TIP=orientation/shortcuts, NOTE=non-determinism/friction, IMPORTANT=structural/safety/ordering, WARNING=destructive/irreversible.

### YAML/Config Callout Rules

Canonical text with examples: `${CLAUDE_SKILL_DIR}/references/yaml-callouts.md`.
**C.1 — YAML manifest callouts** (RECOMMENDED): applied manifests (`oc apply/create/process`) SHOULD get ≤5 one-sentence callouts on opaque fields; never on `role="execute"` blocks; skip trivial config or blocks the prose already explains.

---

## Showroom Structure

```text
<workshop-repo>/
  site.yml                              # Antora site config (title, URL, UI bundle, output)
  ui-config.yml                         # Showroom UI config (tabs, terminals, split view)
  Makefile                              # Build automation (install, build, serve, clean)
  package.json                          # Node dependencies (antora, extensions)
  .gitignore                            # Excludes node_modules/, www/, .cache/, etc.
  content/
    antora.yml                          # Component config (name, nav, attributes)
    modules/ROOT/
      nav.adoc                          # Sidebar navigation tree
      pages/
        index.adoc                      # Welcome / landing page
        00-guide.adoc                   # Background context (optional)
        01-overview.adoc                # Workshop overview
        getting-connected.adoc          # Environment setup
        02-module-01-<slug>.adoc        # First hands-on module
        03-module-02-<slug>.adoc        # Second hands-on module
        NN-conclusion.adoc              # Wrap-up and resources
      assets/images/
        *.png                           # Screenshots and diagrams
    supplemental-ui/                    # Custom UI overrides (optional)
      css/site-extra.css                # Extra styling
      js/buttons.js                     # Interactive button logic
      partials/
        head-meta.hbs                   # Custom head tags
        head-icons.hbs                  # Favicon
      img/
        favicon.svg
    lib/
      inject-buttons.js                 # Antora extension to inline JS/CSS (optional)
```

### Minimum Viable Scaffold

To produce a site that builds with `make serve`, the following files are **required**. All other files (supplemental-ui, lib, screenshots) are optional and can be added later.

1. `package.json` — Antora dependencies
2. `Makefile` — Build targets
3. `site.yml` — Antora playbook
4. `content/antora.yml` — Component descriptor with attributes
5. `content/modules/ROOT/nav.adoc` — At least one xref entry
6. `content/modules/ROOT/pages/index.adoc` — At least one content page
7. `.gitignore` — Exclude build artifacts
8. A git repo with **at least one commit** (Antora requires this)

### File Roles

- **`site.yml`** — Top-level Antora playbook. Sets site title, URL, content source, UI bundle, and output directory. Points to the `rhpds/rhdp_showroom_theme` UI bundle.
- **`ui-config.yml`** — Showroom platform configuration. Defines sidebar tabs (consoles, terminals), default panel width, and view mode (split/full).
- **`content/antora.yml`** — Antora component descriptor. Sets the component name, navigation source, and all `{attribute}` defaults used in `.adoc` pages (URLs, credentials, cluster domains).
- **`nav.adoc`** — Sidebar navigation. Uses `xref:` links grouped under dot-prefixed section headers.
- **`pages/*.adoc`** — Workshop content. Numbered prefix controls page ordering. Each page is a self-contained section or module.
- **`assets/images/`** — Screenshots and diagrams embedded with `image::filename.png[alt]`.
- **`supplemental-ui/`** — Optional CSS/JS overrides and Handlebars partials layered on top of the Showroom theme.

---

## Key Configuration Files

When scaffolding a new workshop, create **all** of the files below. Every file is required for `make serve` to work.

### package.json

```json
{
  "name": "workshop-slug",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "build": "antora site.yml --stacktrace"
  },
  "dependencies": {
    "@antora/cli": "^3.1",
    "@antora/site-generator": "^3.1"
  }
}
```

Replace `workshop-slug` with the workshop's kebab-case name.

### .gitignore

```gitignore
.DS_Store
node_modules/
www/
.cache/
*.log
*.tmp
.env
.env.local
.env.*.local
package-lock.json
```

### site.yml

```yaml
site:
  title: "Workshop Title"
  url: https://rhpds.github.io/<org>/<repo>
  start_page: modules::index.adoc

content:
  sources:
    - url: .
      start_path: content

ui:
  bundle:
    url: https://github.com/rhpds/rhdp_showroom_theme/releases/download/patternfly-6/ui-bundle.zip
    snapshot: true
  supplemental_files: ./content/supplemental-ui

output:
  dir: ./www
```

### content/antora.yml

```yaml
name: modules
title: "Workshop Title"
version: ~
nav:
  - modules/ROOT/nav.adoc

asciidoc:
  attributes:
    source-highlighter: highlight.js
    experimental: true
    page-pagination: true
    lab_name: "Workshop Title"
    # Environment-specific — Showroom platform overrides these at deploy time
    user: user-abc123
    password: "%password%"
    openshift_api_url: "https://api.cluster.example.com:6443"
    openshift_console_url: "https://console-openshift-console.apps.cluster.example.com"
    openshift_cluster_ingress_domain: apps.cluster.example.com
```

### ui-config.yml

```yaml
type: showroom
default_width: 35
persist_url_state: true

view_switcher:
  enabled: true
  default_mode: split

tabs:
  - name: Red Hat OpenShift Console
    url: '{openshift_console_url}'
  # Terminal tabs — uncomment the pattern matching your environment:
  # OCP dedicated (terminal container):
  # - name: Terminal
  #   url: /terminal/
  #   type: terminal
  # RHEL VM (bastion wetty):
  # - name: Terminal
  #   url: /wetty
  #   type: terminal
```

### nav.adoc

```asciidoc
* xref:index.adoc[Welcome]

.Workshop
* xref:01-overview.adoc[Workshop Overview]

.Modules
* xref:getting-connected.adoc[Getting Connected]
* xref:02-module-01-slug.adoc[Module 1: Title]
* xref:03-module-02-slug.adoc[Module 2: Title]

.Wrap-up
* xref:04-conclusion.adoc[Conclusion]
```

Use dot-prefixed lines (`.Workshop`, `.Modules`) as section group headers. Items under a group are indented with `*`.

### Makefile

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

serve: build
	@echo "Serving at http://localhost:$(PORT)"
	python3 -m http.server $(PORT) --directory $(SITE_DIR)

clean:
	rm -rf $(SITE_DIR)
```

### .github/workflows/gh-pages.yml (Optional)

```yaml
name: github pages

on:
  push:
    branches: [main]
    paths:
      - 'content/**'
      - 'site.yml'
      - '.github/workflows/gh-pages.yml'
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: gh-pages
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - run: npm install
      - run: npx antora --fetch site.yml
      - if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'
        uses: actions/upload-pages-artifact@v3
        with:
          path: www
  deploy:
    if: github.ref == 'refs/heads/main' && github.event_name != 'pull_request'
    needs: build
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

---

## AsciiDoc Authoring Patterns

### Page Header

Every `.adoc` page starts with a level-0 title and optional metadata:

```asciidoc
= Module 1: Reasoning Prompting
:navtitle: Module 1: Reasoning Prompting
:toc: macro
:toclevels: 1
:icons: font
```

### Lab Steps with Execute Blocks

Use AsciiDoc ordered lists with continuation (`+`) and `[source,role="execute"]` for every command the learner should run:

```asciidoc
== Exercise 1: Set up your environment

. Export your API token:
+
[source,role="execute"]
----
export TOKEN=$(oc get secret maas-secret -o jsonpath='{.data.token}' | base64 -d)
echo "Token obtained: ${TOKEN:0:20}..."
----

. Verify connectivity:
+
[source,role="execute"]
----
curl -s -H "Authorization: Bearer $TOKEN" \
  {maas_api_url}/v1/models | jq .
----
+
You should see model metadata confirming the endpoint is live.
```

Key rules:
- The `+` on its own line continues the list item (keeps numbering intact).
- `[source,role="execute"]` enables the Showroom UI copy/execute button.
- Use `[source,bash,role="execute",subs="attributes"]` when the code block contains `{attribute}` substitutions.
- Without `subs="attributes"`, curly-brace placeholders are rendered literally (useful when they are shell variables like `${VAR}`).

### Attribute Substitution in Commands

When a command contains environment-specific values, use Antora attributes:

```asciidoc
[source,bash,role="execute",subs="attributes"]
----
oc login {openshift_api_url} -u {user} -p {password}
----
```

The Showroom platform replaces `{openshift_api_url}`, `{user}`, `{password}` at deploy time. Define sensible defaults in `content/antora.yml`.

### Callouts on Config/Manifest Blocks

For non-executable YAML/JSON blocks that the learner applies to the cluster, use numbered
callouts to annotate important fields (see C.1 rule in Workshop Rules above):

```asciidoc
[source,yaml]
----
spec:
  predictor:
    model:
      modelFormat:
        name: vLLM                       # <1>
      resources:
        limits:
          nvidia.com/gpu: "1"            # <2>
----
<1> *Serving runtime* — selects vLLM; other options: `ovms`, `caikit`.
<2> *GPU limit* — requires exactly one GPU; `0` falls back to CPU.
```

When the block also has `{attribute}` placeholders, combine both subs:
`[source,yaml,subs="attributes,callouts"]`.

Never use callouts on `[source,role="execute"]` blocks — the markers would be copied
into the terminal by the Showroom execute button.

### Verification Blocks

After each exercise, add a verification section:

```asciidoc
=== Verify

✓ Token is exported +
✓ API returns model metadata
```

Use `+` at line end for soft line breaks within the block.

### Screenshots

Place images in `content/modules/ROOT/assets/images/` and embed with:

```asciidoc
image::dashboard-overview.png[WordSwarm Dashboard,link=self,window=blank,width=700]
```

- `link=self` — click opens full-size image.
- `window=blank` — opens in new tab.
- `width=700` — constrain display width.
- Alt text is the first positional parameter.

### Tables

```asciidoc
[cols="2,1,1",options="header"]
|===
|Model |Score |GPU Memory

|kimi-k2-5
|1,038
|1,128 GB

|llama-3.2-3b
|36
|18 GB
|===
```

### Cross-References

Link between pages:

```asciidoc
xref:02-module-01-reasoning.adoc[Module 1: Reasoning Prompting]
```

### External Links

```asciidoc
https://docs.redhat.com[Red Hat Documentation^]
```

The `^` suffix opens the link in a new tab.

### Admonitions

```asciidoc
NOTE: This step requires cluster-admin privileges.

TIP: Use `oc whoami` to verify your current user.

WARNING: This action deletes the project and all its resources.
```

---

## Page Content Pattern

Each page should follow this structure where applicable:

### Landing Page (`index.adoc`)

1. Title and welcome
2. What you'll learn (bulleted objectives)
3. Who this is for (audience and experience level)
4. Prerequisites
5. Estimated time
6. Call to action (link to first module)

### Module Pages (`NN-module-*.adoc`)

1. Title with `:navtitle:` and optional `:toc:`
2. Module introduction (1-2 paragraphs of context)
3. Learning objectives
4. Conceptual background (if needed)
5. Numbered exercises with `[source,role="execute"]` blocks
6. Verification block after each exercise
7. Module summary — use the exact bold-label format:
   ```asciidoc
   == Module summary

   **What you accomplished:**

   * Past-tense action (3 bullets)

   **Key takeaways:**

   * Present-tense declarative fact (3 bullets)

   **Next steps:**

   One or two sentences of prose linking to the next module — never bullets.
   ```

### Getting Connected (`getting-connected.adoc`)

1. Login steps with credentials via `{user}` / `{password}` attributes
2. Project/namespace setup
3. Workbench or environment creation (with screenshots)
4. Tool verification (`[source,role="execute"]` blocks for version checks)

### Conclusion (`NN-conclusion.adoc`)

1. What was accomplished (per-module summary)
2. Key takeaways (grouped by theme)
3. Try-it-yourself links
4. External resources
5. Thank you

---

## Screenshot Workflow

1. Log in with `playwright-cli` in a named session.
2. Save auth state with `state-save` if the flow spans many screenshots.
3. For each screenshot, open the page, wait for the intended state, and capture to `content/modules/ROOT/assets/images/`.
4. Use deterministic filenames (e.g., `dashboard-overview.png`, `workbench-create.png`) so re-captures replace the same files and `image::` references stay stable.
5. Re-capture whenever the UI, console version, or workshop steps change.

### Screenshot Manifest (Optional)

For workshops with many screenshots, use a `capture/screenshot-manifest.yaml` to define the full set. Keep workshop-specific values in `capture/workshop-config.toml` and reference them with `{{ key }}` placeholders.

```yaml
workshop:
  slug: workshop-name
  title: Workshop Title
  product: rhai-3.3
  config_file: capture/workshop-config.toml
  viewport:
    width: "{{ viewport.width }}"
    height: "{{ viewport.height }}"

shots:
  - name: login-page
    url: "{{ console_url }}"
    output: content/modules/ROOT/assets/images/01-login-page.png
    caption: OpenShift console login page
    alt_text: OpenShift console login page
    wait_for:
      - "getByRole('heading', { name: /log in/i })"
    steps: []
```

## Guardrails

- Use non-production clusters and dedicated demo accounts for screenshot capture.
- Redact or avoid sensitive values such as usernames, tokens, cluster IDs, pull-secret content, and internal hostnames. Use `{attribute}` substitution instead of hardcoding.
- Keep browser viewport, zoom, theme, and product version consistent across a workshop.
- Do not invent successful UI states. If the cluster is not ready, fix the environment or mark the screenshot step as blocked.
- Never commit real auth state, passwords, or tokens. Use `{attribute}` placeholders that the Showroom platform injects at deploy time.

---

## Build and Preview

### First-Time Bootstrap (New Workshop)

After scaffolding all files, run these steps in order. Every step is required — skipping any one produces a broken or empty site.

```bash
# 1. Initialize git — Antora REQUIRES at least one commit.
#    Without it the site builds but contains zero content pages.
#    The only symptom is a warn-level log:
#    "No matching references found for content source entry"
git init && git add -A && git commit -m "Initial workshop scaffold"

# 2. Install Antora and dependencies from package.json
npm install

# 3. Build the site
make build

# 4. Build and serve locally (includes install + build)
make serve
# Site available at http://localhost:8887
```

### Subsequent Builds

```bash
# Rebuild and serve after editing .adoc content
make serve

# Clean build output
make clean
```

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Site builds but shows only 404 / empty `_/` directory | No git commits | `git add -A && git commit` |
| `npx: command not found` or `antora: not found` | Missing `package.json` or `npm install` not run | Create `package.json` with `@antora/cli` and `@antora/site-generator`, then `npm install` |
| `Cannot find module '@antora/site-generator'` | `npm install` not run | `npm install` |
| Pages render but no styling / broken layout | Missing or wrong UI bundle URL in `site.yml` | Use the `rhpds/rhdp_showroom_theme` URL from the template |
| `{attribute}` placeholders render literally in code blocks | Missing `subs="attributes"` | Add `[source,bash,subs="attributes"]` to the block |

The built site lands in `./www/` and can be deployed to GitHub Pages or served by the Showroom platform.
