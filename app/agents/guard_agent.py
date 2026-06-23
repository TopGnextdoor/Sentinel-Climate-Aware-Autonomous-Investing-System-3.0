from app.agents.base_agent import BaseAgent
from app.config import get_api_key
from typing import Dict, Any, List
from app.services.policy_service import enforce_constraints
from google.adk.tools import McpToolset
from mcp.client.stdio import StdioServerParameters

EXCLUDED_SECTORS = {"coal", "weapons", "firearms", "tobacco", "fossil fuels", "oil sands", "tar sands"}

def check_intent_for_policy_violation(user_request: str) -> Dict[str, Any]:
    """Proactively scan the raw user request for mentions of excluded sectors.
    
    Returns a dict with 'blocked' (bool), 'matched_sector' (str|None), and 'reason' (str).
    """
    lower_request = user_request.lower()
    for sector in EXCLUDED_SECTORS:
        if sector in lower_request:
            return {
                "blocked": True,
                "matched_sector": sector,
                "reason": f"Request explicitly mentions '{sector}', which is on the excluded sector list."
            }
    return {"blocked": False, "matched_sector": None, "reason": "No excluded sectors detected in request."}

def validate_intent(trade: Dict[str, Any], avoid_sectors: List[str], context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Validate the proposed trade against ESG sector constraints and policy rules.
    
    Returns a dict with status (APPROVED / BLOCKED / MODIFIED), decision string,
    violations list, and modifications list.
    """
    context = context or {}
    sector = trade.get("sector", "").lower()
    avoid_sectors_lower = [s.lower() for s in avoid_sectors]
    if sector in avoid_sectors_lower:
        return {
            "status": "BLOCKED",
            "decision": "Trade Blocked by Guard Component",
            "violations": [f"Trade violates ESG constraint: '{sector}' sector is on the exclusion list."],
            "modifications": []
        }
    return enforce_constraints(trade, avoid_sectors, context)

policy_mcp_toolset = McpToolset(
    connection_params=StdioServerParameters(
        command="uv",
        args=["run", "python", "mcp_servers/policy/server.py"]
    )
)

GUARD_INSTRUCTION = """You are a safety guard policy enforcer for an autonomous investing system.

Your job is to inspect every incoming investment request BEFORE any trade is executed.

MANDATORY STEPS — follow these in order for every request:
0. FIRST, call `check_intent_for_policy_violation(user_request)` with the original user message.
   - If it returns blocked=True, IMMEDIATELY output the following and STOP — do not call any other tools:

```
🚫 TRADE BLOCKED
────────────────────────────────
Reason: Request contains a reference to an excluded sector: <matched_sector>
Policy violated: Excluded sector policy (coal, weapons, tobacco, fossil fuels)
Action: Trade has been logged and rejected. No execution will occur.
```

   Then call `log_decision({"status": "BLOCKED", "reason": ..., "matched_sector": ...})`.

1. If intent check passes, determine if a trade was actually proposed by the user or previous agents. If the user only asked for an analysis and no trade parameters (like amount) exist, DO NOT call `validate_trade`. Simply output 'No trade requested, bypassing guard.' and pass the analysis along. STOP HERE.

2. If a trade WAS proposed, call `get_active_policies()` to retrieve the current trading constraints.
3. Extract the ticker, amount, and ESG score from the pipeline context or user request.
4. Call `validate_trade(ticker, amount, esg_score)` with those values.
5. If `validate_trade` returns approved=False:
   - Call `log_decision({"status": "BLOCKED", "ticker": ..., "reason": ...})` to audit the block.
   - Output the BLOCKED message format above.
6. If `validate_trade` returns approved=True:
   - Call `log_decision({"status": "APPROVED", "ticker": ..., "reason": "All policies passed"})`.
   - Output: ✅ TRADE APPROVED — All policies passed.

NEVER allow a trade to proceed if either check returns a violation. This rule is absolute."""

guard_agent = BaseAgent(
    name="guard_agent",
    model="gemini-2.5-flash",
    instruction=GUARD_INSTRUCTION,
    tools=[check_intent_for_policy_violation, validate_intent, policy_mcp_toolset],
)
