"""Tools for the AI Sysadmin demo.

Two groups, split by where they run:

* **Simulated EndlessWarden API tools** (``is_local=False``) run in the isolated Tool
  Sandbox and stand in for the EndlessWarden platform (EWQL, Remote Actions, alerts,
  DEX scores). They cannot see the runtime context, so the tenant is passed in
  explicitly by the model, which learns it from ``get_request_context``.

* **Memory and context tools** (``is_local=True``) run in the Agent Sandbox with
  the full runtime context, so they can read the caller's custom headers and use
  ``app.memory``. They resolve the tenant themselves and never depend on the
  model to get it right.
"""

from __future__ import annotations

import json
from typing import Any

from agent_engine_sdk_adk import App
from agent_engine_sdk_memory import MemoryAPIError

from agent_virtual_sysadmin import endlesswarden_data
from agent_virtual_sysadmin.context import (
    current_session_id,
    current_user_id,
    resolve_tenant,
    tenant_domain,
    tenant_filter,
    tenant_metadata,
    tenant_procedure,
)
from agent_virtual_sysadmin.seed_knowledge import seed_tenant

SOURCE = "ai_sysadmin"

# Partition-scoped memory types pulled into the tenant-scoped recall.
# taxonomic is excluded: it is project-wide and cannot be partition-scoped, so it
# is searched separately and filtered on tenant_id in code.
_RECALL_SOURCES = ("semantic", "episodic", "procedural")


def _ok(payload: Any) -> str:
    return json.dumps(payload, indent=2, default=str)


def _tenant_error(tenant_id: str) -> str:
    return _ok(
        {
            "error": f"Unknown tenant '{tenant_id}'.",
            "known_tenants": endlesswarden_data.known_tenants(),
            "hint": "Call get_request_context first and pass its tenant_id.",
        }
    )


def _known(tenant_id: str) -> bool:
    return endlesswarden_data.get_tenant(tenant_id) is not None


def _unwrap_context(context: Any) -> str:
    """Extract formatted text from a memory context response."""
    formatted = getattr(context, "formatted_context", context)
    return formatted if isinstance(formatted, str) else ""


def _filter_chunks_by_tenant(chunks: list[Any], tenant: str) -> list[Any]:
    """Keep only chunks whose stamped metadata belongs to ``tenant``."""
    kept = []
    for chunk in chunks:
        metadata = getattr(chunk, "metadata", None) or {}
        stamped = metadata.get("metadata", metadata)
        if isinstance(stamped, dict) and stamped.get("tenant_id") == tenant:
            kept.append(chunk)
    return kept


def _normalize_step(step: Any) -> dict[str, Any]:
    """Coerce a step into the memory server's ProceduralStep shape.

    A ProceduralStep requires ``step_type``, ``content``, and ``description``.
    Accept a bare string or a partial dict and fill in the missing fields.
    """
    if isinstance(step, str):
        return {"step_type": "instruction", "content": step, "description": step}
    if isinstance(step, dict):
        content = str(step.get("content") or step.get("text") or step.get("description") or "")
        return {
            "step_type": str(step.get("step_type") or "instruction"),
            "content": content,
            "description": str(step.get("description") or content),
        }
    return {"step_type": "instruction", "content": str(step), "description": str(step)}


def register(app: App) -> None:
    # -----------------------------------------------------------------------
    # Simulated EndlessWarden API tools (remote: run in the Tool Sandbox)
    # -----------------------------------------------------------------------

    @app.tool(is_local=False)
    def endlesswarden_query(tenant_id: str, query: str, limit: int = 50) -> str:
        """Run an EWQL-style read query against the EndlessWarden data model.

        Supported tables: devices, users, applications, execution.crashes,
        session.logins, alerts, dex.scores.

        Args:
            tenant_id: The customer (tenant) to query, from get_request_context.
            query: An EWQL-shaped query string, e.g. "SELECT * FROM execution.crashes".
            limit: Maximum rows to return (1-200).
        """
        if not _known(tenant_id):
            return _tenant_error(tenant_id)
        return _ok(endlesswarden_data.run_ewql_query(tenant_id, query, limit))

    @app.tool(is_local=False)
    def endlesswarden_list_devices(tenant_id: str, site: str = "", platform: str = "") -> str:
        """List endpoints for a tenant, optionally filtered by site or OS platform.

        Args:
            tenant_id: The customer (tenant), from get_request_context.
            site: Optional site filter, e.g. "London".
            platform: Optional OS substring, e.g. "Windows 10".
        """
        if not _known(tenant_id):
            return _tenant_error(tenant_id)
        devices = endlesswarden_data.list_devices(tenant_id, site, platform)
        return _ok({"device_count": len(devices), "devices": devices})

    @app.tool(is_local=False)
    def endlesswarden_get_device(tenant_id: str, device_name: str) -> str:
        """Get one device's hardware, OS, site, owner, metrics, and DEX score.

        Args:
            tenant_id: The customer (tenant), from get_request_context.
            device_name: The device name, e.g. "WKS-4471".
        """
        if not _known(tenant_id):
            return _tenant_error(tenant_id)
        device = endlesswarden_data.get_device(tenant_id, device_name)
        if device is None:
            return _ok({"error": f"No device named '{device_name}' in tenant '{tenant_id}'."})
        return _ok(device)

    @app.tool(is_local=False)
    def endlesswarden_list_applications(tenant_id: str, device_name: str = "") -> str:
        """List applications with crash/freeze counts, optionally for one device.

        Args:
            tenant_id: The customer (tenant), from get_request_context.
            device_name: Optional device name to narrow to affected applications.
        """
        if not _known(tenant_id):
            return _tenant_error(tenant_id)
        applications = endlesswarden_data.list_applications(tenant_id, device_name)
        return _ok({"application_count": len(applications), "applications": applications})

    @app.tool(is_local=False)
    def endlesswarden_find_affected_devices(
        tenant_id: str, application: str, version: str = ""
    ) -> str:
        """Find every device affected by an application's crashes (the fleet view).

        Correlates execution.crashes into the population of devices reporting the
        same application (and version), each with its owner, department, site,
        and DEX score. Use this to turn one report into a fleet-wide picture
        before proposing a remediation.

        Args:
            tenant_id: The customer (tenant), from get_request_context.
            application: The application name, e.g. "Microsoft Teams".
            version: Optional version to scope to, e.g. "24152.0.0".
        """
        if not _known(tenant_id):
            return _tenant_error(tenant_id)
        result = endlesswarden_data.find_affected_devices(tenant_id, application, version)
        if result is None:
            return _tenant_error(tenant_id)
        return _ok(result)

    @app.tool(is_local=False)
    def endlesswarden_get_dex_score(
        tenant_id: str, subject: str, subject_type: str = "device"
    ) -> str:
        """Return a DEX score (0-100), its band, and component breakdown.

        Args:
            tenant_id: The customer (tenant), from get_request_context.
            subject: A device name or a user email address.
            subject_type: Either "device" or "user".
        """
        if not _known(tenant_id):
            return _tenant_error(tenant_id)
        result = endlesswarden_data.get_dex_score(tenant_id, subject, subject_type)
        if result is None:
            return _ok(
                {"error": f"No DEX score for {subject_type} '{subject}' in tenant '{tenant_id}'."}
            )
        return _ok(result)

    @app.tool(is_local=False)
    def endlesswarden_list_alerts(tenant_id: str, severity: str = "") -> str:
        """List active EndlessWarden alerts, optionally filtered by severity.

        Args:
            tenant_id: The customer (tenant), from get_request_context.
            severity: Optional filter: "high", "medium", or "low".
        """
        if not _known(tenant_id):
            return _tenant_error(tenant_id)
        alerts = endlesswarden_data.list_alerts(tenant_id, severity)
        return _ok({"alert_count": len(alerts), "alerts": alerts})

    @app.tool(is_local=False)
    def endlesswarden_assess_alert_impact(tenant_id: str, alert_id: str) -> str:
        """Assess an alert's business impact as SIGNIFICANT, MODERATE, or MINIMAL.

        Args:
            tenant_id: The customer (tenant), from get_request_context.
            alert_id: The alert id, e.g. "ALT-9001".
        """
        if not _known(tenant_id):
            return _tenant_error(tenant_id)
        result = endlesswarden_data.assess_alert_impact(tenant_id, alert_id)
        if result is None:
            return _ok({"error": f"No alert '{alert_id}' in tenant '{tenant_id}'."})
        return _ok(result)

    @app.tool(is_local=False)
    def endlesswarden_run_remote_action(
        tenant_id: str, device_names: list[str], action: str
    ) -> str:
        """Execute a scripted remediation Remote Action on one or more endpoints.

        This is a MUTATING action. It requires human approval before it runs, and
        that approval covers every device in the list, so state the scope (which
        devices, which users, which departments) before you call it. A single
        device is a one-element list.

        Args:
            tenant_id: The customer (tenant), from get_request_context.
            device_names: The target devices, e.g. ["WKS-4471"], or a fleet list.
            action: The action to run, e.g. "Clear Teams cache and restart Teams".
        """
        if not _known(tenant_id):
            return _tenant_error(tenant_id)
        if not device_names:
            return _ok({"status": "error", "error": "device_names must not be empty."})
        executions = [
            endlesswarden_data.run_remote_action(tenant_id, device, action)
            for device in device_names
        ]
        failed = [e for e in executions if e.get("status") != "completed"]
        return _ok(
            {
                "status": "completed" if not failed else "partial",
                "action": action,
                "device_count": len(device_names),
                "succeeded": len(executions) - len(failed),
                "failed": len(failed),
                "executions": executions,
            }
        )

    # -----------------------------------------------------------------------
    # Context and memory tools (local: run in the Agent Sandbox)
    # -----------------------------------------------------------------------

    @app.tool()
    def get_request_context() -> str:
        """Return the caller's identity: user_id, tenant_id, and session_id.

        Call this first. Pass the returned tenant_id to every endlesswarden_* tool.
        """
        return _ok(
            {
                "user_id": current_user_id(),
                "tenant_id": resolve_tenant(),
                "session_id": current_session_id(),
            }
        )

    @app.tool()
    def recall_context(query: str) -> str:
        """Recall the tenant's shared knowledge: environment facts, past incidents, runbooks, and glossary terms.

        Results are filtered to the caller's tenant using the memory metadata
        partition key, so another customer's knowledge is never returned.

        Args:
            query: What to recall, e.g. "Teams crashes on the Finance fleet".
        """
        tenant = resolve_tenant()
        user_id = current_user_id()
        # Use build_context, not build_context_from_sources: only build_context
        # has the "memory read owned by tool" bypass, so it is the one context
        # path that may be called from inside a tool callback without starting an
        # exclusive durable activity that would conflict with the tool activity.
        parts: list[str] = []
        degraded = False
        try:
            context = app.memory.build_context(
                query=query,
                user_id=user_id,
                metadata_filter=tenant_filter(tenant),
                enabled_sources=set(_RECALL_SOURCES),
            )
        except MemoryAPIError:
            # The metadata partition key is not served by this memory server
            # (for example, the search index predates the key, or the runtime is
            # on an image that does not support partition keys). Degrade to a
            # user-scoped read, which is still tenant-isolated because user ids
            # are tenant-qualified ("<tenant>:<user>"), rather than failing.
            degraded = True
            context = app.memory.build_context(
                query=query,
                user_id=user_id,
                enabled_sources=set(_RECALL_SOURCES),
            )
        text = _unwrap_context(context)
        if text:
            parts.append(text)

        # Taxonomic (glossary) memory is project-wide and cannot be
        # partition-scoped, so search it and filter the returned records on their
        # tenant_id metadata instead.
        try:
            terms = _filter_chunks_by_tenant(
                app.memory.search_taxonomic(query=query, top_k=5), tenant
            )
        except MemoryAPIError:
            terms = []
        if terms:
            definitions = [getattr(chunk, "content", str(chunk)) for chunk in terms]
            parts.append("Glossary:\n" + "\n".join(f"- {d}" for d in definitions))

        result: dict[str, Any] = {"tenant_id": tenant, "found": bool(parts)}
        result["context"] = "\n\n".join(parts)
        if degraded:
            result["note"] = (
                "Tenant metadata filter unavailable on this memory server; "
                "results are scoped to the caller's user id only."
            )
        return _ok(result)

    @app.tool()
    def recall_personal_context(query: str) -> str:
        """Recall the caller's own memory, including knowledge learned automatically from past conversations.

        Scoped to the caller's user id (which is tenant-qualified), so it also
        surfaces memory the platform extracted in the background.

        Args:
            query: What to recall, e.g. "what do we know about our Windows fleet".
        """
        tenant = resolve_tenant()
        try:
            context = app.memory.build_context(query=query, user_id=current_user_id())
        except MemoryAPIError as error:
            return _ok({"tenant_id": tenant, "found": False, "error": str(error)})
        text = _unwrap_context(context)
        if not text:
            return _ok({"tenant_id": tenant, "found": False, "context": ""})
        return _ok({"tenant_id": tenant, "found": True, "context": text})

    @app.tool()
    def save_fact(text: str, label: str) -> str:
        """Save a durable fact about the tenant's environment for future sessions.

        Args:
            text: The fact, e.g. "Acme standard image is Windows 11 23H2".
            label: A short slug for the fact, e.g. "standard-image".
        """
        tenant = resolve_tenant()
        result = app.memory.save_semantic(
            text=text,
            label=f"{tenant}:{label}",
            source=SOURCE,
            metadata={**tenant_metadata(tenant), "type": "environment_fact"},
            user_id=current_user_id(),
        )
        if getattr(result, "acknowledged", result):
            return _ok({"status": "saved", "tenant_id": tenant, "label": label})
        return _ok({"status": "error", "error": "Memory is not enabled"})

    @app.tool()
    def save_runbook(procedure: str, description: str, content: str, steps_json: str = "[]") -> str:
        """Save or update a reusable remediation runbook for the tenant.

        Args:
            procedure: The runbook name, e.g. "slow-device-triage".
            description: One-line description of when to use it.
            content: The runbook body.
            steps_json: Optional JSON array of step objects.
        """
        tenant = resolve_tenant()
        try:
            raw_steps = json.loads(steps_json) if steps_json else []
        except json.JSONDecodeError:
            raw_steps = []
        if not isinstance(raw_steps, list):
            raw_steps = []
        steps = [_normalize_step(step) for step in raw_steps]
        # Procedural memory is unique per (org, procedure), so namespace the name
        # per tenant; skip if this tenant already has that runbook.
        scoped_name = tenant_procedure(procedure, tenant)
        user_id = current_user_id()
        try:
            if app.memory.get_procedure(scoped_name, user_id=user_id):
                return _ok(
                    {
                        "status": "exists",
                        "tenant_id": tenant,
                        "procedure": procedure,
                        "message": "Runbook already exists for this tenant.",
                    }
                )
        except Exception:  # noqa: BLE001 - a failed lookup must not block the write
            pass
        result = app.memory.save_procedure(
            procedure=scoped_name,
            description=description,
            content=content,
            steps=steps,
            tags=[tenant],
            visibility="org",
            metadata={**tenant_metadata(tenant), "type": "runbook"},
            user_id=user_id,
        )
        if getattr(result, "acknowledged", bool(result)):
            return _ok({"status": "saved", "tenant_id": tenant, "procedure": procedure})
        return _ok({"status": "error", "error": "Memory is not enabled"})

    @app.tool()
    def save_glossary_term(domain: str, term: str, definition: str) -> str:
        """Save a domain term definition (glossary entry) for the tenant.

        Args:
            domain: The domain, e.g. "dex".
            term: The term, e.g. "DEX Score".
            definition: The definition.
        """
        tenant = resolve_tenant()
        result = app.memory.save_taxonomic(
            domain=tenant_domain(domain, tenant),
            term=term,
            definition=definition,
            visibility="org",
            metadata={**tenant_metadata(tenant), "type": "glossary"},
            user_id=current_user_id(),
        )
        if getattr(result, "acknowledged", bool(result)):
            return _ok({"status": "saved", "tenant_id": tenant, "term": term})
        return _ok({"status": "error", "error": "Memory is not enabled"})

    @app.tool()
    def lookup_glossary(term: str, domain: str = "dex") -> str:
        """Look up a glossary term definition for the caller's tenant.

        Args:
            term: The term to look up, e.g. "DEX Score".
            domain: The domain to search, default "dex".
        """
        tenant = resolve_tenant()
        try:
            chunks = app.memory.search_taxonomic(
                query=term, domain=tenant_domain(domain, tenant), top_k=10
            )
        except MemoryAPIError as error:
            return _ok({"tenant_id": tenant, "found": False, "term": term, "error": str(error)})
        matches = _filter_chunks_by_tenant(chunks, tenant)
        if not matches:
            return _ok({"tenant_id": tenant, "found": False, "term": term})
        return _ok(
            {
                "tenant_id": tenant,
                "found": True,
                "term": term,
                "definitions": [getattr(chunk, "content", str(chunk)) for chunk in matches],
            }
        )

    @app.tool()
    def discover_runbook(query: str) -> str:
        """Find tenant-scoped remediation runbooks relevant to a query.

        Args:
            query: The situation, e.g. "device is slow".
        """
        tenant = resolve_tenant()
        user_id = current_user_id()
        try:
            candidates = app.memory.discover_procedures(
                query=query,
                user_id=user_id,
                metadata_filter=tenant_filter(tenant),
                top_k=5,
            )
        except MemoryAPIError:
            # Degrade to a user-scoped lookup when the metadata filter is not
            # served, rather than failing the tool.
            candidates = app.memory.discover_procedures(
                query=query,
                user_id=user_id,
                top_k=5,
            )
        return _ok({"tenant_id": tenant, "runbook_count": len(candidates), "runbooks": candidates})

    @app.tool()
    def seed_demo_knowledge() -> str:
        """Seed this tenant's demo knowledge: glossary terms, runbooks, and baseline facts.

        Idempotent: safe to run repeatedly. Use it to prepare a tenant before a demo.
        """
        tenant = resolve_tenant()
        counts = seed_tenant(app.memory, tenant, current_user_id(), source=SOURCE)
        return _ok({"status": "seeded", "tenant_id": tenant, **counts})
