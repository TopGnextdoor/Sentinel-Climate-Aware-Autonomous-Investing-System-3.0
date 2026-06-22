from app.agents.base_agent import BaseAgent
from app.config import get_api_key
from typing import Dict, Any
from app.services.trading_service import execute_alpaca_trade
from app.services.market_data import get_stock_price
from google.adk.tools import McpToolset
from mcp.client.stdio import StdioServerParameters
import random

def generate_trade_proposals(allowed_assets: list = None, max_trade: float = 1000.0) -> Dict[str, Any]:
    """Agent for generating actual paper trades (Pre-Guard Intent Generation)."""
    ticker_meta = {
        "AAPL": {"sector": "technology", "risk_score": 30},
        "MSFT": {"sector": "technology", "risk_score": 25},
        "TSLA": {"sector": "auto", "risk_score": 60},
        "XOM": {"sector": "fossils", "risk_score": 85},
        "NEE": {"sector": "renewables", "risk_score": 20}
    }
    if not allowed_assets:
        allowed_assets = ["AAPL"]
    target_ticker = random.choice(allowed_assets)
    meta = ticker_meta.get(target_ticker, {"sector": "unknown", "risk_score": 50})
    price = get_stock_price(target_ticker)
    affordable_qty = max(1, int((max_trade * 0.5) / price)) 
    quantity = min(affordable_qty, 200)
    estimated_cost = quantity * price
    return {
        "proposed_trade": {
            "ticker": target_ticker, 
            "action": "buy", 
            "quantity": quantity,
            "sector": meta["sector"],
            "risk_score": meta["risk_score"],
            "price": round(price, 2)
        }, 
        "estimated_cost": round(estimated_cost, 2)
    }

def execute_trade(trade: Dict[str, Any]) -> Dict[str, Any]:
    """Thin wrapper delegating to Alpaca service."""
    return execute_alpaca_trade(trade)

market_mcp_toolset = McpToolset(
    connection_params=StdioServerParameters(
        command="uv",
        args=["run", "python", "mcp_servers/market/server.py"]
    )
)

trader_agent = BaseAgent(
    name="trader_agent",
    model="gemini-2.5-flash-lite",
    instruction="You are a trade execution engine. You generate trade proposals and execute them via Alpaca. Use the provided MCP tools to fetch live stock prices to validate costs before trading.\n\nCRITICAL PIPELINE RULE: You are part of an automated sequential pipeline. DO NOT ask the user clarifying questions. If the user only asks for an analysis and does not explicitly request a trade execution, DO NOT propose or execute a trade. Just pass the analysis along.",
    tools=[generate_trade_proposals, execute_trade, market_mcp_toolset],
)
