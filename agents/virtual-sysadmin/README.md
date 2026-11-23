# AI Sysadmin (EndlessWarden demo)

An Atlas Agent Engine agent that acts as a **DEX troubleshooting copilot** for
EndlessWarden's IT service desks. It investigates a reported issue by calling
simulated EndlessWarden platform APIs (EWQL, alerts, DEX scores, Remote
Actions), proposes a remediation, and remembers what it learns — **scoped per
customer (tenant)**.

It is a demonstration of Atlas Agent Engine **memory**: all memory types,
automatic background extraction, human-in-the-loop approval, and multi-tenant
isolation through memory metadata filtering.

## What it demonstrates

| Capability | How |
|---|---|
| Simulated API calls + troubleshooting | Remote tools (`endlesswarden_*`) query a deterministic mock of the EndlessWarden data model. |
| Human-in-the-loop | `endlesswarden_run_remote_action` is wrapped in `FunctionTool(..., require_confirmation=True)`; the run suspends for approval before the action executes. |
| All memory types | Semantic (`save_fact`), procedural (`save_runbook`), taxonomic (`save_glossary_term`), episodic (background extraction), plus short-term turns recorded by the platform. |
| Automatic extraction | Background extraction (`memory.extraction.enabled` in `project-config.yaml`) distils free-form chat into long-term memory, recalled in a later session. |
| Multi-tenancy | Every memory write stamps `metadata.tenant_id`; every read filters on the declared partition key `metadata.tenant_id`, so one customer's memory never surfaces for another. |

## Architecture

Two groups of tools, split by where they run:

- **`endlesswarden_*` tools (remote, Tool Sandbox).** Stand in for the EndlessWarden
  platform. They cannot read the runtime context, so they receive `tenant_id`
  explicitly — the model learns it from `get_request_context` and passes it on.
- **Memory / context tools (local, Agent Sandbox).** Run in-process so they can
  read the caller's custom headers and use `app.memory`. They resolve the tenant
  themselves and never depend on the model.

The tenant is resolved by `context.resolve_tenant()`, in this order:

1. the custom header `tenant-id` (sent as `X-Mdb-Agent-Engine-Custom-Tenant-Id`);
2. the tenant encoded in the user id as `tenant:user` (e.g. `acme-corp:alice`);
3. the default `endlesswarden-demo`.

The mock backend serves three tenants: **`acme-corp`**, **`globex`**, and
`endlesswarden-demo`.

## Prerequisites

- `LLM_API_KEY` in `.env` (the agent's LLM).
- `VOYAGE_API_KEY` in `.env` (required because memory is enabled).
- Apply the memory configuration (declares the `tenant_id` partition key):

  ```bash
  agentengine memory configure
  agentengine memory apply
  ```

  Partition keys are **write-once** and the memory server reads its config only
  at startup, so run this before writing memories. If `memory apply` rejects the
  `taxonomic`/`procedural` index legs, remove them from
  `metadata_partition_index` in `project-config.yaml` and re-apply; the agent
  falls back gracefully (see Notes).

## Run locally

```bash
[ -f .env ] || cp env.example .env   # set LLM_API_KEY and VOYAGE_API_KEY
agentengine dev up
```

Open the Playground at <http://localhost:3000>. The Playground has a **userId**
field — set it to `acme-corp:alice` to act as an Acme admin (the tenant comes
from the `tenant:` prefix). Use `globex:bob` for the second tenant.

## Demo script

As `acme-corp:alice`. The scenario runs in three beats — diagnose one device, fix
it, then sweep the fleet — which is where human-in-the-loop earns its keep.

### Beat 1 — Diagnose (no changes)

> "Teams keeps crashing on Priya's laptop (WKS-4471). What's going on?"

The agent calls `get_request_context`, recalls tenant knowledge, pulls the device,
its crash history, its DEX score, and any related alerts, then presents the finding
and a recommended fix. It changes nothing and waits.

### Beat 2 — Fix Priya (HITL #1)

> "Go ahead and fix it."

The agent proposes clearing the Teams cache on `WKS-4471` and calls
`endlesswarden_run_remote_action`, which **suspends for approval**. Approve; the run
resumes and the action executes.

### Beat 3 — Sweep the fleet (HITL #2, the showcase)

> "Are other people affected? Fix them too."

The agent correlates the crashes with `endlesswarden_find_affected_devices` and
finds **8 devices on Teams 24152.0.0 across three departments** — five in Finance,
but also Sales and Marketing. It proposes one bulk remediation for all eight.

Deny it, and the agent narrows the scope and re-proposes (e.g. Finance only).
Approve the narrower action, and it executes. That's the beat that shows a human
actually steering the agent rather than rubber-stamping.

Once the session goes idle, background extraction records the incident as an
episode.

### Then — automatic extraction

Have a free-form chat about Acme's environment (standard image, sites, known
issues) without asking the agent to save anything. End the session, start a **new**
session as the same user, and ask what it knows — the agent recalls facts extracted
in the background via `recall_personal_context`.

### Then — multi-tenancy

Run Beat 1 as `globex:bob`. Acme's facts, incidents, glossary, and runbooks never
appear; only Globex's own tenant data and memory are returned.

## Seed tenant knowledge

To pre-populate the glossary, runbooks, and baseline facts for a tenant, ask the
agent to call `seed_demo_knowledge` (it seeds the current tenant), or run the
offline script against a deployed project:

```bash
export AGENTIC_MEMORY_SERVICE_ACCOUNT_TOKEN=...
export AGENTIC_MEMORY_PROJECT_ID=...
uv run python scripts/seed.py acme-corp globex
```

## Deploy

```bash
agentengine init
agentengine secret set LLM_API_KEY --project-scope   # extraction needs it too
agentengine secret set VOYAGE_API_KEY --project-scope
agentengine deploy --build
```

Invoke with the tenant as a custom header (the production path):

```bash
curl -s "$AGENTENGINE_URL/api/v1/projects/$PROJECT_ID/workspaces/$WORKSPACE_ID/invoke" \
  -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Mdb-Agent-Engine-Custom-Tenant-Id: acme-corp" \
  -H "Content-Type: application/json" \
  -d '{"message": "Teams keeps crashing on Priya laptop"}'
```

The response is `suspended` with a `suspend_context.interrupts` list. Resume it,
**resending the tenant header** (custom headers are not persisted across a
suspend):

```bash
curl -s "$AGENTENGINE_URL/api/v1/projects/$PROJECT_ID/executions/$EXECUTION_ID/resume?workspace_id=$WORKSPACE_ID" \
  -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "X-Mdb-Agent-Engine-Custom-Tenant-Id: acme-corp" \
  -H "Content-Type: application/json" \
  -d '{"resume_map": {"<interrupt-id>": {"confirmed": true}}}'
```

## File layout

| Path | Purpose |
|---|---|
| `src/agent_virtual_sysadmin/main.py` | Builds the ADK agent; wraps the remediation tool in `FunctionTool(require_confirmation=True)`. |
| `src/agent_virtual_sysadmin/tools.py` | All `@app.tool` registrations (EndlessWarden API + memory/context). |
| `src/agent_virtual_sysadmin/endlesswarden_data.py` | Deterministic, tenant-scoped mock of the EndlessWarden data model. |
| `src/agent_virtual_sysadmin/context.py` | `resolve_tenant()` and memory metadata/filter helpers. |
| `src/agent_virtual_sysadmin/seed_knowledge.py` | Glossary, runbooks, and baseline facts; shared seeder. |
| `src/agent_virtual_sysadmin/system_message.py` | The AI Sysadmin system prompt. |
| `scripts/seed.py` | Offline tenant seeding via the standalone memory client. |
| `agent.yaml` | Sandbox tool placement and feature flags. |
| `../../project-config.yaml` | Project memory config, including the `tenant_id` partition key. |

## Notes and limitations

- **Short-term memory is not tenant-filtered.** The platform records turns
  automatically and they do not carry `tenant_id`; isolation for short-term
  memory comes from session scoping. Tenant filtering applies to the long-term
  types the agent writes.
- **Taxonomic and procedural memory are not partition-scoped.** The memory
  server only accepts `semantic`, `episodic`, `procedural`, and `short_term` in
  `metadata_partition_index`, and both taxonomic and procedural memory are
  project-wide, unique per `(org, domain, term)` and `(org, procedure)`
  respectively. To keep each customer's knowledge separate the agent namespaces
  those keys per tenant (`dex` → `dex-acme-corp`, `slow-device-triage` →
  `slow-device-triage-acme-corp`) and filters returned records on their
  `tenant_id` metadata in code (`lookup_glossary`, `discover_runbook`, and the
  glossary section of `recall_context`).
- **Memory reads from a tool must use `build_context`.** The durable runtime
  treats `build_context_from_sources` as an exclusive activity, which conflicts
  with the tool's own activity; `build_context` has a "memory read owned by tool"
  bypass and is the only context path safe to call from inside a tool. Writes
  (`save_*`) and the `search_*` reads call the memory engine directly and are
  also safe.
- **One tool call per turn.** The durable ADK adapter rejects overlapping tool
  activities, and ADK runs every function call in a model response
  concurrently. The model is therefore configured with
  `parallel_tool_calls=False` and instructed to call one tool at a time.
- **The tenant metadata filter needs the partition index.** Filtering on
  `metadata.tenant_id` is served by the memory search index. If a memory runtime
  already existed before the `tenant_id` partition key was configured, its index
  predates the key and a filtered read fails (HTTP 500, "Failed to build
  context"); apply the config *before* the first memory write
  (`agentengine memory configure && agentengine memory apply --wait`), and if the
  index is already drifted, recreate it. The agent degrades instead of failing —
  on a memory API error the tenant-filtered tools fall back to a user-scoped
  read (still tenant-isolated, because user ids are tenant-qualified) and report
  a `note`.
- **The mock backend is static** — `endlesswarden_run_remote_action` returns a
  deterministic result and does not change any data, so the demo is repeatable.
