"""
Sentinel Pipeline — Standalone /chat handler.

Bypasses the ADK LLM pipeline entirely.  Each agent step is executed as a
direct Python function call (climate → financial → simulation → portfolio →
guard → explain).  Only the final "explain" step calls an LLM (via
OpenRouter) to produce a natural-language summary.

This removes the dependency on litellm/ADK model routing and avoids every
free-model-availability issue we have been hitting.
"""

import gc
import os
import json
import random
import urllib.request
import asyncio
import traceback

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.utils.quota_tracker import get_quota_summary

# ── Service imports (all local, no LLM needed) ──────────────────────────
from app.services.climate_data import fetch_climate_metrics
from app.services.risk import calculate_market_trends
from app.services.simulation_engine import run_monte_carlo_sim
from app.services.optimizer import calculate_allocation
from app.services.market_data import get_multiple_prices, get_stock_price
from app.services.policy_service import enforce_constraints

# ── Guard helpers ────────────────────────────────────────────────────────
EXCLUDED_SECTORS = {"coal", "weapons", "firearms", "tobacco", "fossil fuels",
                    "oil sands", "tar sands"}

def _check_intent(user_request: str):
    lower = user_request.lower()
    for sector in EXCLUDED_SECTORS:
        if sector in lower:
            return {"blocked": True, "matched_sector": sector,
                    "reason": f"Request mentions excluded sector: '{sector}'."}
    return {"blocked": False, "matched_sector": None, "reason": "OK"}


# ── OpenRouter LLM call (with multi-model fallback) ─────────────────────
OPENROUTER_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemma-4-31b-it:free",
    "google/gemma-4-26b-a4b-it:free",
    "qwen/qwen3-coder:free",
    "openai/gpt-oss-120b:free",
    "meta-llama/llama-3.2-3b-instruct:free",
]


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call OpenRouter with automatic fallback across free models."""
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        return "(LLM unavailable — no OPENROUTER_API_KEY set)"

    for model in OPENROUTER_MODELS:
        try:
            payload = json.dumps({
                "model": model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 1024,
                "temperature": 0.4,
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/chat/completions",
                data=payload,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "Sentinel",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = json.loads(resp.read().decode())
            text = body["choices"][0]["message"]["content"]
            if text:
                return text.strip()
        except Exception as exc:
            print(f"[OpenRouter] Model {model} failed: {exc}")
            continue  # try next model

    return "(All free models unavailable — raw data returned below)"


# ── The pipeline itself ─────────────────────────────────────────────────

def _run_pipeline(user_message: str) -> dict:
    """Run the full Sentinel 7-step pipeline with pure Python calls."""

    steps_log = []       # human-readable trace
    avoid_sectors = []   # default
    budget = 10000.0     # default

    # ── Parse intent ─────────────────────────────────────────────────
    intent = _check_intent(user_message)
    if intent["blocked"]:
        return {
            "response": (
                f"🚫 TRADE BLOCKED\n"
                f"────────────────────────────────\n"
                f"Reason: Request contains a reference to an excluded sector: "
                f"{intent['matched_sector']}\n"
                f"Policy violated: Excluded sector policy "
                f"(coal, weapons, tobacco, fossil fuels)\n"
                f"Action: Trade has been logged and rejected. "
                f"No execution will occur."
            ),
            "status": "BLOCKED",
        }

    # ── Step 1: Climate ──────────────────────────────────────────────
    try:
        climate = fetch_climate_metrics(avoid_sectors, esg_threshold=60.0)
        steps_log.append(f"✅ Climate: green_score={climate.get('green_score')}, "
                         f"eligible={len(climate.get('eligible_assets', []))} assets")
    except Exception as e:
        climate = {"green_score": 0, "eligible_assets": [], "avoided_sectors_applied": []}
        steps_log.append(f"⚠️ Climate step failed: {e}")

    # ── Step 2: Financial ────────────────────────────────────────────
    tickers = [a["ticker"] for a in climate.get("eligible_assets", []) if a.get("ticker")]
    if not tickers:
        tickers = ["AAPL", "MSFT", "TSLA"]
    try:
        financial = calculate_market_trends("moderate", tickers)
        steps_log.append(f"✅ Financial: sentiment={financial.get('market_sentiment')}, "
                         f"expected_return={financial.get('expected_return')}")
    except Exception as e:
        financial = {"market_sentiment": "neutral", "expected_return": 0.07, "volatility": 0.12}
        steps_log.append(f"⚠️ Financial step failed: {e}")

    # ── Step 3: Simulation ───────────────────────────────────────────
    try:
        sim = run_monte_carlo_sim(budget,
                                  financial.get("expected_return", 0.07),
                                  financial.get("volatility", 0.12))
        steps_log.append(f"✅ Simulation: expected_1y={sim.get('expected_1y_value')}, "
                         f"VaR95={sim.get('value_at_risk_95')}")
    except Exception as e:
        sim = {"expected_1y_value": budget, "value_at_risk_95": 0, "drawdown_probability": 0.15}
        steps_log.append(f"⚠️ Simulation step failed: {e}")

    # ── Step 4: Portfolio ────────────────────────────────────────────
    try:
        stock_prices = get_multiple_prices(tickers)
        portfolio = calculate_allocation(budget, climate.get("eligible_assets", []), stock_prices)
        steps_log.append(f"✅ Portfolio: invested={portfolio.get('invested_amount')}, "
                         f"holdings={len(portfolio.get('holdings', []))}")
    except Exception as e:
        portfolio = {"invested_amount": 0, "cash_balance": budget, "holdings": []}
        steps_log.append(f"⚠️ Portfolio step failed: {e}")

    # ── Step 5: Trader (propose) ─────────────────────────────────────
    allowed = [a["ticker"] for a in climate.get("eligible_assets", []) if a.get("ticker")]
    if not allowed:
        allowed = ["AAPL"]
    target_ticker = random.choice(allowed)
    price = get_stock_price(target_ticker)
    quantity = max(1, int((1000 * 0.5) / price))
    proposed_trade = {
        "ticker": target_ticker,
        "action": "buy",
        "quantity": quantity,
        "sector": next(
            (a["sector"] for a in climate.get("eligible_assets", [])
             if a.get("ticker") == target_ticker), "Technology"),
        "risk_score": 30,
        "price": round(price, 2),
    }
    estimated_cost = round(quantity * price, 2)
    steps_log.append(f"✅ Trader: proposed BUY {quantity}x {target_ticker} @ ${price:.2f}")

    # ── Step 6: Guard ────────────────────────────────────────────────
    guard_result = enforce_constraints(proposed_trade, avoid_sectors, {})
    steps_log.append(f"✅ Guard: status={guard_result.get('status')}")

    # ── Step 7: Explain (LLM) ───────────────────────────────────────
    pipeline_state = {
        "user_message": user_message,
        "climate_data": climate,
        "financial_data": financial,
        "simulation": sim,
        "portfolio": portfolio,
        "proposed_trade": proposed_trade,
        "guard": guard_result,
        "steps_log": steps_log,
    }

    system_prompt = """You are Sentinel, an AI-powered climate-aware autonomous investing assistant.

You MUST generate a beautifully formatted investment analysis report using rich Markdown.

MANDATORY FORMAT — follow this structure exactly:

## 📊 Sentinel Investment Report

### 🌿 1. Climate & ESG Screening
- Use a markdown **table** showing each eligible asset's ticker, sector, climate score, and risk level.
- State the average green score and which sectors were avoided.

### 📈 2. Market Analysis
- Use a markdown **table** for per-ticker signals (ticker, daily return %, volatility %, sentiment).
- State the overall market sentiment (bullish/bearish/neutral) and expected return.

### 🎲 3. Risk Simulation
- Use a markdown **table** for: Expected 1-Year Value, Estimated Return %, VaR (95%), Drawdown Probability, Sharpe Ratio, Sortino Ratio, Beta.

### 💼 4. Portfolio Allocation
- Use a markdown **table** for: Ticker, Shares, Price, Allocated Value, Weight %.
- State invested amount, cash balance.

### 🛡️ 5. Trade Decision
- State the proposed trade (action, ticker, quantity, price).
- State the guard status (APPROVED/BLOCKED/MODIFIED) and why.

### 📋 6. Summary & Recommendation
- 3-5 bullet points summarizing the key takeaways.
- A **bold final recommendation** sentence.

RULES:
- ALWAYS use markdown tables (with | headers |), bold, headings, and bullet points.
- NEVER return a plain text paragraph. Always use the structured format above.
- Keep each section concise but data-rich.
- Use emojis in headings only."""

    user_prompt = (
        f"The user asked: \"{user_message}\"\n\n"
        f"Here is the full pipeline data (use ALL of this data in your report):\n\n"
        f"```json\n{json.dumps(pipeline_state, indent=2, default=str)}\n```"
    )

    llm_explanation = _call_llm(system_prompt, user_prompt)

    status = guard_result.get("status", "UNKNOWN")
    final_response = llm_explanation

    return {"response": final_response, "status": status}


# ── Route registration (same pattern as before) ─────────────────────────

def register_quota_route(app: FastAPI):
    for route in app.routes:
        if getattr(route, "path", None) == "/quota-status":
            return
    @app.get("/quota-status")
    def quota_status():
        return get_quota_summary()


def register_chat_route(app: FastAPI):
    for route in app.routes:
        if getattr(route, "path", None) == "/chat":
            return

    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)

    if not any(getattr(route, "name", "") == "static" for route in app.routes):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(os.path.join(static_dir, "index.html"))

    @app.post("/chat")
    async def chat_handler(request: Request):
        data = await request.json()
        user_message = data.get("message", "")

        try:
            result = await asyncio.to_thread(_run_pipeline, user_message)
        except Exception as exc:
            traceback.print_exc()
            result = {
                "response": f"Pipeline error: {exc}",
                "status": "ERROR",
            }

        return JSONResponse(result)


# ── Monkeypatch FastAPI to auto-register routes ──────────────────────────
original_init = FastAPI.__init__

def patched_init(self, *args, **kwargs):
    original_init(self, *args, **kwargs)
    register_quota_route(self)
    register_chat_route(self)

FastAPI.__init__ = patched_init

for obj in gc.get_objects():
    if isinstance(obj, FastAPI):
        try:
            register_quota_route(obj)
            register_chat_route(obj)
        except Exception:
            pass
