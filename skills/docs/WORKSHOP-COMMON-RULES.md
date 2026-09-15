# Workshop Common Rules

**Version**: 1.3

Shared contracts for all workshop-* skills in the OODA pipeline. Every workshop skill
MUST reference this file and follow these rules.

---

## 0. Security — No Secrets (MANDATORY)

Skills MUST NOT produce, accept, or store sensitive information in any file.

**Prohibited content:**
- Real passwords, API keys, tokens, secrets, or credentials
- Internal hostnames, VPN endpoints, bastion IPs, or non-public URLs
- SSH keys, certificates, kubeconfig contents, or private key material

**Required patterns:**
- Use `{attribute}` placeholders for all environment-specific values (e.g., `{password}`, `{openshift_console_url}`)
- Use `example.com`, `192.0.2.x` (RFC 5737), and dummy UUIDs in examples
- Never commit auth state files (playwright state, `.auth-state.json`, kubeconfig)

**Skill behavior:**
- Never ask users to paste credentials into the conversation
- Never write credentials to generated files
- Never echo back real credentials provided by the user

---

## 1. AsciiDoc Code Blocks (REQUIRED)

### Executable Commands

Use `[source,role="execute"]` for every command the learner should run. This enables
the Showroom UI copy/execute button.

```asciidoc
[source,role="execute"]
----
oc get pods -n my-project
----
```

When attribute substitution is needed:

```asciidoc
[source,bash,role="execute",subs="attributes"]
----
oc login {openshift_api_url} -u {user} -p {password}
----
```

**Do NOT use `[.copypaste]`** — it is the older nookbag pattern and is deprecated.

### Non-executable Blocks

- Config/data blocks: `[source,yaml]`, `[source,json]` — no `role="execute"`
- Expected output: plain `----` listing with no source declaration
- AsciiDoc examples: `[source,asciidoc]`

### List Continuation

The `+` on its own line continues a list item (keeps numbering intact):

```asciidoc
. Run the command:
+
[source,role="execute"]
----
oc get pods
----
```

---

## 1a. YAML/Config Callouts (RECOMMENDED)

Non-executable `[source,yaml]` / `[source,json]` blocks that represent manifests or config
applied to the cluster SHOULD use AsciiDoc numbered callouts to annotate important fields.

Full reference with examples: `skills/openshift-workshop-builder/references/yaml-callouts.md`.

### When to use

- Block is a manifest the learner applies (`oc apply`, `oc create`, `oc process`)
- Block has fields the learner must understand to succeed in later exercises
- Field names are opaque without context (e.g., `modelFormat.name`, `runtime`)

### When NOT to use

- Executable blocks (`[source,role="execute"]`) — callout markers would be copied to terminal
- Expected output or trivial config (1–2 obvious fields)
- Surrounding prose already explains every field

### Rules

- Maximum **5 callouts per block** — more is noise
- Each callout: one sentence — `<1> *Bold label* — explanation.`
- Use `[source,yaml,subs="attributes,callouts"]` when the block also has `{attribute}` placeholders
- Markers must be sequential (`<1>`, `<2>`, `<3>`) and match between inline and explanation list

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

---

## 2. Image Conventions (REQUIRED)

All images go in `content/modules/ROOT/assets/images/`.

### Required Syntax

```asciidoc
image::filename.png[Alt text,link=self,window=blank,width=700]
```

- `link=self` — click opens full-size image
- `window=blank` — opens in new tab
- `width=700` — constrain display width (500-800px typical)
- Alt text is the first positional parameter — make it meaningful for accessibility

### Filename Conventions

- Use deterministic names so re-captures replace existing files: `01-keycloak-login.png`, `06-workbench-creation-form.png`
- Use 2-digit prefix for ordering within a module
- Descriptive slug after the prefix — no `image1.png`

### Placeholders

If an image doesn't exist yet:

```asciidoc
// TODO: capture screenshot
image::create-workbench-form.png[Workbench creation form,link=self,window=blank,width=700]
```

---

## 3. Attribute Substitution (REQUIRED)

Never hardcode cluster-specific values. Use Antora attributes defined in
`content/antora.yml`:

```yaml
asciidoc:
  attributes:
    openshift_console_url: https://console-openshift-console.{deployer_domain}
    user: user1
    password: openshift
    project_name: demo
```

Use `subs="attributes"` on code blocks that contain `{attribute}` values. Without it,
curly-brace placeholders render literally.

---

## 4. RAC Integration (REQUIRED)

Workshop artifacts live in the RAC repo at `~/git/zt-<slug>-rac/`.

**Read from:**
- `requirements/` — acceptance criteria, learning objectives, module structure
- `decisions/` — architectural decisions (content format, infra approach)
- `designs/` — parameter inventory, module flow

**Write to:**
- `assets/` only — observation documents, screenshot evidence, validation reports

**Never modify:**
- `requirements/`, `decisions/`, `designs/` — if a requirement is wrong, flag it and
  ask the user to update it via workshop-orient

---

## 5. Quality Gate (REQUIRED)

Before declaring content ready, run the `verify-content` skill (vendored in this repo
under `skills/verify-content/`).

```
/verify-content
```

This launches parallel agents per module, checking against Red Hat quality standards:
- AsciiDoc structure and formatting
- Accessibility compliance
- Red Hat style guide
- Technical accuracy

**Severity handling:**
- **Critical** / **High** — must fix before proceeding
- **Warning** — report but do not block
- **Info** / **Recommendation** — optional improvement

---

## 6. Related Skills Convention (REQUIRED)

Every SKILL.md ends with a `## Related Skills` section listing connected skills:

```markdown
## Related Skills

- `/workshop-orient` — Plan the workshop from observations
- `/workshop-do` — Scaffold content and infrastructure
- `/verify-content` — Validate content against Red Hat standards
```

---

## 7. Skill Coordination Pattern

Skills in the OODA pipeline follow a sequential handoff:

```
Observe → Orient → Do → Act
                    ↑      ↑
              screenshot  verify-content
```

Each skill reads from the previous phase's output and writes to its own output
location. Skills communicate through:
- RAC artifacts (requirements, decisions, designs)
- Git repos (showroom content, automation infrastructure)
- Structured reports (validation tables, evidence maps)

---

## 7a. Subagent Isolation (REQUIRED — context hygiene)

Auto-accept runs burn tokens quadratically when verbose tool traffic (browser
snapshots, build logs, schema dumps, reference-catalog reads) lands in the main
conversation, because every later tool call re-sends it.

**Rule: high-traffic work runs in subagents; the main agent orchestrates and
keeps only structured results.**

- Delegate when a step produces >~50 lines of tool output per action, or reads
  large reference material: browser automation runs, screenshot capture,
  per-module content drafting, cluster diagnostics, reference-catalog/example
  reads, schema dumps.
- **Pass** the subagent everything it needs (paths, requirements, attributes,
  credentials-free coordinates) — subagents share nothing from the parent
  conversation.
- **Return** a structured summary only (pass/fail tables, file paths, evidence
  locations, error excerpts ≤10 lines). No raw snapshots, logs, or page dumps.
- **Never delegate** the decisions: RAC authoring/ratification, fix-loop
  categorization (content vs infra vs environment), publish, and anything the
  user must see verbatim. The main agent stays the source of truth and re-reads
  a subagent's output files before acting on its claims.
- verify-content and catalog-builder are already subagent-orchestrated by
  design — invoke them as-is, don't inline their agents' work.

---

## 8. Prose Style (REQUIRED)

Every module page MUST follow these four prose rules. Full AsciiDoc examples with bad/good
side-by-sides are in
`skills/openshift-workshop-builder/references/prose-style.md`.

### P.1 — Module summary format

End every module page with `== Module summary` containing three bold-label sections:

```asciidoc
== Module summary

**What you accomplished:**

* Past-tense action (3 bullets)

**Key takeaways:**

* Present-tense declarative fact (3 bullets)

**Next steps:**

One or two sentences of prose linking to the next module — never bullets.
```

The conclusion module omits **Next steps**.

### P.2 — Exercise transitions

Every `== Exercise N` boundary must have at least one bridging sentence (after `=== Verify`,
before the next heading). Three interchangeable formulas:

- **Callback-then-pivot**: "Now that you've [done X], let's [do Y]."
- **Problem-then-purpose**: State the gap, then what the next exercise closes.
- **Forward reference**: "You will explore this in Exercise N."

### P.3 — Workaround handling

Any workaround or known deviation: NOTE/WARNING **before** the command → "This is expected."
→ one sentence why → then the command block. Never explain after the command.
Complex optional depth → `[%collapsible]` block.

### P.4 — Admonition type

| Admonition | Use for |
|---|---|
| `TIP` | Orientation, persona framing, practical shortcuts |
| `NOTE` | Non-determinism, expected friction, key conceptual asides |
| `IMPORTANT` | Structural, safety, or ordering constraints |
| `WARNING` | Destructive or irreversible operations |

**Severity handling (verify-content check IDs P.1–P.4):**
- P.1 missing or malformed → Warning
- P.2 missing transition → Warning
- P.3 explanation after command → Warning
- P.4 wrong admonition type → Info

---

**Maintained by:** zt-rhaibu OODA pipeline
