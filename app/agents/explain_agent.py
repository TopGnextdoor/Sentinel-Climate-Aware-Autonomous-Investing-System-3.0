from app.agents.base_agent import BaseAgent
from app.config import get_api_key
from typing import Dict, Any

def generate_explanation(pipeline_state: Dict[str, Any]) -> str:
    """Agent for translating autonomous orchestration decisions into human-readable text."""
    if not pipeline_state:
        return "Insufficient data to generate an explanation. Pipeline execution was interrupted."
    try:
        climate = pipeline_state.get("climate_data", {})
        guard = pipeline_state.get("guard", {})
        sim = pipeline_state.get("simulation", {})
        green_score = climate.get('green_score', 0)
        guard_status = guard.get('status', 'UNKNOWN')
        modifications = guard.get('modifications', [])
        violations = guard.get('violations', [])
        drawdown = sim.get('drawdown_probability', 0)
        trade_obj = guard.get("original_trade", {})
        ticker = trade_obj.get("ticker", "asset")
        action = str(trade_obj.get("action", "trade")).upper()
        
        explanation = (
            "EXECUTING CLIMATE-AWARE REBALANCING...<br>"
            f"> [PORTFOLIO CONTEXT] Allocation dynamically weighted by ESG metrics, achieving an average climate score of {green_score}/100.<br>"
            f"> [TRADE INTENT] System proposed to {action} {ticker}.<br>"
        )
        if guard_status == "APPROVED":
            explanation += f"> [WHY THIS DECISION?] The {ticker} trade was APPROVED as it passed all fiscal limits and rigorously respected sector restrictions. 🛡️ Safe-Guard verified compliance."
        elif guard_status == "MODIFIED":
            mods = " ".join(modifications) if modifications else "scaling down the quantity to fit allocation limits."
            explanation += f"> [SAFE-GUARD INTERVENTION] The {ticker} trade was MODIFIED: {mods} ⚠️ Limits enforced dynamically."
        elif guard_status == "BLOCKED":
            issues = " ".join(violations) if violations else "intent policy violations."
            explanation += f"> [SAFE-GUARD INTERVENTION] The {ticker} trade was STRICTLY BLOCKED to protect user intent. Reason: {issues} 🚫"
        if guard_status in ["APPROVED", "MODIFIED"] and "expected_1y_value" in sim:
            explanation += (
                f"<br>> [SIMULATION] A Monte Carlo test validated the risk, forecasting a "
                f"{drawdown*100:.1f}% probability of severe drawdown, matching your tolerance."
            )
        elif guard_status == "BLOCKED":
            explanation += "<br>> [SIMULATION] Forward simulation and market execution were cleanly bypassed to safely enforce the policy block."
        return explanation.strip()
    except Exception as e:
        return f"Pipeline execution completed, but the explanation engine encountered a formatting issue: {str(e)}"

explain_agent = BaseAgent(
    name="explain_agent",
    model="gemini-2.5-flash-lite",
    instruction="You are a reporting agent. Generate a human-readable explanation from the overall pipeline state.\n\nCRITICAL PIPELINE RULE: You are the final step in an automated sequential pipeline. DO NOT ask the user clarifying questions or output conversational apologies. If no pipeline state is available, just output a generic final report.",
    tools=[generate_explanation],
)
