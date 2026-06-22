from app.agents.base_agent import BaseAgent
from app.config import get_api_key
from typing import Dict, Any
from app.services.optimizer import calculate_allocation
from app.services.market_data import get_multiple_prices

def optimize_portfolio(budget: float = 10000.0, climate_data: Dict[str, Any] = None, financial_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Thin wrapper for optimizing portfolio mixes."""
    budget = budget or 10000.0
    eligible_assets = climate_data.get("eligible_assets", [])
    tickers = [asset.get("ticker") for asset in eligible_assets if asset.get("ticker")]
    if not tickers:
        tickers = ["AAPL", "MSFT", "TSLA"]
    stock_prices = get_multiple_prices(tickers)
    return calculate_allocation(budget, eligible_assets, stock_prices)

portfolio_agent = BaseAgent(
    name="portfolio_agent",
    model="gemini-2.5-flash-lite",
    instruction="You are a portfolio allocation expert. Generate a portfolio allocation using climate data and financial data.\n\nCRITICAL PIPELINE RULE: You are part of an automated sequential pipeline. DO NOT ask the user clarifying questions. If a budget is missing, default to $10,000. Never output conversational apologies.",
    tools=[optimize_portfolio],
)
