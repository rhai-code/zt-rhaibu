---
name: workshop-screenshot
description: >
  Capture screenshots from a live cluster via playwright-cli and embed them into
  showroom AsciiDoc content; writes RAC screenshot evidence. Called by workshop-act
  during acceptance testing. Triggers: "capture screenshots", "workshop screenshots",
  "recapture images", "refresh screenshots".
triggers:
  keywords:
    - "capture screenshots"
    - "workshop screenshots"
    - "take screenshots"
    - "recapture images"
    - "refresh screenshots"
    - "screenshot workshop"
  matchMode: any
enabled: true
---

# Workshop Screenshot

Capture screenshots from a live OpenShift/RHOAI cluster and embed them into workshop
AsciiDoc content. This skill is adaptive — it reads existing content and RAC
requirements to determine what to capture rather than relying on a static list.

## Skill coordination

- Use **playwright-cli** for all browser automation — session management, navigation,
  waiting, and screenshot capture.
- Read **RAC requirements** from `~/git/zt-<slug>-rac/requirements/` to identify
  acceptance criteria that imply visual verification.
- Write **RAC evidence** to `~/git/zt-<slug>-rac/assets/screenshot-evidence-<slug>.md`
  mapping each captured screenshot to the requirement criterion it satisfies.
- Read **AsciiDoc content** from `~/git/zt-<slug>-showroom/content/modules/ROOT/pages/`
  to find existing `image::` references and surrounding context.
- Use **openshift-4-21-expert** for OpenShift console navigation patterns.
- Use **openshift-ai-3-3-expert** for RHOAI dashboard navigation patterns.
- After embedding screenshots, recommend running **verify-content** to
  validate the updated content against Red Hat quality standards.
- **Subagent isolation (WORKSHOP-COMMON-RULES §7a):** each capture flow group is one
  subagent job — it owns the playwright session, writes screenshots to
  `assets/images/`, and returns only the capture table (filename | page | status |
  size) + failure excerpts. The main agent does the shot-list planning and the
  RAC evidence artifact from those results.
- See `skills/docs/WORKSHOP-COMMON-RULES.md` for shared AsciiDoc, image, security,
  and quality rules.
- Reference `${CLAUDE_SKILL_DIR}/references/capture-patterns.md` for reusable
  playwright-cli patterns for common OpenShift/RHOAI screenshot scenarios.

## Prerequisites

Check these before starting. If any are missing, print what's needed and stop.

- `playwright-cli` available — `playwright-cli --version`
- Showroom repo exists at `~/git/zt-<slug>-showroom/`
- `KUBECONFIG` is set and `oc whoami` succeeds
- Target cluster routes are accessible (test with `curl -s -o /dev/null -w "%{http_code}" https://<route>`)

Optional:
- RAC repo at `~/git/zt-<slug>-rac/` (enables gap analysis mode)
- Showroom values.yaml in `~/git/zt-<slug>-automation/` (provides deployer.domain, credentials)

## Workflow

### 0. Resolve workshop slug and repos

Accept a workshop slug as argument. If none provided, discover existing showroom repos:

```bash
ls -d ~/git/zt-*-showroom/ 2>/dev/null
```

If exactly one exists, use it. If multiple exist, list them and ask the user to
choose. Derive the slug from the directory name.

Locate the three repos:
- `~/git/zt-<slug>-showroom/` (required — content repo)
- `~/git/zt-<slug>-rac/` (optional — enables gap analysis)
- `~/git/zt-<slug>-automation/` (optional — provides cluster config values)

### 1. Analyze what to capture

Read the showroom `values.yaml` (if the automation repo exists) to extract:
- `deployer.domain` — cluster apps domain
- `showroom.user` / `showroom.password` — login credentials
- `showroom.projectName` / `showroom.workbenchName` — workshop-specific values

#### Mode A: From AsciiDoc (default)

Scan all `.adoc` files under `content/modules/ROOT/pages/`:

```bash
grep -rn 'image::' ~/git/zt-<slug>-showroom/content/modules/ROOT/pages/
```

For each `image::filename.png[alt,link=self,window=blank,width=700]` reference, extract:
- **filename** — the screenshot to capture (e.g., `06-workbench-creation-form.png`)
- **page** — which `.adoc` file contains the reference
- **context** — the surrounding AsciiDoc text (2-3 lines before the image reference)
  to understand what the screenshot should show
- **hints** — button names, page titles, form field values mentioned in the
  surrounding exercise instructions

Build a shot list ordered by page sequence (use the `NN-` filename prefix for
ordering) and by position within each page.

#### Mode B: From RAC requirements (gap analysis)

If the RAC repo exists, also read requirements from
`~/git/zt-<slug>-rac/requirements/`:

- Find acceptance criteria containing visual verification language:
  `MUST verify`, `MUST see`, `SHOULD observe`, `MUST open`, `MUST click`
- Each implies a screenshot opportunity
- Cross-reference with the shot list from Mode A
- Any requirement criterion without a matching `image::` reference is a **gap**
- Report gaps and offer to add screenshots for them

### 2. Build the shot list

For each screenshot to capture, determine:

| Field | Description |
|-------|-------------|
| `name` | Deterministic filename (e.g., `06-workbench-creation-form.png`) |
| `page` | Source `.adoc` page |
| `context` | What the screenshot should show (from AsciiDoc text) |
| `url` | Target URL (derived from `deployer.domain` or `{attribute}` references) |
| `preconditions` | Required state (logged in, project exists, on specific page) |
| `actions` | Playwright steps to reach the right state |

Group shots by navigation flow to minimize redundant steps:
- **Login flow** — shots requiring the Keycloak/OpenShift login page
- **RHOAI dashboard flow** — shots on the RHOAI dashboard (project list, project overview)
- **Workbench flow** — shots during workbench creation and startup
- **Application flow** — shots inside the running workbench (JupyterLab, etc.)

Order within each flow follows the natural user journey — do not jump back and forth.

### 3. Capture screenshots

Open a playwright-cli session and capture each shot in sequence:

```
playwright-cli -s=workshop-screenshots open <login_url>
```

For each shot in the ordered list:

1. **Navigate** to the required state using the `actions` from the shot list
2. **Wait** for the expected content to render:
   - Use `waitForLoadState('networkidle')` for page transitions
   - Use `waitForSelector` or `getByRole`/`getByText` for specific elements
   - Wait for animations to settle (500ms pause after dynamic content loads)
3. **Capture** the screenshot:
   ```
   playwright-cli screenshot ~/git/zt-<slug>-showroom/content/modules/ROOT/assets/images/<filename>
   ```
4. **Verify** the file was created and has a reasonable size (>10KB for a real screenshot)

Between flow groups, save and restore auth state:
```
playwright-cli state-save workshop-auth
playwright-cli state-load workshop-auth
```

If a capture fails (element not found, navigation error, timeout):
- Log the failure with the shot name and error
- Skip to the next shot in the same flow
- Do not abort the entire capture run

### 4. Embed into AsciiDoc

For each successfully captured screenshot:

- **Existing reference**: if `image::filename.png[alt,link=self,window=blank,width=700]` already exists in the
  `.adoc` page, the file replacement is sufficient — no AsciiDoc edit needed
- **New screenshot** (from gap analysis): insert an `image::` reference at the
  appropriate location:
  - Find the exercise step or verification block that corresponds to the screenshot
  - Insert `image::filename.png[Description,link=self,window=blank,width=700]` on the line after the instruction
    text, preceded by `+` for AsciiDoc list continuation
  - Use the context from the RAC requirement for the alt text

### 5. Rebuild and verify

```bash
cd ~/git/zt-<slug>-showroom
make build
```

After building, verify no broken image references:

```bash
grep -rn 'image::' content/modules/ROOT/pages/ | while read line; do
  file=$(echo "$line" | sed 's/.*image::\([^[]*\).*/\1/')
  if [ ! -f "content/modules/ROOT/assets/images/$file" ]; then
    echo "MISSING: $file"
  fi
done
```

### 6. Write RAC screenshot evidence

If the RAC repo exists at `~/git/zt-<slug>-rac/`, write a screenshot evidence artifact
to `~/git/zt-<slug>-rac/assets/screenshot-evidence-<slug>.md`.

This artifact maps each captured screenshot to the RAC requirement criterion it
satisfies, creating a verifiable evidence trail between visual captures and acceptance
criteria.

```markdown
---
schema_version: 1
type: asset
---
# Screenshot Evidence: <Workshop Title>

## Capture Summary

- **Date:** <capture date>
- **Cluster:** <cluster domain from deployer.domain>
- **Product version:** <RHOAI version from cluster>
- **Captured:** N/M shots
- **Failed:** N shots

## Evidence Map

| Screenshot | Page | Requirement | Criterion | Status |
|------------|------|-------------|-----------|--------|
| 01-keycloak-login.png | getting-connected.adoc | RHAIBU-KXYZFK17N4M2 | Login to OpenShift | captured |
| 02-rhoai-dashboard-home.png | getting-connected.adoc | RHAIBU-KXYZGTZVSVY9 | REQ-001 | captured |
| 06-workbench-creation-form.png | 03-module-02-...adoc | RHAIBU-KXYZGWA6G88A | REQ-001 | captured |

## Uncovered Criteria

Requirements with visual verification criteria but no matching screenshot:

- RHAIBU-KXYZGWA6G88A REQ-007: "SHOULD understand the difference..." — not screenshottable
```

The evidence map is built by matching each screenshot's AsciiDoc context back to the
RAC requirement criterion it illustrates. When a criterion uses `MUST verify`,
`MUST see`, or `MUST open` language, the screenshot that appears adjacent to that
instruction in the AsciiDoc is the evidence.

List uncovered criteria separately — these are either not screenshottable (conceptual
understanding) or gaps that need additional captures.

### 7. Report

Print a summary table:

```
=== Screenshot Capture Report ===

Filename                            | Page                        | Status   | Size
------------------------------------+-----------------------------+----------+-------
01-keycloak-login.png               | getting-connected.adoc      | captured | 142KB
02-rhoai-dashboard-home.png         | getting-connected.adoc      | captured | 198KB
06-workbench-creation-form.png      | 03-module-02-...adoc        | captured | 165KB
...

Captured: 14/14
Failed: 0
New embeddings added: 0
RAC evidence: ~/git/zt-<slug>-rac/assets/screenshot-evidence-<slug>.md
Build status: PASS
```

If any shots were captured from gap analysis, list the new `image::` references added.

Clean up the playwright session:

```
playwright-cli -s=workshop-screenshots close
```

## Guardrails

- Never fabricate screenshots. Only capture from live, running systems. If the cluster
  is not ready or a page does not load, mark the shot as failed — do not use placeholder
  images.
- Use deterministic filenames so re-captures replace existing files without requiring
  AsciiDoc edits.
- Save screenshots directly to the showroom repo's `assets/images/` directory.
- Clean up playwright sessions when capture is complete.
- Do not modify RAC requirements or decisions. If a requirement's acceptance criteria
  cannot be screenshotted, report it as a gap in the evidence artifact. Only write to
  `rac/assets/` — never to `rac/requirements/`, `rac/decisions/`, or `rac/designs/`.
- Do not create new AsciiDoc pages. Only embed screenshots into existing pages.
- Do not store auth state, passwords, or tokens in any committed file. Use playwright
  session state only.
- Redact or avoid capturing sensitive values (tokens, pull secrets, internal hostnames)
  in screenshots. Use `{attribute}` substitution in AsciiDoc, not hardcoded values.

## Out of scope

- Writing workshop content or creating new AsciiDoc pages — use `workshop-do`
- Deploying the workshop to a cluster — use `workshop-act`
- Planning which modules need screenshots — use `workshop-orient`
- Analyzing demo applications — use `workshop-observe`
- Video recording or screen recording
- Screenshot editing, cropping, or annotation

## Related Skills

- `/workshop-act` — Deploy and test the workshop end-to-end
- `/workshop-do` — Scaffold content and infrastructure from RAC requirements
- `/verify-content` — Validate content against Red Hat quality standards
