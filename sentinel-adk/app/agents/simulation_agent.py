from app.agents.base_agent import BaseAgent
from app.config import get_api_key
from typing import Dict, Any
from app.services.simulation_engine import run_monte_carlo_sim

def simulate_scenario(budget: float = 10000.0, portfolio: Dict[str, Any] = None) -> Dict[str, Any]:
    """Thin wrapper for running potential trade simulations."""
    budget = budget or 10000.0
    portfolio_volatility = 0.12 
    portfolio_return = 0.07 
    return run_monte_carlo_sim(budget, portfolio_return, portfolio_volatility)

simulation_agent = BaseAgent(
    name="simulation_agent",
    model="litellm:openrouter/meta-llama/llama-3-8b-instruct:free",
    instruction="You are a risk simulation engine. Run a Monte Carlo simulation based on budget and portfolio logic.\n\nCRITICAL PIPELINE RULE: You are part of an automated sequential pipeline. DO NOT ask the user clarifying questions. If any info like budget is missing, default to $10,000. Never output conversational apologies.",
    tools=[simulate_scenario],
)
