"""Deterministic, tenant-scoped mock of the EndlessWarden data model.

This module stands in for the EndlessWarden platform APIs (EWQL, Remote Actions,
alerts, DEX scores) so the demo can "call" a realistic backend without network
access. Everything is static: no randomness and no clock reads at import, so
the agent sandbox and the tool sandbox always agree.

Shape follows the EndlessWarden EWQL data model: ``devices``, ``users``,
``applications``, ``execution.crashes``, ``session.logins``, ``alerts``,
``dex.scores``, and ``remote_actions``. Every tenant (customer) has its own
slice of the data under :data:`TENANTS`.
"""

from __future__ import annotations

import hashlib
from typing import Any

SUPPORTED_TABLES = [
    "devices",
    "users",
    "applications",
    "execution.crashes",
    "session.logins",
    "alerts",
    "dex.scores",
    "remote_actions",
]

# ---------------------------------------------------------------------------
# Tenant data
# ---------------------------------------------------------------------------

TENANTS: dict[str, dict[str, Any]] = {
    "acme-corp": {
        "display_name": "Acme Corp",
        "sites": ["London", "Berlin", "Stockholm", "Tokyo"],
        "devices": [
            {
                "name": "WKS-4471",
                "owner": "priya.nair@acme.example",
                "department": "Finance",
                "site": "London",
                "platform": "Windows 11 23H2",
                "hardware_model": "Lenovo ThinkPad T14 Gen 4",
                "memory_gb": 16,
                "collector_version": "24.3",
                "dex": {
                    "score": 42,
                    "endpoint": 40,
                    "applications": 31,
                    "collaboration": 55,
                    "sentiment": 48,
                },
                "metrics": {
                    "cpu_usage_pct": 78,
                    "ram_usage_pct": 88,
                    "disk_free_pct": 11,
                    "disk_queue_length": 4.2,
                },
                "boot_seconds": 92,
                "logon_seconds": 71,
            },
            {
                "name": "WKS-2210",
                "owner": "tom.becker@acme.example",
                "department": "Sales",
                "site": "Berlin",
                "platform": "Windows 11 23H2",
                "hardware_model": "Dell Latitude 5440",
                "memory_gb": 16,
                "collector_version": "24.3",
                "dex": {
                    "score": 38,
                    "endpoint": 33,
                    "applications": 29,
                    "collaboration": 47,
                    "sentiment": 44,
                },
                "metrics": {
                    "cpu_usage_pct": 91,
                    "ram_usage_pct": 82,
                    "disk_free_pct": 7,
                    "disk_queue_length": 5.8,
                },
                "boot_seconds": 110,
                "logon_seconds": 95,
            },
            {
                "name": "MAC-1108",
                "owner": "sara.lindqvist@acme.example",
                "department": "Design",
                "site": "Stockholm",
                "platform": "macOS 14.5",
                "hardware_model": "MacBook Pro 14 (M3)",
                "memory_gb": 32,
                "collector_version": "24.2",
                "dex": {
                    "score": 71,
                    "endpoint": 74,
                    "applications": 68,
                    "collaboration": 79,
                    "sentiment": 65,
                },
                "metrics": {
                    "cpu_usage_pct": 34,
                    "ram_usage_pct": 55,
                    "disk_free_pct": 38,
                    "disk_queue_length": 0.9,
                },
                "boot_seconds": 41,
                "logon_seconds": 28,
            },
            {
                "name": "WKS-3390",
                "owner": "diego.alvarez@acme.example",
                "department": "Finance",
                "site": "London",
                "platform": "Windows 10 22H2",
                "hardware_model": "HP EliteBook 840 G8",
                "memory_gb": 8,
                "collector_version": "23.9",
                "dex": {
                    "score": 33,
                    "endpoint": 27,
                    "applications": 30,
                    "collaboration": 41,
                    "sentiment": 39,
                },
                "metrics": {
                    "cpu_usage_pct": 84,
                    "ram_usage_pct": 93,
                    "disk_free_pct": 9,
                    "disk_queue_length": 6.1,
                },
                "boot_seconds": 128,
                "logon_seconds": 102,
            },
            {
                "name": "WKS-5122",
                "owner": "hana.sato@acme.example",
                "department": "Engineering",
                "site": "Tokyo",
                "platform": "Windows 11 24H2",
                "hardware_model": "Lenovo ThinkPad X1 Carbon Gen 12",
                "memory_gb": 32,
                "collector_version": "24.3",
                "dex": {
                    "score": 82,
                    "endpoint": 85,
                    "applications": 81,
                    "collaboration": 84,
                    "sentiment": 78,
                },
                "metrics": {
                    "cpu_usage_pct": 22,
                    "ram_usage_pct": 48,
                    "disk_free_pct": 52,
                    "disk_queue_length": 0.6,
                },
                "boot_seconds": 33,
                "logon_seconds": 24,
            },
        ],
        "applications": [
            {
                "name": "Microsoft Teams",
                "vendor": "Microsoft",
                "crashes_7d": 148,
                "freezes_7d": 62,
                "affected_devices": ["WKS-4471", "WKS-2210", "WKS-3390"],
                "avg_response_ms": 1840,
                "error_rate": 0.11,
            },
            {
                "name": "Microsoft Outlook",
                "vendor": "Microsoft",
                "crashes_7d": 12,
                "freezes_7d": 9,
                "affected_devices": ["WKS-2210"],
                "avg_response_ms": 620,
                "error_rate": 0.02,
            },
            {
                "name": "Google Chrome",
                "vendor": "Google",
                "crashes_7d": 7,
                "freezes_7d": 4,
                "affected_devices": ["WKS-3390"],
                "avg_response_ms": 410,
                "error_rate": 0.01,
            },
            {
                "name": "Zoom Workplace",
                "vendor": "Zoom",
                "crashes_7d": 1,
                "freezes_7d": 15,
                "affected_devices": ["MAC-1108", "WKS-2210"],
                "avg_response_ms": 520,
                "error_rate": 0.01,
            },
        ],
        "crashes": [
            {
                "device": "WKS-4471",
                "binary": "teams.exe",
                "application": "Microsoft Teams",
                "count_7d": 43,
                "first_seen": "2026-11-08",
                "error_code": "0xc0000005",
                "version": "24152.0.0",
            },
            {
                "device": "WKS-2210",
                "binary": "teams.exe",
                "application": "Microsoft Teams",
                "count_7d": 27,
                "first_seen": "2026-11-09",
                "error_code": "0xc0000005",
                "version": "24152.0.0",
            },
            {
                "device": "WKS-3390",
                "binary": "teams.exe",
                "application": "Microsoft Teams",
                "count_7d": 19,
                "first_seen": "2026-11-10",
                "error_code": "0xc0000005",
                "version": "24152.0.0",
            },
            {
                "device": "WKS-4471",
                "binary": "outlook.exe",
                "application": "Microsoft Outlook",
                "count_7d": 6,
                "first_seen": "2026-11-11",
                "error_code": "0xc0000005",
                "version": "1.2024.1108",
            },
            {
                "device": "MAC-1108",
                "binary": "Microsoft Teams",
                "application": "Microsoft Teams",
                "count_7d": 2,
                "first_seen": "2026-11-12",
                "error_code": "-10670",
                "version": "24152.0.0",
            },
        ],
        "logins": [
            {
                "device": "WKS-4471",
                "user": "priya.nair@acme.example",
                "logon_seconds": 71,
                "failed_logins_7d": 0,
            },
            {
                "device": "WKS-2210",
                "user": "tom.becker@acme.example",
                "logon_seconds": 95,
                "failed_logins_7d": 2,
            },
            {
                "device": "WKS-3390",
                "user": "diego.alvarez@acme.example",
                "logon_seconds": 102,
                "failed_logins_7d": 5,
            },
            {
                "device": "WKS-5122",
                "user": "hana.sato@acme.example",
                "logon_seconds": 24,
                "failed_logins_7d": 0,
            },
        ],
        "alerts": [
            {
                "id": "ALT-9001",
                "severity": "high",
                "title": "Microsoft Teams crash spike across Finance",
                "scope": "application",
                "target": "Microsoft Teams",
                "affected_devices": ["WKS-4471", "WKS-2210", "WKS-3390"],
                "impact": "SIGNIFICANT",
                "created": "2026-11-16",
                "monitor": "App crash count > 20 on > 2 devices",
            },
            {
                "id": "ALT-9002",
                "severity": "medium",
                "title": "Slow logons on the Windows 10 fleet",
                "scope": "device",
                "target": "WKS-3390",
                "affected_devices": ["WKS-3390"],
                "impact": "MODERATE",
                "created": "2026-11-15",
                "monitor": "Logon duration > 90s for 3 consecutive days",
            },
            {
                "id": "ALT-9003",
                "severity": "low",
                "title": "System disk below 10% free",
                "scope": "device",
                "target": "WKS-2210",
                "affected_devices": ["WKS-2210"],
                "impact": "MINIMAL",
                "created": "2026-11-14",
                "monitor": "Disk free < 10%",
            },
        ],
    },
    "globex": {
        "display_name": "Globex",
        "sites": ["Madrid", "Osaka", "Lagos"],
        "devices": [
            {
                "name": "GLX-7012",
                "owner": "marta.silva@globex.example",
                "department": "Operations",
                "site": "Madrid",
                "platform": "Windows 11 23H2",
                "hardware_model": "Dell Latitude 5540",
                "memory_gb": 16,
                "collector_version": "24.3",
                "dex": {
                    "score": 55,
                    "endpoint": 52,
                    "applications": 58,
                    "collaboration": 61,
                    "sentiment": 50,
                },
                "metrics": {
                    "cpu_usage_pct": 61,
                    "ram_usage_pct": 72,
                    "disk_free_pct": 24,
                    "disk_queue_length": 2.1,
                },
                "boot_seconds": 58,
                "logon_seconds": 44,
            },
            {
                "name": "GLX-7044",
                "owner": "ken.ito@globex.example",
                "department": "R&D",
                "site": "Osaka",
                "platform": "macOS 15.1",
                "hardware_model": "MacBook Pro 16 (M3 Max)",
                "memory_gb": 48,
                "collector_version": "24.3",
                "dex": {
                    "score": 68,
                    "endpoint": 70,
                    "applications": 64,
                    "collaboration": 72,
                    "sentiment": 66,
                },
                "metrics": {
                    "cpu_usage_pct": 45,
                    "ram_usage_pct": 61,
                    "disk_free_pct": 33,
                    "disk_queue_length": 1.4,
                },
                "boot_seconds": 37,
                "logon_seconds": 26,
            },
            {
                "name": "GLX-7090",
                "owner": "amara.okafor@globex.example",
                "department": "Finance",
                "site": "Lagos",
                "platform": "Windows 11 24H2",
                "hardware_model": "HP ZBook Firefly 14",
                "memory_gb": 16,
                "collector_version": "24.3",
                "dex": {
                    "score": 47,
                    "endpoint": 44,
                    "applications": 49,
                    "collaboration": 45,
                    "sentiment": 51,
                },
                "metrics": {
                    "cpu_usage_pct": 73,
                    "ram_usage_pct": 79,
                    "disk_free_pct": 18,
                    "disk_queue_length": 3.3,
                },
                "boot_seconds": 74,
                "logon_seconds": 52,
            },
        ],
        "applications": [
            {
                "name": "Cisco Secure Client (VPN)",
                "vendor": "Cisco",
                "crashes_7d": 21,
                "freezes_7d": 8,
                "affected_devices": ["GLX-7012"],
                "avg_response_ms": 980,
                "error_rate": 0.08,
            },
            {
                "name": "Slack",
                "vendor": "Salesforce",
                "crashes_7d": 5,
                "freezes_7d": 3,
                "affected_devices": ["GLX-7090"],
                "avg_response_ms": 360,
                "error_rate": 0.01,
            },
            {
                "name": "Microsoft Teams",
                "vendor": "Microsoft",
                "crashes_7d": 4,
                "freezes_7d": 6,
                "affected_devices": ["GLX-7044"],
                "avg_response_ms": 540,
                "error_rate": 0.01,
            },
        ],
        "crashes": [
            {
                "device": "GLX-7012",
                "binary": "vpnagent.exe",
                "application": "Cisco Secure Client (VPN)",
                "count_7d": 21,
                "first_seen": "2026-11-13",
                "error_code": "0x00000000",
                "version": "5.0.3",
            },
            {
                "device": "GLX-7090",
                "binary": "slack.exe",
                "application": "Slack",
                "count_7d": 5,
                "first_seen": "2026-11-14",
                "error_code": "0xc0000005",
                "version": "4.41.98",
            },
            {
                "device": "GLX-7044",
                "binary": "Microsoft Teams",
                "application": "Microsoft Teams",
                "count_7d": 4,
                "first_seen": "2026-11-15",
                "error_code": "-10670",
                "version": "24152.0.0",
            },
        ],
        "logins": [
            {
                "device": "GLX-7012",
                "user": "marta.silva@globex.example",
                "logon_seconds": 44,
                "failed_logins_7d": 1,
            },
            {
                "device": "GLX-7090",
                "user": "amara.okafor@globex.example",
                "logon_seconds": 52,
                "failed_logins_7d": 3,
            },
        ],
        "alerts": [
            {
                "id": "GLX-ALT-01",
                "severity": "medium",
                "title": "VPN disconnect spike on Operations laptops",
                "scope": "application",
                "target": "Cisco Secure Client (VPN)",
                "affected_devices": ["GLX-7012"],
                "impact": "MODERATE",
                "created": "2026-11-16",
                "monitor": "VPN disconnects > 10 in 24h",
            },
            {
                "id": "GLX-ALT-02",
                "severity": "low",
                "title": "Slack freeze reports rising",
                "scope": "application",
                "target": "Slack",
                "affected_devices": ["GLX-7090"],
                "impact": "MINIMAL",
                "created": "2026-11-15",
                "monitor": "App freeze count > 3 on > 0 devices",
            },
        ],
    },
    "endlesswarden-demo": {
        "display_name": "EndlessWarden Demo",
        "sites": ["Zurich"],
        "devices": [
            {
                "name": "DEMO-0001",
                "owner": "demo.user@endlesswarden.example",
                "department": "IT",
                "site": "Zurich",
                "platform": "Windows 11 24H2",
                "hardware_model": "Microsoft Surface Laptop 6",
                "memory_gb": 16,
                "collector_version": "24.3",
                "dex": {
                    "score": 64,
                    "endpoint": 62,
                    "applications": 66,
                    "collaboration": 68,
                    "sentiment": 60,
                },
                "metrics": {
                    "cpu_usage_pct": 40,
                    "ram_usage_pct": 58,
                    "disk_free_pct": 41,
                    "disk_queue_length": 1.2,
                },
                "boot_seconds": 44,
                "logon_seconds": 31,
            },
        ],
        "applications": [
            {
                "name": "Microsoft Teams",
                "vendor": "Microsoft",
                "crashes_7d": 3,
                "freezes_7d": 2,
                "affected_devices": ["DEMO-0001"],
                "avg_response_ms": 420,
                "error_rate": 0.01,
            },
        ],
        "crashes": [
            {
                "device": "DEMO-0001",
                "binary": "teams.exe",
                "application": "Microsoft Teams",
                "count_7d": 3,
                "first_seen": "2026-11-15",
                "error_code": "0xc0000005",
                "version": "24152.0.0",
            },
        ],
        "logins": [
            {
                "device": "DEMO-0001",
                "user": "demo.user@endlesswarden.example",
                "logon_seconds": 31,
                "failed_logins_7d": 0,
            },
        ],
        "alerts": [],
    },
}


def known_tenants() -> list[str]:
    """Return the tenant ids this mock backend serves."""
    return sorted(TENANTS)


def get_tenant(tenant_id: str) -> dict[str, Any] | None:
    """Return a tenant's data slice, or ``None`` if the tenant is unknown."""
    return TENANTS.get(tenant_id)


def dex_band(score: int) -> str:
    """Map a DEX score (0-100) to its EndlessWarden band label."""
    if score <= 30:
        return "frustrating"
    if score <= 70:
        return "average"
    return "good"


# ---------------------------------------------------------------------------
# Query helpers (used by the tools)
# ---------------------------------------------------------------------------


def list_devices(tenant_id: str, site: str = "", platform: str = "") -> list[dict[str, Any]]:
    """List devices for a tenant, optionally filtered by site or OS platform."""
    tenant = get_tenant(tenant_id)
    if tenant is None:
        return []
    devices = tenant["devices"]
    if site:
        devices = [d for d in devices if d["site"].lower() == site.lower()]
    if platform:
        devices = [d for d in devices if platform.lower() in d["platform"].lower()]
    return devices


def get_device(tenant_id: str, device_name: str) -> dict[str, Any] | None:
    """Return a single device by name."""
    for device in list_devices(tenant_id):
        if device["name"].lower() == device_name.strip().lower():
            return device
    return None


def list_applications(tenant_id: str, device_name: str = "") -> list[dict[str, Any]]:
    """List applications, optionally narrowed to those affected on one device."""
    tenant = get_tenant(tenant_id)
    if tenant is None:
        return []
    applications = tenant["applications"]
    if device_name:
        needle = device_name.strip().lower()
        applications = [
            a for a in applications if any(d.lower() == needle for d in a["affected_devices"])
        ]
    return applications


def get_dex_score(
    tenant_id: str, subject: str, subject_type: str = "device"
) -> dict[str, Any] | None:
    """Return a DEX score with its band and component breakdown."""
    tenant = get_tenant(tenant_id)
    if tenant is None:
        return None
    subject_type = subject_type.strip().lower()
    if subject_type == "device":
        device = get_device(tenant_id, subject)
        if device is None:
            return None
        components = device["dex"]
        return {
            "subject": device["name"],
            "subject_type": "device",
            "owner": device["owner"],
            "site": device["site"],
            "score": components["score"],
            "band": dex_band(components["score"]),
            "components": {k: v for k, v in components.items() if k != "score"},
        }
    # User-scoped score: average the DEX scores of the user's devices.
    needle = subject.strip().lower()
    owned = [d for d in tenant["devices"] if d["owner"].lower() == needle]
    if not owned:
        return None
    score = round(sum(d["dex"]["score"] for d in owned) / len(owned))
    return {
        "subject": subject,
        "subject_type": "user",
        "devices": [d["name"] for d in owned],
        "score": score,
        "band": dex_band(score),
    }


def list_alerts(tenant_id: str, severity: str = "") -> list[dict[str, Any]]:
    """List alerts for a tenant, optionally filtered by severity."""
    tenant = get_tenant(tenant_id)
    if tenant is None:
        return []
    alerts = tenant["alerts"]
    if severity:
        alerts = [a for a in alerts if a["severity"].lower() == severity.strip().lower()]
    return alerts


def assess_alert_impact(tenant_id: str, alert_id: str) -> dict[str, Any] | None:
    """Return an alert's business-impact assessment and the rationale behind it."""
    for alert in list_alerts(tenant_id):
        if alert["id"].lower() == alert_id.strip().lower():
            affected = len(alert["affected_devices"])
            return {
                "alert_id": alert["id"],
                "title": alert["title"],
                "impact": alert["impact"],
                "severity": alert["severity"],
                "affected_device_count": affected,
                "affected_devices": alert["affected_devices"],
                "rationale": (
                    f"{affected} device(s) affected; monitor '{alert['monitor']}' "
                    f"fired on {alert['created']}."
                ),
            }
    return None


def run_ewql_query(tenant_id: str, query: str, limit: int = 50) -> dict[str, Any]:
    """Route a small set of EWQL-shaped queries to the mock data tables.

    This is a deliberately small stand-in for the real EWQL API: it matches on
    the table name and a few filters rather than parsing SQL. Unknown tables
    return a structured error listing the supported ones.
    """
    tenant = get_tenant(tenant_id)
    if tenant is None:
        return {"error": f"Unknown tenant '{tenant_id}'.", "known_tenants": known_tenants()}

    normalized = query.lower()
    limit = max(1, min(limit, 200))

    if "execution.crashes" in normalized or "crashes" in normalized:
        table, rows = "execution.crashes", tenant["crashes"]
    elif "session.logins" in normalized or "logins" in normalized or "logon" in normalized:
        table, rows = "session.logins", tenant["logins"]
    elif "applications" in normalized:
        table, rows = "applications", tenant["applications"]
    elif "alerts" in normalized:
        table, rows = "alerts", tenant["alerts"]
    elif "dex" in normalized:
        table, rows = (
            "dex.scores",
            [
                {
                    "device": d["name"],
                    "owner": d["owner"],
                    "score": d["dex"]["score"],
                    "band": dex_band(d["dex"]["score"]),
                }
                for d in tenant["devices"]
            ],
        )
    elif "users" in normalized:
        table, rows = (
            "users",
            [
                {
                    "upn": d["owner"],
                    "department": d["department"],
                    "site": d["site"],
                    "device": d["name"],
                }
                for d in tenant["devices"]
            ],
        )
    elif "devices" in normalized:
        table, rows = (
            "devices",
            [
                {
                    "name": d["name"],
                    "owner": d["owner"],
                    "site": d["site"],
                    "platform": d["platform"],
                    "metrics": d["metrics"],
                }
                for d in tenant["devices"]
            ],
        )
    else:
        return {
            "error": f"Could not map the query to a known table: {query!r}",
            "supported_tables": SUPPORTED_TABLES,
        }

    return {"table": table, "row_count": min(len(rows), limit), "rows": rows[:limit]}


def run_remote_action(tenant_id: str, device_name: str, action: str) -> dict[str, Any]:
    """Simulate triggering an EndlessWarden Remote Action on an endpoint.

    Deterministic and side-effect free: it returns a plausible execution record
    without mutating the dataset, so the agent and tool sandboxes stay in sync.
    """
    tenant = get_tenant(tenant_id)
    if tenant is None:
        return {"status": "error", "error": f"Unknown tenant '{tenant_id}'."}
    device = get_device(tenant_id, device_name)
    if device is None:
        return {
            "status": "error",
            "error": f"No device named '{device_name}' in tenant '{tenant_id}'.",
        }

    seed = f"{tenant_id}|{device['name']}|{action}".encode()
    digest = int(hashlib.sha1(seed).hexdigest(), 16)
    execution_id = f"RA-{digest % 100000:05d}"
    return {
        "status": "completed",
        "execution_id": execution_id,
        "tenant": tenant_id,
        "device": device["name"],
        "action": action,
        "result": f"Remote Action '{action}' executed successfully on {device['name']}.",
        "duration_seconds": 12,
    }
