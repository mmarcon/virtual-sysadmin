"""LLM provider selection for virtual-sysadmin."""

from __future__ import annotations

import os

from google.adk.models.lite_llm import LiteLlm
from google.adk.models import BaseLlm

MODEL = "openai/responses/gpt-6.1-sol"


def build_llm(temperature: float = 0) -> BaseLlm:
    api_key = os.environ.get("LLM_API_KEY", "")
    if not api_key:
        raise RuntimeError("LLM_API_KEY is missing; add it to .env or project secrets")
    # Endpoint deployments use opaque aliases whose model family cannot be
    # inferred, so the provider default governs; the LangGraph gateway builders
    # omit temperature for the same reason.
    #
    # parallel_tool_calls=False: the durable ADK adapter rejects overlapping
    # (concurrent) tool activities, and ADK executes every function call in one
    # model response concurrently. Disabling parallel tool calls makes the model
    # emit at most one tool call per turn, which the adapter accepts.
    return LiteLlm(
        model=MODEL,
        api_key=api_key,
        api_base="https://grove-gateway-prod.azure-api.net/grove-foundry-prod/openai/v1",
        extra_headers={"api-key": api_key},
        parallel_tool_calls=False,
    )
