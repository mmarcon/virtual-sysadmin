<!-- agentengine-create:begin -->
# virtual-sysadmin

This is an Atlas Agent Engine project. Project-level settings are in `project-config.yaml`, and each agent lives in its own directory under `agents/`.

## Agents

- `agents/virtual-sysadmin/` — see `agents/virtual-sysadmin/AGENTS.md`

Each agent has its own `AGENTS.md` with guidance for working on that agent.

Platform documentation: https://www.mongodb.com/docs/agentengine
<!-- agentengine-create:end -->

## What this project is

`agents/virtual-sysadmin/` is an **AI Sysadmin** demo: a DEX (digital employee
experience) troubleshooting copilot that calls simulated EndlessWarden platform
APIs, proposes remediations behind human approval, and showcases Atlas Agent
Engine memory — semantic, episodic, procedural, and taxonomic types, automatic
background extraction, and per-customer (tenant) isolation through memory
metadata filtering. See `agents/virtual-sysadmin/README.md` for the demo script.

