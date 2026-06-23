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
        "GOOGL": {"sector": "technology", "risk_score": 28},
        "AMZN": {"sector": "e-commerce", "risk_score": 40},
        "NVDA": {"sector": "semiconductors", "risk_score": 55},
        "META": {"sector": "technology", "risk_score": 45},
        "NEE": {"sector": "renewables", "risk_score": 20},
        "ENPH": {"sector": "renewables", "risk_score": 50},
        "FSLR": {"sector": "renewables", "risk_score": 48},
        "JNJ": {"sector": "healthcare", "risk_score": 15},
        "UNH": {"sector": "healthcare", "risk_score": 22},
        "V": {"sector": "financial services", "risk_score": 20},
        "JPM": {"sector": "financial services", "risk_score": 35},
        "PEP": {"sector": "consumer staples", "risk_score": 12},
        "KO": {"sector": "consumer staples", "risk_score": 10},
        "DIS": {"sector": "entertainment", "risk_score": 42},
        "COST": {"sector": "consumer staples", "risk_score": 18},
        "AMD": {"sector": "semiconductors", "risk_score": 58},
        "CRM": {"sector": "technology", "risk_score": 32},
        "ADBE": {"sector": "technology", "risk_score": 30},
        "NFLX": {"sector": "entertainment", "risk_score": 45},
        "XOM": {"sector": "fossils", "risk_score": 85},
        "CVX": {"sector": "fossils", "risk_score": 80},
        "BA": {"sector": "aerospace", "risk_score": 65},
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
    model="litellm:openrouter/meta-llama/llama-3-8b-instruct:free",
    instruction="You are a trade execution engine. You generate trade proposals and execute them via Alpaca. Use the provided MCP tools to fetch live stock prices to validate costs before trading.\n\nCRITICAL PIPELINE RULE: You are part of an automated sequential pipeline. DO NOT ask the user clarifying questions. If the user only asks for an analysis and does not explicitly request a trade execution, DO NOT propose or execute a trade. Just pass the analysis along.",
    tools=[generate_trade_proposals, execute_trade, market_mcp_toolset],
)
