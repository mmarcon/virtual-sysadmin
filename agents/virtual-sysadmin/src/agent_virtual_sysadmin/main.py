"""AI Sysadmin demo agent for Atlas Agent Engine (Google ADK).

A DEX troubleshooting copilot for EndlessWarden's DEX platform: it investigates a
reported issue by calling simulated EndlessWarden APIs, proposes a remediation, and
remembers what it learns -- scoped per customer (tenant) through memory metadata
filtering.
"""

from __future__ import annotations

import logging

from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools.function_tool import FunctionTool
from agent_engine_sdk_adk import App

from agent_virtual_sysadmin.llm import build_llm
from agent_virtual_sysadmin.system_message import SYSTEM_PROMPT
from agent_virtual_sysadmin.tools import register

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(message)s")
logger = logging.getLogger(__name__)
load_dotenv()

app = App(app_name="virtual-sysadmin", app_version="1.0.0")

register(app)

# Tools that mutate the customer's environment. These suspend the run for human
# approval before they execute. Names must match the registered @app.tool names.
CONFIRM_TOOLS = {"endlesswarden_run_remote_action"}


@app.entrypoint
def build_agent() -> LlmAgent:
    """Build the ADK agent."""
    logger.info("Building AI Sysadmin agent")

    # Wrap the secure-wrapped callables that app.tools() returns -- never the raw
    # @app.tool functions -- and gate the mutating ones behind human confirmation.
    tools = []
    gated: set[str] = set()
    for tool in app.tools():
        name = getattr(tool, "__name__", "")
        if name in CONFIRM_TOOLS:
            tools.append(FunctionTool(tool, require_confirmation=True))
            gated.add(name)
        else:
            tools.append(tool)

    missing = CONFIRM_TOOLS - gated
    if missing:
        # Fail closed: an ungated mutating tool is worse than a failed build.
        raise RuntimeError(
            f"Confirmation-gated tools were not found in app.tools(): {sorted(missing)}"
        )

    return LlmAgent(
        name="ai_sysadmin",
        description=(
            "AI Sysadmin for EndlessWarden: investigates digital-employee-experience "
            "issues with tenant-scoped memory and human-approved remediation."
        ),
        instruction=SYSTEM_PROMPT.strip(),
        model=app.llm(build_llm()),
        tools=tools,
    )


def main() -> None:
    """Run the AI Sysadmin agent."""
    app.run()


if __name__ == "__main__":
    main()
