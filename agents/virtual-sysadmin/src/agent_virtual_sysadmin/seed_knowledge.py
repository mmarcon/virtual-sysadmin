"""Tenant knowledge seeded for the AI Sysadmin demo.

Shared by the in-agent ``seed_demo_knowledge`` tool and the standalone
``scripts/seed.py`` script, so both seed exactly the same glossary, runbooks, and
baseline facts. Every record is stamped with ``metadata.tenant_id`` so it stays
tenant-scoped, and ``seed_tenant`` is idempotent (semantic facts upsert by label;
runbooks update by name).
"""

from __future__ import annotations

from typing import Any

GLOSSARY: list[tuple[str, str, str]] = [
    (
        "dex",
        "DEX Score",
        "A 0-100 Digital Employee Experience score per device or user, recomputed daily from a Technology component (endpoint, applications, collaboration) and a Sentiment component (survey responses). Bands: 0-30 frustrating, 31-70 average, 71-100 good.",
    ),
    (
        "dex",
        "EWQL",
        "EndlessWarden Query Language: a SQL-like language for reading the EndlessWarden data model (SELECT ... FROM devices WHERE ...).",
    ),
    (
        "dex",
        "Remote Action",
        "A scripted remediation executed on an endpoint by the EndlessWarden Collector, tracked as remote_action.executions.",
    ),
    (
        "dex",
        "Alert Impact Assessment",
        "EndlessWarden's classification of an alert as SIGNIFICANT, MODERATE, or MINIMAL based on how many devices or users it affects.",
    ),
    (
        "dex",
        "Collector",
        "The lightweight EndlessWarden agent installed on each endpoint that streams device, application, and session telemetry.",
    ),
]

RUNBOOKS: list[tuple[str, str, str, list[str]]] = [
    (
        "slow-device-triage",
        "Triage a slow device",
        "Diagnose a device reported as slow: check DEX score and the endpoint component, then CPU/RAM/disk from device metrics and execution.events, then propose a remediation.",
        [
            "Get the device and its DEX score; note the band.",
            "Inspect metrics: cpu_usage_pct, ram_usage_pct, disk_free_pct, disk_queue_length.",
            "Check session.logins for logon_seconds if the user reports slow logons too.",
            "Identify the top resource consumer and propose a Remote Action (disk cleanup, restart).",
        ],
    ),
    (
        "app-crash-triage",
        "Triage a crashing application",
        "Diagnose repeated crashes of an application: group execution.crashes by binary and version, find the affected population, and decide single-device vs fleet-wide.",
        [
            "Query execution.crashes filtered by the application.",
            "Group by binary and version; note the error_code and first_seen.",
            "Count affected devices; if more than a couple, treat it as fleet-wide and check for a related alert.",
            "Propose a remediation (clear cache, update the app, restart) and record the outcome.",
        ],
    ),
    (
        "logon-latency-triage",
        "Triage slow or failing logons",
        "Diagnose slow or failing logons using session.logins (logon_seconds, failed_logins_7d) and device_performance.boots.",
        [
            "Query session.logins for the user or device; note logon_seconds and failed_logins_7d.",
            "Compare against the fleet baseline for the site.",
            "Check boot_seconds and disk pressure for the device.",
            "Propose a remediation and record the episode.",
        ],
    ),
]

FACTS: list[tuple[str, str]] = [
    (
        "environment",
        "Devices stream telemetry through the EndlessWarden Collector; all reads go through EWQL.",
    ),
]

TENANT_FACTS: dict[str, list[tuple[str, str]]] = {
    "acme-corp": [
        (
            "standard-image",
            "Acme Corp standard image is Windows 11 23H2; Finance users are on Lenovo ThinkPad T14 laptops.",
        ),
        (
            "teams-issue",
            "Microsoft Teams 24152.0.0 has a known crash issue on Acme devices (error 0xc0000005), hitting Finance hardest but also affecting Sales and Marketing.",
        ),
    ],
    "globex": [
        (
            "vpn",
            "Globex remote access uses Cisco Secure Client (VPN); Operations laptops report frequent disconnects.",
        ),
    ],
}


def facts_for(tenant: str) -> list[tuple[str, str]]:
    """Return the default facts plus any tenant-specific facts."""
    return list(FACTS) + TENANT_FACTS.get(tenant, [])


def seed_tenant(
    memory: Any, tenant: str, user_id: str, *, source: str = "ai_sysadmin"
) -> dict[str, int]:
    """Seed a tenant's glossary, runbooks, and facts into ``memory``.

    ``memory`` is any object exposing ``save_taxonomic``, ``save_procedure``, and
    ``save_semantic`` -- either ``app.memory`` or a bound ``Memory`` client.
    Idempotent and safe to run repeatedly.
    """
    metadata = {"tenant_id": tenant}

    for domain, term, definition in GLOSSARY:
        # Taxonomic memory is unique per (org, domain, term) and is project-wide,
        # so scope the domain per tenant and skip terms that already exist.
        scoped_domain = f"{domain}-{tenant}"
        try:
            if memory.get_taxonomic_term(scoped_domain, term, user_id=user_id):
                continue
        except Exception:  # noqa: BLE001 - a missing lookup must not block seeding
            pass
        memory.save_taxonomic(
            domain=scoped_domain,
            term=term,
            definition=definition,
            visibility="org",
            metadata={**metadata, "type": "glossary"},
            user_id=user_id,
        )

    for procedure, description, content, steps in RUNBOOKS:
        # Procedural memory is unique per (org, procedure) and is project-wide, so
        # scope the name per tenant and skip runbooks that already exist.
        scoped_name = f"{procedure}-{tenant}"
        try:
            if memory.get_procedure(scoped_name, user_id=user_id):
                continue
        except Exception:  # noqa: BLE001 - a missing lookup must not block seeding
            pass
        memory.save_procedure(
            procedure=scoped_name,
            description=description,
            content=content,
            steps=[
                {"step_type": "instruction", "content": text, "description": text} for text in steps
            ],
            tags=[tenant],
            visibility="org",
            metadata={**metadata, "type": "runbook"},
            user_id=user_id,
        )

    facts = facts_for(tenant)
    for label, text in facts:
        memory.save_semantic(
            text=text,
            label=f"{tenant}:{label}",
            source=source,
            metadata={**metadata, "type": "environment_fact"},
            user_id=user_id,
        )

    return {"glossary_terms": len(GLOSSARY), "runbooks": len(RUNBOOKS), "facts": len(facts)}
