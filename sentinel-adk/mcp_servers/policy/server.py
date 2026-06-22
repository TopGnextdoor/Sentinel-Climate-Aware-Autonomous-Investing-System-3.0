import os
import json
from datetime import datetime, UTC
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("sentinel-policy-mcp")

# For simplicity, assuming a static mock portfolio value to evaluate the 20% rule
MOCK_PORTFOLIO_VALUE = 100000.0

# Mock excluded sectors represented by tickers
EXCLUDED_TICKERS = ["XOM", "CVX", "LMT", "RTX"]

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
AUDIT_LOG_FILE = os.path.join(DATA_DIR, "audit_log.json")

os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(AUDIT_LOG_FILE):
    with open(AUDIT_LOG_FILE, "w") as f:
        json.dump([], f)

@mcp.tool()
def get_active_policies() -> list[str]:
    """Retrieve the current active trading constraints."""
    return [
        "Block any stock with esg_score below 40",
        "Block any single trade amount above 20% of the total portfolio value",
        "Block stocks in excluded sectors (coal, weapons)"
    ]

@mcp.tool()
def validate_trade(ticker: str, amount: float, esg_score: float) -> dict:
    """Validate a trade against the active ESG and financial policies.
    Returns a dict with 'approved' (bool) and 'reason' (str)."""
    
    ticker_upper = ticker.upper()
    
    if esg_score < 40:
        return {"approved": False, "reason": f"ESG score {esg_score} is below the minimum threshold of 40."}
        
    if amount > (MOCK_PORTFOLIO_VALUE * 0.20):
        return {"approved": False, "reason": f"Trade amount ${amount} exceeds 20% of the portfolio."}
        
    if ticker_upper in EXCLUDED_TICKERS:
        return {"approved": False, "reason": f"Ticker {ticker_upper} belongs to an excluded sector (coal/weapons)."}
        
    return {"approved": True, "reason": "Trade complies with all active policies."}

@mcp.tool()
def log_decision(decision_payload: dict) -> dict:
    """Stores an audit trail entry for a trading decision."""
    try:
        with open(AUDIT_LOG_FILE, "r") as f:
            logs = json.load(f)
    except Exception:
        logs = []
        
    entry = {
        "timestamp": datetime.now(UTC).isoformat(),
        "payload": decision_payload
    }
    logs.append(entry)
    
    with open(AUDIT_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)
        
    return {"status": "success", "message": "Decision successfully audited."}

if __name__ == "__main__":
    mcp.run(transport="stdio")
