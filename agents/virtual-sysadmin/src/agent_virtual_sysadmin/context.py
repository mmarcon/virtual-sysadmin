"""Tenant resolution and memory-scoping helpers for the AI Sysadmin demo.

Multi-tenancy model
-------------------
Every EndlessWarden customer (tenant) shares one Atlas Agent Engine memory store.
Isolation is enforced by two rules, both applied through the helpers here:

* every memory write stamps ``metadata={"tenant_id": <tenant>}``, and
* every memory read filters on the fully qualified path
  ``{"metadata.tenant_id": <tenant>}``.

The ``tenant_id`` metadata attribute is declared as a filterable partition key
in ``project-config.yaml`` (``memory.metadata_partition_key``), which is what
lets the filter run inside the search index.
"""

from __future__ import annotations

from typing import Any

from agent_engine_runner_shared.context import (
    get_current_custom_headers,
    get_current_session_id,
    get_current_user_id,
)

# Tenant used when the caller supplies neither a header nor a tenant-scoped user id.
DEFAULT_TENANT = "endlesswarden-demo"

# The API Gateway strips the ``X-Mdb-Agent-Engine-Custom-`` prefix and lowercases
# the remainder, so ``X-Mdb-Agent-Engine-Custom-Tenant-Id`` arrives as "tenant-id".
TENANT_HEADER = "tenant-id"

# A user id may encode its tenant as "<tenant>:<user>", e.g. "acme-corp:alice".
IDENTITY_SEPARATOR = ":"


def tenant_from_user_id(user_id: str | None) -> str:
    """Return the tenant encoded in ``user_id`` (``tenant:user``), else the default."""
    if user_id and IDENTITY_SEPARATOR in user_id:
        tenant = user_id.split(IDENTITY_SEPARATOR, 1)[0].strip()
        if tenant:
            return tenant
    return DEFAULT_TENANT


def resolve_tenant() -> str:
    """Resolve the active tenant for the current request.

    Precedence:

    1. The custom header ``tenant-id`` (sent as
       ``X-Mdb-Agent-Engine-Custom-Tenant-Id``) -- the production path.
    2. The tenant encoded in the user id as ``tenant:user`` -- the local
       Playground / ``agentengine invoke --user-id`` path.
    3. :data:`DEFAULT_TENANT`.

    Custom headers are readable only from in-process (local) tools, so this must
    be called from a tool registered with the default ``is_local=True``.
    """
    header_tenant = get_current_custom_headers().get(TENANT_HEADER, "").strip()
    if header_tenant:
        return header_tenant
    return tenant_from_user_id(get_current_user_id())


def current_user_id() -> str:
    """Return the caller's user id, or a stable placeholder when unset."""
    return get_current_user_id() or "anonymous"


def current_session_id() -> str:
    """Return the current session id, or a stable placeholder when unset."""
    return get_current_session_id() or "no-session"


def tenant_metadata(tenant: str) -> dict[str, Any]:
    """Metadata stamped on every memory write so the record is tenant-scoped."""
    return {"tenant_id": tenant}


def tenant_domain(domain: str, tenant: str) -> str:
    """Namespace a taxonomic domain by tenant.

    Taxonomic memory is unique per (org, domain, term) and is project-wide, so a
    plain ``dex`` domain would collide across tenants. Prefixing the domain with
    the tenant keeps each customer's glossary separate.
    """
    return f"{domain}-{tenant}"


def tenant_procedure(procedure: str, tenant: str) -> str:
    """Namespace a procedural memory name by tenant.

    Procedural memory is unique per (org, procedure) and is project-wide, so a
    plain ``slow-device-triage`` would collide across tenants. Suffixing the
    name with the tenant keeps each customer's runbooks separate.
    """
    return f"{procedure}-{tenant}"


def tenant_filter(tenant: str) -> dict[str, Any]:
    """Metadata filter for reads.

    The key is the qualified index path (``metadata.tenant_id``), matching the
    attribute declared under ``memory.metadata_partition_key`` in
    ``project-config.yaml``. Nothing is prefixed for you, so the ``metadata.``
    segment is required.
    """
    return {"metadata.tenant_id": tenant}
