---
name: workshop-act
description: >
  Phase 4 of the OODA workshop pipeline (Act): deploy to a prelude cluster, run
  browser tests + verify-content quality gate, fix-and-test loop until RAC acceptance
  criteria pass, then PR to p-zero-lessons (publish). Triggers: "deploy workshop",
  "test workshop", "validate workshop", "workshop prelude", "publish workshop".
  Do NOT use for planning (workshop-orient) or scaffolding (workshop-do).
triggers:
  keywords:
    - "workshop act"
    - "deploy workshop"
    - "test workshop"
    - "validate workshop"
    - "workshop prelude"
    - "ooda act"
    - "workshop smoke test"
    - "workshop acceptance"
  matchMode: any
enabled: true
---

# Workshop Act

Deploy to a prelude cluster, test with browser automation, loop until RAC acceptance
criteria pass, then signal ready for human-in-the-loop review.

## Skill coordination

- Use **playwright-cli** for all browser automation — opening pages, capturing
  screenshots, clicking, filling forms, assertions.
- Use **openshift-4-21-expert** for cluster diagnostics when deployments fail.
- Use **openshift-ai-3-3-expert** for RHOAI-specific diagnostics.
- Read RAC requirements from `~/git/zt-<slug>-rac/requirements/` for acceptance criteria to validate.
- Use **workshop-screenshot** for capturing and embedding screenshots into AsciiDoc content.
- Run **verify-content** as a quality gate after content and screenshots are ready.
- See `skills/docs/WORKSHOP-COMMON-RULES.md` for shared AsciiDoc, image, security,
  and quality rules — including §7a subagent isolation: delegate the high-traffic
  steps here (playwright test runs, screenshot capture, cluster diagnostics) to
  subagents returning only pass/fail tables + evidence paths; the main agent keeps
  the fix-loop categorization and the final report.

## Prerequisites

Check these before starting. If any are missing, print what's needed and stop.

**Required tools:**
- `git` — `git --version`
- `oc` CLI — `oc version` (OpenShift client, authenticated as cluster-admin)
- `helm` — `helm version --short`
- `node` / `npm` — `node --version && npm --version`
- `decided` CLI — `decided --version` ([install](https://github.com/asdecided/core/releases))
- `playwright-cli` — for browser automation and screenshot capture

**Required cluster access:**
- `oc` authenticated to a prelude OpenShift cluster (`oc whoami` succeeds)
- RHOAI operator available or pre-installed (only if the workshop content requires it)
- Sufficient resources for the workshop (GPUs if required)

**Required state (from prior pipeline steps):**
- Workshop RAC repo at `~/git/zt-<slug>-rac/` (from workshop-orient)
- Workshop content repo at `~/git/zt-<slug>-showroom/` (from workshop-do) with a successful `make build`
- Workshop infrastructure repo at `~/git/zt-<slug>-automation/` (from workshop-do) — a thin
  Helm wrapper (`values-<slug>.yaml` + `Makefile`) referencing the `zt-showroom-deployer` chart

## Workflow

### 0. Resolve workshop slug

Accept `$ARGUMENTS` as a workshop slug. If no argument is provided, discover
existing RAC repos:

```bash
ls -d ~/git/zt-*-rac/ 2>/dev/null
```

If exactly one exists, use it. If multiple exist, list them and ask the user to
choose. If none exist, stop — workshop-orient must be run first.

Verify that all three repos exist for the resolved slug:
- `~/git/zt-<slug>-rac/` (RAC artifacts)
- `~/git/zt-<slug>-showroom/` (content)
- `~/git/zt-<slug>-automation/` (infrastructure)

If the showroom or automation repo is missing, stop — workshop-do must be run first.

### 1. Pre-flight checks

Verify the environment before deploying:

```bash
oc whoami
oc whoami --show-server
oc get clusterversion -o jsonpath='{.items[0].status.desired.version}'
oc get co --no-headers | grep -v "True.*False.*False" | head -10
helm version --short
decided --version
```

If any check fails, report the issue and stop. Do not deploy to an unhealthy cluster.

Confirm the cluster URL matches the expected prelude cluster. Ask the user to verify
if this is the correct target before proceeding.

### 2. Deploy the showroom

The infra repo is a thin Helm wrapper (`values-<slug>.yaml` + `Makefile`) around the
published `zt-showroom-deployer` chart — no ArgoCD, no app-of-apps, no operator/tenant
layers. Deploy with `helm upgrade --install` via the Makefile.

First fill in the cluster-specific values in `values-<slug>.yaml` (they are placeholders
after workshop-do): `deployer.domain`, `deployer.apiUrl`, and the `showroom.wetty.*` SSH
coordinates. Confirm the content repo is pushed to the `showroom.gitRepoUrl` — the chart's
`git-cloner` init container clones it on-cluster.

```bash
cd ../zt-<slug>-automation

# Fill cluster coordinates (or edit values-<slug>.yaml directly)
DOMAIN=$(oc get ingress.config cluster -o jsonpath='{.spec.domain}')
API=$(oc whoami --show-server)

make repo                    # helm repo add/update the chart repo
make template                # render locally to review (no cluster changes)
make deploy                  # helm upgrade --install into showroom-<slug>
```

`make deploy` runs `helm upgrade --install showroom <chart> -n showroom-<slug>
--create-namespace -f values-<slug>.yaml`. To deploy against a local chart checkout
instead of the published repo, pass `CHART=~/git/zt-showroom-deployer`.

### 3. Verify showroom readiness

Verify the showroom deployment came up:

```bash
helm status showroom -n showroom-<slug>
oc rollout status deploy/showroom -n showroom-<slug> --timeout=5m
oc get pods -n showroom-<slug>            # expect the showroom pod Running (all containers ready)
ROUTE=$(oc get route -n showroom-<slug> -o jsonpath='{.items[0].spec.host}')
curl -sk -o /dev/null -w '%{http_code}\n' https://$ROUTE/   # expect 200
```

The chart's init containers (`git-cloner`, `antora-builder`) clone and build the content
on-cluster; `cluster-setup` patches the IngressController so the environment iframe renders.

Only if the **workshop content itself** requires cluster-side resources (e.g. RHOAI model
serving), also verify those pre-exist on the cluster — this skill does not install them:
- Operator CSVs `Succeeded`: `oc get csv -A --no-headers | grep -v Succeeded`
- Required CRDs registered (e.g., `InferenceService`)

Map each check back to a RAC requirement's acceptance criteria. Record pass/fail.

### 4. Build and serve workshop content

In the content repo:

```bash
cd ../zt-<slug>-showroom
make serve &
SERVE_PID=$!
```

Wait for the server to start (poll `http://localhost:8887` until it responds).

Use playwright-cli to open the workshop landing page and verify it renders correctly:
- Page title matches the workshop name
- Navigation sidebar has entries for all modules
- No broken images or missing CSS

### 5. Run acceptance tests

For each RAC requirement, execute its acceptance criteria:

**Content tests** (for each module page):
- Open the page URL with playwright-cli
- Verify the page renders (check for the module title text)
- Verify `[source,role="execute"]` blocks are present (check for code block elements)
- Capture a screenshot and save to `content/modules/ROOT/assets/images/`
  using deterministic filenames

**Infrastructure tests** (for cluster-dependent steps):
- Log into the OpenShift console with playwright-cli
- Navigate to the relevant pages (RHOAI dashboard, model serving, etc.)
- Execute commands from the workshop lab steps in a terminal
- Verify expected outcomes (pods running, models deployed, API responding)
- Capture screenshots of each verified state

**Record results** in a structured format:

| Requirement ID | Test Description | Status | Evidence |
|----------------|------------------|--------|----------|
| RHAIBU-REQ-001 | Login to console | PASS | screenshot: 01-login.png |
| RHAIBU-REQ-002 | Deploy model | FAIL | Error: timeout waiting for pod |

### 5b. Content quality verification

Run the `verify-content` skill (vendored in this repo under `skills/verify-content/`)
against the showroom content:

```
/verify-content
```

This spawns parallel agents per module, checking against Red Hat quality standards:
- AsciiDoc structure and formatting (missing execute roles, broken blocks)
- Accessibility compliance (image alt text, heading hierarchy)
- Red Hat style guide (product names, acronym expansion)
- Technical accuracy (undefined attributes, broken xrefs)

On **fix-loop re-runs** (step 6), pass `modules: [<changed .adoc files>]` in the
invocation so only the changed modules are re-reviewed — unchanged modules keep
their prior findings.

**Severity handling:**
- **Critical** / **High** — must fix before proceeding to the fix-and-test loop
- **Warning** / **Info** — report in the validation table but do not block

### 6. Fix-and-test loop

If any test fails, identify the failure category and fix:

**Content issue** (AsciiDoc error, wrong instructions, missing page):
1. Fix the `.adoc` file in the content repo
2. Rebuild: `make build`
3. Go to step 5 — **delta mode**: re-test only the failed requirement(s) and the
   module page(s) they belong to; do not re-run tests for requirements that passed
   in a prior iteration (their evidence is still valid — the fix touched only the
   files listed in this iteration's fix step)

**Infrastructure issue** (showroom pod won't start, wrong values, content build fails):
1. Fix `values-<slug>.yaml` in the automation repo (or the content repo if the on-cluster
   antora build failed), and push content changes so `git-cloner` picks them up
2. Redeploy: `make deploy` (helm upgrade --install) — or `oc rollout restart deploy/showroom
   -n showroom-<slug>` to re-run the init containers against updated content
3. Wait for the rollout to complete
4. Go to step 3 — infra changes invalidate ALL evidence, so re-run the full suite

**Environment issue** (cluster problem, insufficient resources, external dependency):
1. Report the issue to the user with diagnostics
2. Stop the loop — environment issues require human intervention

**Loop bounds:**
- Maximum 5 iterations before escalating to human-in-the-loop
- Track which requirements passed/failed per iteration
- Detect no-progress (same tests failing the same way) and bail out early
- Delta re-test (content fixes) vs full re-test (infra fixes) as above — this keeps
  per-iteration cost proportional to what actually changed

### 7. Clean up and report

Stop the local server:

```bash
kill $SERVE_PID 2>/dev/null
```

Print the final results table:

```
=== Workshop Validation Report ===

Requirement ID   | Title                    | Status | Iterations | Evidence
-----------------+--------------------------+--------+------------+---------
RHAIBU-REQ-001   | Console Login            | PASS   | 1          | 01-login.png
RHAIBU-REQ-002   | Model Deployment         | PASS   | 3          | 02-model.png
RHAIBU-REQ-003   | API Query                | FAIL   | 5          | Error: timeout

Passed: 8/10
Failed: 2/10
Iterations: 3

Human review needed for:
- RHAIBU-REQ-003: API endpoint not responding (environment issue)
- RHAIBU-REQ-009: Cannot automate — requires manual verification
```

If all requirements pass:
"Workshop validation complete. All requirements passed. Ready for human-in-the-loop review."

If some failed after max iterations:
"Workshop validation incomplete after 5 iterations. The above requirements need attention."

Prompt the user to commit updated screenshots and any content fixes.

### 8. Publish to p-zero-lessons

Once all requirements pass (or after human sign-off if some needed manual review),
contribute the validated content to the central lessons repo.

**Target repo:** `https://github.com/red-hat-ai-dev/p-zero-lessons`
**Repo structure:**
```
p-zero-lessons/
  antora-playbook.yml          ← registers all lesson components; update this
  home/                        ← hub landing page; update nav.adoc and index.adoc
    antora.yml
    modules/ROOT/
      nav.adoc                 ← add an xref entry for the new lesson
      pages/index.adoc         ← add a row to the lessons table
  supplemental-ui/             ← shared UI assets (do not modify)
  lib/inject-buttons.js        ← shared Antora extension (do not modify)
  lessons/
    <slug>/                    ← lesson content goes here
      content/
        antora.yml             ← MUST have name: <slug> (not "modules")
        ...
```

**GitHub Pages:** merging to `main` auto-triggers the Actions workflow
(`.github/workflows/gh-pages.yml`) which builds with `antora-playbook.yml`
and deploys to `https://red-hat-ai-dev.github.io/p-zero-lessons/`.

#### Step-by-step

**1. Clone or update the lessons repo:**

```bash
LESSONS_DIR=~/git/p-zero-lessons
if [ -d "$LESSONS_DIR" ]; then
  git -C "$LESSONS_DIR" fetch origin && git -C "$LESSONS_DIR" checkout main && git -C "$LESSONS_DIR" pull
else
  git clone https://github.com/red-hat-ai-dev/p-zero-lessons.git "$LESSONS_DIR"
fi
git -C "$LESSONS_DIR" checkout -b workshop/<slug>
```

**2. Copy lesson content (exclude build artifacts and git history):**

```bash
rsync -av --delete \
  ~/git/zt-<slug>-showroom/ \
  "$LESSONS_DIR/lessons/<slug>/" \
  --exclude='.git' \
  --exclude='node_modules' \
  --exclude='.cache' \
  --exclude='www'
```

**3. Fix the Antora component name** — the showroom scaffold uses `name: modules`
by default but p-zero-lessons needs each lesson's component name to match its slug
so cross-component xrefs work:

```bash
# In lessons/<slug>/content/antora.yml, set:  name: <slug>
sed -i '' "s/^name: modules/name: <slug>/" "$LESSONS_DIR/lessons/<slug>/content/antora.yml"
```

Verify the change: `grep '^name:' "$LESSONS_DIR/lessons/<slug>/content/antora.yml"`

**4. Register the lesson in `antora-playbook.yml`** — add a new content source entry:

```yaml
content:
  sources:
    - url: .
      start_path: home
    # existing lessons...
    - url: .
      start_path: lessons/<slug>/content   # ← add this line
```

**5. Update the hub landing page** so the lesson appears in the sidebar and table:

In `home/modules/ROOT/nav.adoc`, add under `.Lessons`:
```asciidoc
* xref:<slug>::index.adoc[<Workshop Title>]
```

In `home/modules/ROOT/pages/index.adoc`, add a row to the lessons table:
```asciidoc
| xref:<slug>::index.adoc[<Workshop Title>]
| <one-line description>
| <estimated time>
```

**6. Update the site URL in the lesson's `site.yml`:**

```bash
sed -i '' "s|url:.*zt-<slug>-showroom|url: https://red-hat-ai-dev.github.io/p-zero-lessons/<slug>|" \
  "$LESSONS_DIR/lessons/<slug>/site.yml"
```

**7. Commit and open a PR:**

```bash
git -C "$LESSONS_DIR" add lessons/<slug>/ antora-playbook.yml \
  home/modules/ROOT/nav.adoc home/modules/ROOT/pages/index.adoc
git -C "$LESSONS_DIR" commit -m "Add <slug> workshop lesson"
git -C "$LESSONS_DIR" push -u origin workshop/<slug>
gh pr create \
  --repo red-hat-ai-dev/p-zero-lessons \
  --base main \
  --head workshop/<slug> \
  --title "Add <slug> workshop" \
  --body "Validated workshop from zt-<slug>-showroom. All RAC acceptance criteria passed."
```

Print the PR URL and stop. Human review and merge is the final gate — the GitHub
Actions workflow deploys automatically on merge to `main`.

## Guardrails

- Never deploy to a production cluster. Verify the cluster URL with the user before
  deploying.
- Never delete namespaces or resources not created by this skill. Use labels
  (`app.kubernetes.io/managed-by: workshop-act`) on test resources.
- Do not modify RAC requirements to make tests pass. If a requirement is wrong or
  untestable, flag it and ask the user to update it in the Orient step.
- Bound the fix-and-test loop at 5 iterations. Infinite loops waste cluster resources.
- Capture screenshots only from the target product version. Never reuse screenshots
  from a different version or fabricate UI states.
- Clean up test artifacts (playwright sessions, background server processes) on exit.
- If the OODA loop finds structural problems (wrong module count, missing concepts),
  recommend going back to Orient rather than patching at the Act level.

## Out of scope

- Writing new workshop content from scratch — use `workshop-do`
- Planning the workshop — use `workshop-orient`
- Analyzing demo applications — use `workshop-observe`
- Production deployment or multi-tenant provisioning
- Performance testing or load testing

## Related Skills

- `/workshop-do` — Scaffold content and infrastructure from RAC requirements
- `/workshop-screenshot` — Capture and embed screenshots into AsciiDoc content
- `/verify-content` — Validate content against Red Hat quality standards
- `/catalog-builder` — Create RHDP AgnosticV catalog entry when ready to publish
