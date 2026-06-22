from app.agents.base_agent import BaseAgent
from app.services.climate_data import fetch_climate_metrics
from app.config import get_api_key
from typing import Dict, Any, List
from google.adk.tools import McpToolset
from mcp.client.stdio import StdioServerParameters

def analyze_climate_impact(avoid_sectors: List[str], esg_threshold: float = 60.0) -> Dict[str, Any]:
    """Thin wrapper for climate impact analysis using JSON data, filtering by ESG threshold."""
    return fetch_climate_metrics(avoid_sectors, esg_threshold)

mcp_toolset = McpToolset(
    connection_params=StdioServerParameters(
        command="uv",
        args=["run", "python", "mcp_servers/esg/server.py"]
    )
)

climate_agent = BaseAgent(
    name="climate_agent",
    model="gemini-2.5-flash-lite",
    instruction="You are a climate expert. Assess ESG and environmental risk scoring based on sectors to avoid and the ESG threshold. Use the provided MCP tools to fetch live ESG scores, carbon footprints, and green sectors.\n\nCRITICAL PIPELINE RULE: You are part of an automated sequential pipeline. DO NOT ask the user clarifying questions. If any information is missing, use reasonable defaults or simply pass along the analysis without complaining. Never output conversational apologies.",
    tools=[analyze_climate_impact, mcp_toolset],
)
