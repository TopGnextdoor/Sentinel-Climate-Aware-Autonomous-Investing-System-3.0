from app.agents.base_agent import BaseAgent
from app.config import get_api_key
from typing import Dict, Any, List, Optional
from app.services.risk import calculate_market_trends
from google.adk.tools import McpToolset
from mcp.client.stdio import StdioServerParameters

def analyze_market_trends(risk_level: str = "moderate", tickers: Optional[List[str]] = None) -> Dict[str, Any]:
    """Thin wrapper for assessing financial markets and trends using real market signals."""
    return calculate_market_trends(risk_level, tickers=tickers)

market_mcp_toolset = McpToolset(
    connection_params=StdioServerParameters(
        command="uv",
        args=["run", "python", "mcp_servers/market/server.py"]
    )
)

financial_agent = BaseAgent(
    name="financial_agent",
    model="gemini-2.5-flash-lite",
    instruction="You are a financial analyst. Assess market trends for the eligible tickers given a risk level. Use the provided MCP tools to fetch live stock prices, market trends, and search for stocks.\n\nCRITICAL PIPELINE RULE: You are part of an automated sequential pipeline. DO NOT ask the user clarifying questions. If any information like risk level is missing, default to 'moderate' and proceed. Never output conversational apologies.",
    tools=[analyze_market_trends, market_mcp_toolset],
)
