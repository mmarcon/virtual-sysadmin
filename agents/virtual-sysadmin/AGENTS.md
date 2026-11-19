# AI Sysadmin (EndlessWarden demo)

Atlas Agent Engine is a MongoDB Atlas service for building, running, and deploying AI agents. You write the agent as a LangGraph or Google ADK app, and the `agentengine` CLI runs it locally and deploys it to the platform.

This agent is a **Google ADK 2** DEX troubleshooting copilot for EndlessWarden's platform. It investigates reported IT issues by calling simulated EndlessWarden APIs, proposes remediations (behind human approval), and remembers what it learns — scoped per customer (tenant) through memory metadata filtering. See `README.md` for the demo script.

## File Layout

| Path | Purpose |
|---|---|
| `agent.yaml` | App name, entrypoint, `framework: adk`, feature flags, and tool placement across sandboxes. |
| `dev.yaml` | Local-only settings for `agentengine dev up`: service ports and the local MongoDB container. |
| `env.example` | Environment variable names. Copy to `.env` if missing. |
| `pyproject.toml` | Python dependencies, including `agent-engine-sdk-adk` and `google-adk`. |
| `pyrightconfig.json` | Type-checking settings. |
| `src/agent_virtual_sysadmin/main.py` | Creates the `App`, returns the `LlmAgent`, and wraps the remediation tool in `FunctionTool(require_confirmation=True)`. |
| `src/agent_virtual_sysadmin/tools.py` | All `@app.tool` registrations: remote `endlesswarden_*` API tools and local memory/context tools. |
| `src/agent_virtual_sysadmin/endlesswarden_data.py` | Deterministic, tenant-scoped mock of the EndlessWarden data model (EWQL, alerts, DEX, Remote Actions). |
| `src/agent_virtual_sysadmin/context.py` | `resolve_tenant()` and memory metadata/filter helpers. |
| `src/agent_virtual_sysadmin/seed_knowledge.py` | Glossary, runbooks, and baseline facts; shared by the tool and the offline seeder. |
| `src/agent_virtual_sysadmin/llm.py` | LLM provider and model selection through `LiteLlm`. |
| `src/agent_virtual_sysadmin/system_message.py` | The AI Sysadmin system prompt. |
| `scripts/seed.py` | Offline tenant seeding via the standalone `agent-engine-sdk-memory` client. |
| `README.md` | Setup, demo script, and deployment walkthrough. |

## Configuration

- `agent.yaml`: `name` and `entrypoint` identify the app. `features.memory` turns long-term memory on or off. The `sandboxes` lists decide which tools run in the agent sandbox (local) and which run in the tool sandbox (remote) — keep them consistent with each tool's `is_local` argument.
- `src/agent_virtual_sysadmin/llm.py`: `MODEL` and the `LiteLlm` constructor select the LLM provider. Every provider reads its key from `LLM_API_KEY`.
- `.env`: `LLM_API_KEY` is required; `VOYAGE_API_KEY` is required when memory is enabled. Leave `MONGODB_URI` empty for local development.
- `../../project-config.yaml`: project memory config, including the `tenant_id` metadata partition key that backs multi-tenancy. Apply changes with `agentengine memory configure && agentengine memory apply`.
- `dev.yaml`: the Playground UI port, fixed at `3000`.

## Conventions

- Remote tools cannot read the runtime context, so any tool that needs the tenant or user id must be a **local** tool, or receive the value as an argument.
- Every memory write stamps `metadata={"tenant_id": <tenant>}`; every read filters `{"metadata.tenant_id": <tenant>}` (the qualified index path). Use `context.tenant_metadata()` / `context.tenant_filter()` rather than inlining the key.

## Run Locally

```bash
[ -f .env ] || cp env.example .env
# Set LLM_API_KEY and VOYAGE_API_KEY in .env.
agentengine memory configure && agentengine memory apply
agentengine dev up
```

The Playground UI is at `http://localhost:3000`; set its `userId` field to `acme-corp:alice` to select a tenant.

## Deploy

If memory is enabled, set `LLM_API_KEY` and `VOYAGE_API_KEY` at project scope so extraction can read them.

```bash
agentengine init
agentengine secret set LLM_API_KEY --project-scope
agentengine secret set VOYAGE_API_KEY --project-scope
agentengine build
agentengine deploy
```

`agentengine agent validate` checks `agent.yaml` before a build.

## Platform Documentation

The documentation site is the source of truth:

```
https://www.mongodb.com/docs/agentengine
```

The index at `https://www.mongodb.com/docs/agentengine/llms.txt` lists every page with a one-line summary and a link to its Markdown version. Fetch the index, pick pages by their summaries, and read only those pages. Prefer the documentation over prior knowledge about Atlas Agent Engine.

## Skills

Install the Agent Engine skills for this project if your coding agent does not list them:

```bash
npx skills add mongodb/agent-engine-examples
```

- `atlas-agent-engine`: change this project's code. Covers the project layout, tools, memory, human review, guardrails, and deployment.
- `atlas-agent-engine-docs`: answer platform questions from the documentation site.
