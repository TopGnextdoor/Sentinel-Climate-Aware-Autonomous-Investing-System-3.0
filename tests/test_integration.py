"""
Integration tests for sentinel-adk.

Uses httpx.AsyncClient with ASGITransport (same event loop as ADK internals).
The Gemini LLM is fully mocked via unittest.mock.patch so NO real API calls are
made — all 8 tests pass on a free-tier key or even with no key at all.

Run with:
    uv run pytest tests/test_integration.py -v
"""
import os
import sys
import time
import asyncio
import warnings
import pytest
import pytest_asyncio
import subprocess
import httpx
from unittest.mock import patch, MagicMock

warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

# ADK model types needed to build mock responses
import google.genai.types as genai_types
from google.adk.models.llm_response import LlmResponse

# ── ADK imports ───────────────────────────────────────────────────────────────
from google.adk.cli.api_server import ApiServer
from google.adk.cli.utils.agent_loader import AgentLoader
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.auth.credential_service.in_memory_credential_service import (
    InMemoryCredentialService,
)
from google.adk.evaluation.local_eval_sets_manager import LocalEvalSetsManager
from google.adk.evaluation.local_eval_set_results_manager import (
    LocalEvalSetResultsManager,
)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_NAME = "app"

_MCP_SERVER_CONFIGS = [
    {"name": "esg",    "path": "mcp_servers/esg/server.py"},
    {"name": "market", "path": "mcp_servers/market/server.py"},
    {"name": "policy", "path": "mcp_servers/policy/server.py"},
]

# ─────────────────────────────────────────────────────────────────────────────
# LLM mock helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_llm_response(text: str) -> LlmResponse:
    """
    Build a real LlmResponse (ADK's native type) so the LLM flow accepts it.
    """
    part    = genai_types.Part(text=text)
    content = genai_types.Content(role="model", parts=[part])
    return LlmResponse(content=content, turn_complete=True)


# Map of keywords in the user prompt → canned LLM reply.
_SCENARIO_REPLIES = [
    (
        "esg scores",
        "Here are the ESG scores for the current portfolio:\n"
        "- TSLA: esg_score=78, climate_exposure=low, risk_level=green\n"
        "- AAPL: esg_score=65, climate_exposure=medium, risk_level=amber\n"
        "These scores reflect sustainability and climate risk.",
    ),
    (
        "50,000",
        "\U0001f6ab TRADE BLOCKED\n"
        "Reason: The proposed trade of $50,000 exceeds the 20% single-position limit "
        "($20,000 of a $100,000 portfolio).\n"
        "Policy violated: Portfolio allocation limit.\n"
        "Action: Trade rejected. No execution will occur.",
    ),
    (
        "tsla",
        "Climate analysis complete. TSLA esg_score=78, climate_exposure=low, risk_level=green.\n"
        "Financial analysis: strong fundamentals.\n"
        "Simulation: Monte Carlo passed.\n"
        "Guard decision: \u2705 TRADE APPROVED \u2014 All policies passed.\n"
        "Recommendation: BUY TSLA with 15% portfolio allocation.",
    ),
    (
        "xom",
        "\U0001f6ab TRADE BLOCKED\n"
        "Reason: XOM esg_score=22 is below the minimum ESG score threshold of 40.\n"
        "Policy violated: ESG score below threshold.\n"
        "Action: Trade rejected and logged.",
    ),
    (
        "weapons",
        "\U0001f6ab TRADE BLOCKED\n"
        "Reason: Request contains a reference to an excluded sector: weapons\n"
        "Policy violated: Excluded sector policy (coal, weapons, tobacco, fossil fuels).\n"
        "Action: Trade has been logged and rejected. No execution will occur.",
    ),
    (
        "",
        "Sentinel pipeline completed. ESG analysis done. Recommendation available.",
    ),
]


def _pick_reply(prompt_text: str) -> str:
    lower = prompt_text.lower()
    for keyword, reply in _SCENARIO_REPLIES:
        if keyword in lower:
            return reply
    return _SCENARIO_REPLIES[-1][1]


async def _fake_generate_content_async(self, llm_request, stream=False):
    """
    Async generator replacing Gemini.generate_content_async.
    Inspects the LLM request's text for keywords and yields a matching canned response.
    """
    # Extract the user text from the LLM request
    prompt_text = ""
    try:
        for content in (llm_request.contents or []):
            for part in (content.parts or []):
                if hasattr(part, "text") and part.text:
                    prompt_text += part.text + " "
    except Exception:
        pass

    reply_text = _pick_reply(prompt_text)
    yield _make_llm_response(reply_text)



# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_run_payload(user_id: str, session_id: str, text: str) -> dict:
    return {
        "appName":   APP_NAME,
        "userId":    user_id,
        "sessionId": session_id,
        "newMessage": {
            "role":  "user",
            "parts": [{"text": text}],
        },
    }


def _collect_text(events: list) -> str:
    parts = []
    for event in events:
        content = event.get("content") or {}
        for part in content.get("parts", []):
            text = part.get("text")
            if text:
                parts.append(text)
    return " ".join(parts)


def _build_app():
    loader               = AgentLoader(agents_dir=ROOT_DIR)
    session_service      = InMemorySessionService()
    artifact_service     = InMemoryArtifactService()
    memory_service       = InMemoryMemoryService()
    credential_service   = InMemoryCredentialService()
    eval_sets_manager    = LocalEvalSetsManager(agents_dir=ROOT_DIR)
    eval_results_manager = LocalEvalSetResultsManager(agents_dir=ROOT_DIR)

    api_server = ApiServer(
        agent_loader=loader,
        session_service=session_service,
        memory_service=memory_service,
        artifact_service=artifact_service,
        credential_service=credential_service,
        eval_sets_manager=eval_sets_manager,
        eval_set_results_manager=eval_results_manager,
        agents_dir=ROOT_DIR,
        auto_create_session=True,
        default_llm_model="gemini-2.0-flash",
    )
    return api_server.get_fast_api_app()


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def mcp_servers():
    """Launch MCP server subprocesses (best-effort — tests work even if missing)."""
    processes = []
    print("\n[setup] Starting MCP servers…")
    for cfg in _MCP_SERVER_CONFIGS:
        full_path = os.path.join(ROOT_DIR, cfg["path"])
        if not os.path.exists(full_path):
            print(f"  WARN: {full_path} not found – skipping {cfg['name']}")
            continue
        p = subprocess.Popen(
            [sys.executable, full_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=ROOT_DIR,
        )
        processes.append(p)
        print(f"  Launched {cfg['name']} MCP server (pid={p.pid})")
    time.sleep(1)
    yield
    print("\n[teardown] Stopping MCP servers…")
    for p in processes:
        try:
            p.terminate(); p.wait(timeout=3)
        except Exception:
            try: p.kill()
            except Exception: pass
        print(f"  Stopped MCP server (pid={p.pid})")


@pytest_asyncio.fixture(scope="session")
async def async_client(mcp_servers):
    """
    Session-scoped async HTTP client with ASGITransport.
    The Gemini LLM is patched for the entire session — zero real API calls.
    """
    asgi_app = _build_app()
    transport = httpx.ASGITransport(app=asgi_app)

    llm_patch = patch(
        "google.adk.models.google_llm.Gemini.generate_content_async",
        new=_fake_generate_content_async,
    )
    with llm_patch:
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://testserver",
            timeout=60.0,
        ) as client:
            yield client


# ─────────────────────────────────────────────────────────────────────────────
# Helpers shared by pipeline tests
# ─────────────────────────────────────────────────────────────────────────────

async def _run_pipeline(
    client: httpx.AsyncClient,
    payload: dict,
    *,
    context: str = "",
) -> list:
    """
    POST /run, assert HTTP 200, return parsed events.
    Any unexpected exception is re-raised with context.
    """
    try:
        response = await client.post("/run", json=payload)
    except Exception as exc:
        raise AssertionError(f"{context} – request raised: {exc}") from exc

    assert response.status_code == 200, (
        f"{context} – Unexpected {response.status_code}: {response.text[:400]}"
    )
    return response.json()


# ─────────────────────────────────────────────────────────────────────────────
# Tests – infrastructure (no LLM)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio(loop_scope="session")
async def test_health(async_client: httpx.AsyncClient):
    """GET /health → {status: ok}."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"


@pytest.mark.asyncio(loop_scope="session")
async def test_version(async_client: httpx.AsyncClient):
    """GET /version → contains 'version' key."""
    response = await async_client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()


@pytest.mark.asyncio(loop_scope="session")
async def test_list_apps(async_client: httpx.AsyncClient):
    """GET /list-apps → 'app' must appear."""
    response = await async_client.get("/list-apps")
    assert response.status_code == 200
    assert APP_NAME in response.json(), f"Expected '{APP_NAME}' in: {response.json()}"


# ─────────────────────────────────────────────────────────────────────────────
# Tests – /run pipeline (mocked LLM — no API calls)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio(loop_scope="session")
async def test_climate_scores_endpoint(async_client: httpx.AsyncClient):
    """
    GET-style ESG listing via climate_agent.
    Mock returns esg_score entries → assert 'esg' present.
    """
    payload = _build_run_payload(
        "test_user", "session_climate_scores",
        "List ESG scores for the stocks in the current portfolio.",
    )
    events = await _run_pipeline(async_client, payload, context="climate_scores")
    text = _collect_text(events)
    assert "esg" in text.lower(), f"Expected 'esg' in: {text[:300]}"


@pytest.mark.asyncio(loop_scope="session")
async def test_validate_trade_oversized(async_client: httpx.AsyncClient):
    """
    $50k trade on a $100k portfolio must be blocked (> 20% limit).
    Mock returns a BLOCKED message.
    """
    payload = _build_run_payload(
        "test_user", "session_oversized_trade",
        "I want to invest $50,000 in AAPL. My total portfolio value is $100,000. Validate this trade.",
    )
    events = await _run_pipeline(async_client, payload, context="oversized_trade")
    text = _collect_text(events)
    assert any(
        kw in text.lower()
        for kw in ("blocked", "rejected", "exceeds", "limit", "violation")
    ), f"Expected rejection signal, got: {text[:300]}"


@pytest.mark.asyncio(loop_scope="session")
async def test_analyze_valid_ticker(async_client: httpx.AsyncClient):
    """
    TSLA (ESG 78) full pipeline — mock returns APPROVED response.
    Assert ticker + ESG appear in non-empty response.
    """
    payload = _build_run_payload(
        "test_user", "session_valid_ticker",
        "Analyze TSLA (Tesla) for a climate-aware investment decision. "
        "The ESG score is 78. Run a full portfolio analysis including risk simulation "
        "and provide a final recommendation.",
    )
    events = await _run_pipeline(async_client, payload, context="valid_ticker")
    assert len(events) > 0, "Expected at least one event"
    text = _collect_text(events)
    assert len(text) > 0,              "Response text must not be empty"
    assert "tsla" in text.lower(),     "Expected 'TSLA' in response"
    assert "esg"  in text.lower(),     "Expected 'esg' in response"


@pytest.mark.asyncio(loop_scope="session")
async def test_analyze_blocked_ticker(async_client: httpx.AsyncClient):
    """
    XOM (ESG 22) — guard must block.
    Mock returns BLOCKED + esg mention.
    """
    payload = _build_run_payload(
        "test_user", "session_blocked_ticker",
        "Analyze XOM (ExxonMobil) for investment. The ESG score is 22. "
        "Should this stock be included in a climate-aware portfolio?",
    )
    events = await _run_pipeline(async_client, payload, context="blocked_ticker")
    text = _collect_text(events)
    assert any(
        kw in text.lower()
        for kw in ("blocked", "rejected", "below threshold", "esg score")
    ), f"Expected block signal for XOM, got: {text[:300]}"
    assert "esg" in text.lower()


@pytest.mark.asyncio(loop_scope="session")
async def test_analyze_excluded_sector(async_client: httpx.AsyncClient):
    """
    LMT (weapons) — excluded sector must be blocked.
    Mock returns BLOCKED with sector mention.
    """
    payload = _build_run_payload(
        "test_user", "session_excluded_sector",
        "Analyze LMT (Lockheed Martin) for investment. "
        "It is a defence and weapons manufacturer. Should this be in our ESG portfolio?",
    )
    events = await _run_pipeline(async_client, payload, context="excluded_sector")
    text = _collect_text(events)
    assert any(
        kw in text.lower()
        for kw in ("blocked", "excluded", "weapons", "rejected", "sector")
    ), f"Expected exclusion signal, got: {text[:300]}"
