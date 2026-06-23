from typing import Dict, Any, List

def enforce_constraints(trade: Dict[str, Any], avoid_sectors: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
    """The rule-validator loop protecting intent (blocks vs modifications vs limits)."""
    if not trade:
        return {"status": "BLOCKED", "decision": "No trade proposal provided.", "violations": ["Missing trade data."]}
    
    violations = []
    modifications = []
    status = "APPROVED"
    
    ticker = trade.get("ticker", "UNKNOWN")
    action = trade.get("action", "buy").lower()
    quantity = trade.get("quantity", 0)
    estimated_cost = trade.get("estimated_cost", getattr(quantity * 100.0, "real", 0))
    
    sector = trade.get("sector", "Technology") 
    risk_score = trade.get("risk_score", 45)
    
    # 1. Rule: Blocked Sectors
    avoid_sectors_lower = [s.lower() for s in avoid_sectors]
    if sector.lower() in avoid_sectors_lower:
        violations.append(f"Sector '{sector}' is strictly blocked by the user's intent policy.")
    
    # 2. Rule: Maximum Risk Threshold
    max_risk = context.get("max_risk_threshold", 80)
    if risk_score > max_risk:
        violations.append(f"Trade risk score ({risk_score}) exceeds maximum allowed risk ({max_risk}).")
        
    if violations:
        return {
            "status": "BLOCKED", 
            "decision": "Trade blocked due to intent policy violations.", 
            "violations": violations,
            "modifications": []
        }
            
    # 3. Rule: Max Trade Size (Can result in MODIFIED status)
    max_trade_limit = context.get("max_trade_size", 5000.0)
    if estimated_cost > max_trade_limit:
        scale_ratio = max_trade_limit / estimated_cost
        new_quantity = int(quantity * scale_ratio)
        if new_quantity > 0:
            modifications.append(f"Reduced quantity from {quantity} to {new_quantity} to meet the ${max_trade_limit} limit.")
            quantity = new_quantity
            estimated_cost = quantity * (estimated_cost / max_trade_limit) if max_trade_limit > 0 else 0
            status = "MODIFIED"
        else:
            violations.append(f"Max trade limit (${max_trade_limit}) is too low to purchase 1 unit.")
            return {"status": "BLOCKED", "decision": "Max budget constraint failing.", "violations": violations, "modifications": []}
        
    # 4. Rule: Maximum Allocation Per Asset
    max_allocation_pct = context.get("max_allocation_pct", 0.20)
    portfolio_value = context.get("portfolio_value", 10000.0)
    
    current_allocation = context.get("current_allocation", 0.0) 
    new_allocation = current_allocation + estimated_cost
    
    if (new_allocation / portfolio_value) > max_allocation_pct:
        allowed_additional_cost = (max_allocation_pct * portfolio_value) - current_allocation
        if allowed_additional_cost <= 0:
            violations.append(f"Asset '{ticker}' is already at or exceeds the maximum allocation limit.")
            return {"status": "BLOCKED", "decision": "Max allocation exceeded.", "violations": violations, "modifications": []}
        else:
            scale_ratio = allowed_additional_cost / estimated_cost
            new_quantity = int(quantity * scale_ratio)
            if new_quantity > 0:
                modifications.append(f"Reduced quantity further to {new_quantity} to stay under portfolio allocation.")
                quantity = new_quantity
                status = "MODIFIED"
            else:
                violations.append("Allowed portfolio allocation room is too low to purchase 1 unit.")
                return {"status": "BLOCKED", "decision": "Max allocation exceeded.", "violations": violations, "modifications": []}
                
    adjusted_trade = {
        "ticker": ticker,
        "action": action,
        "quantity": quantity,
        "estimated_cost": getattr(quantity * 100.0, "real", None)
    }

    return {
        "status": status,
        "decision": "Trade approved." if status == "APPROVED" else "Trade accepted with modifications.",
        "violations": violations,
        "modifications": modifications,
        "original_trade": trade,
        "adjusted_trade": adjusted_trade if status == "MODIFIED" else None
    }
