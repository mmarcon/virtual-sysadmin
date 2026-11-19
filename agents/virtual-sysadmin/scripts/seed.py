#!/usr/bin/env python
"""Seed tenant knowledge into a deployed Atlas Agent Engine memory store.

The in-agent ``seed_demo_knowledge`` tool seeds whatever tenant the request
belongs to; this script does the same thing offline, so you can prepare tenants
before a demo without running the agent. It uses the standalone
``agent-engine-sdk-memory`` client, not ``app.memory``.

Set the connection via environment variables (or pass ``--token``/``--project``):

    export AGENTIC_MEMORY_SERVICE_ACCOUNT_TOKEN=...   # service-account access token
    export AGENTIC_MEMORY_PROJECT_ID=...              # your project id
    # export AGENTIC_MEMORY_BASE_URL=...              # only for a non-default endpoint

Then run from the agent directory:

    uv run python scripts/seed.py acme-corp globex

Each tenant is seeded under the synthetic admin user ``<tenant>:seed``, so the
records carry the same tenant-qualified identity and ``tenant_id`` metadata the
agent writes at runtime.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from agent_engine_sdk_memory import Memory, MemoryRequestContext  # noqa: E402

from agent_virtual_sysadmin.seed_knowledge import seed_tenant  # noqa: E402

DEFAULT_TENANTS = ["acme-corp", "globex"]


def main(argv: list[str]) -> int:
    tenants = argv[1:] or DEFAULT_TENANTS
    memory = Memory()  # reads AGENTIC_MEMORY_* environment variables

    for tenant in tenants:
        user_id = f"{tenant}:seed"
        session = memory.bind(MemoryRequestContext(user_id=user_id, session_id=f"seed-{tenant}"))
        counts = seed_tenant(session, tenant, user_id)
        print(f"seeded tenant '{tenant}': {counts}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
