from typing import Dict, Any, List
import math

def calculate_allocation(budget: float, eligible_assets: List[Dict[str, Any]], stock_prices: Dict[str, float]) -> Dict[str, Any]:
    """Math calculations mapping budget to fractional share allocation weighted by ESG."""
    if not eligible_assets:
        return {"error": "No eligible assets after climate & sector filtering.", "holdings": []}
        
    total_climate = sum(asset["climate_score"] for asset in eligible_assets)
    
    holdings = []
    total_allocated = 0.0
    
    for asset in eligible_assets:
        ticker = asset["ticker"]
        weight = asset["climate_score"] / total_climate if total_climate > 0 else 1.0 / len(eligible_assets)
        allocated_amount = budget * weight
        
        price = stock_prices.get(ticker, 100.0)
        shares = math.floor(allocated_amount / price)
        
        if shares > 0:
            holdings.append({
                "ticker": ticker,
                "price": round(price, 2),
                "shares": shares,
                "weight": round(weight, 4),
                "allocated_value": round(shares * price, 2)
            })
            total_allocated += (shares * price)
        
    return {
        "total_budget": budget,
        "invested_amount": round(total_allocated, 2),
        "cash_balance": round(budget - total_allocated, 2),
        "holdings": holdings
    }
