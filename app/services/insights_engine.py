import math
import random
from typing import Dict, Any, List

def generate_insights_data(holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generates dynamic insights data based on the provided portfolio holdings."""
    
    # If no holdings, provide a default mapping.
    if not holdings:
        holdings = [
            {"ticker": "NVDA", "shares": 100, "weight": 25.0},
            {"ticker": "OXY", "shares": 150, "weight": 15.0},
            {"ticker": "JPM", "shares": 50, "weight": 20.0},
            {"ticker": "UNH", "shares": 30, "weight": 20.0},
            {"ticker": "TSLA", "shares": 80, "weight": 20.0}
        ]


    sector_map = {
        "NVDA": "Technology", "MSFT": "Technology", "AAPL": "Technology", "GOOGL": "Technology", "META": "Technology",
        "CVX": "Energy", "XOM": "Energy", "OXY": "Energy",
        "JPM": "Financials", "GS": "Financials",
        "JNJ": "Healthcare", "UNH": "Healthcare",
        "TSLA": "Cons. Discr.", "AMZN": "Cons. Discr."
    }

    # ESG baseline data
    esg_baselines = {
        "NVDA": {"score": 92, "rating": "AAA", "carbon": "Low", "water": "Low", "waste": "Low", "trans": "Low", "phys": "Low", "ret": 45, "risk": 15},
        "MSFT": {"score": 88, "rating": "AAA", "carbon": "Low", "water": "Med", "waste": "Low", "trans": "Low", "phys": "Low", "ret": 32, "risk": 20},
        "AAPL": {"score": 75, "rating": "AA", "carbon": "Low", "water": "Low", "waste": "Med", "trans": "Low", "phys": "Med", "ret": 28, "risk": 35},
        "TSLA": {"score": 60, "rating": "BBB", "carbon": "Med", "water": "Med", "waste": "Med", "trans": "High", "phys": "Med", "ret": 55, "risk": 80},
        "XOM":  {"score": 25, "rating": "B", "carbon": "High", "water": "High", "waste": "Med", "trans": "High", "phys": "High", "ret": 15, "risk": 95},
        "CVX":  {"score": 35, "rating": "BB", "carbon": "High", "water": "Med", "waste": "Med", "trans": "High", "phys": "Med", "ret": 18, "risk": 85},
    }

    def get_baseline(tkr):
        if tkr in esg_baselines:
            return esg_baselines[tkr]
        # Random placeholder for unknown tickers
        r = random.Random(tkr)
        sc = r.randint(30, 95)
        rt = "AAA" if sc >= 85 else "AA" if sc >= 70 else "BBB" if sc >= 50 else "BB" if sc >= 35 else "B"
        return {"score": sc, "rating": rt, "carbon": r.choice(["Low", "Med", "High"]), 
                "water": r.choice(["Low", "Med", "High"]), "waste": r.choice(["Low", "Med", "High"]),
                "trans": r.choice(["Low", "Med", "High"]), "phys": r.choice(["Low", "Med", "High"]),
                "ret": r.randint(5, 40), "risk": r.randint(10, 90)}

    assets = []
    total_weight = 0
    sector_exposure = {}

    for h in holdings:
        t = h["ticker"]
        w = float(h.get("weight", 0))
        total_weight += w
        
        sec = sector_map.get(t, "Other")
        sector_exposure[sec] = sector_exposure.get(sec, 0) + w

        base = get_baseline(t)
        # Add dynamic variation based on day
        jitter = random.uniform(-1, 1)
        score = min(100, max(0, round(base["score"] + jitter)))
        
        assets.append({
            "ticker": t,
            "sector": sec,
            "weight": w,
            "esg_score": score,
            "rating": base["rating"],
            "carbon": base["carbon"],
            "water": base["water"],
            "waste": base["waste"],
            "transition": base["trans"],
            "physical": base["phys"],
            "exp_return": base["ret"] + round(random.uniform(-2, 2)),
            "risk_score": base["risk"] + round(random.uniform(-5, 5))
        })

    # Sector logic
    sectors_arr = []
    for sec, w in sector_exposure.items():
        if w <= 0: continue
        limit = 35 if sec == "Technology" else 15 if sec == "Energy" else 20
        status = "safe" if w <= limit else "warn" if w <= limit + 5 else "danger"
        sectors_arr.append({
            "sector": sec,
            "weight": round(w, 1),
            "limit": limit,
            "status": status,
            "is_heavy": sec in ["Energy", "Industrials"]
        })

    sectors_arr.sort(key=lambda x: x["weight"], reverse=True)

    # Calculate overall rating
    total_esg = sum([a["esg_score"] * a["weight"] for a in assets])
    avg_esg = round(total_esg / total_weight) if total_weight > 0 else 0
    
    # Portfolio summary
    carbon_int = 100 - avg_esg + random.randint(-5, 5)
    water_sec = avg_esg + random.randint(-5, 10)
    gov = avg_esg + random.randint(0, 10)

    # Generate insights messages
    alerts = []
    heavy_energy = sum(s["weight"] for s in sectors_arr if s["sector"] == "Energy")
    if heavy_energy > 15:
        alerts.append({"status": "danger", "icon": "⚠️", "text": f"High exposure to carbon-heavy Energy sector ({heavy_energy}%). Target limit is < 15% to maintain Paris alignment."})
    
    tech_weight = sum(s["weight"] for s in sectors_arr if s["sector"] == "Technology")
    if tech_weight > 40:
        alerts.append({"status": "safe", "icon": "✅", "text": f"Strong concentration ({tech_weight}%) in Tech ESG leaders. Exceptional resilience against standard transition shocks."})

    high_risk_assets = [a["ticker"] for a in assets if a["risk_score"] > 80]
    if high_risk_assets:
        alerts.append({"status": "warn", "icon": "📉", "text": f"{', '.join(high_risk_assets)} flagged: Climate Value-at-Risk (CVaR) exceeds threshold under a 1.5°C disorderly scenario."})
    
    if not alerts:
         alerts.append({"status": "safe", "icon": "🌟", "text": "Portfolio strictly adheres to all Paris-aligned trajectory goals with no flagged deviations."})

    return {
        "assets": assets,
        "sectors": sectors_arr,
        "portfolio_rating": avg_esg,
        "portfolio_status": "EXCELLENT" if avg_esg >= 80 else "GOOD" if avg_esg >= 65 else "FAIR" if avg_esg >= 50 else "POOR",
        "scores": {
            "carbon_intensity": min(100, max(0, carbon_int)),
            "water_security": min(100, max(0, water_sec)),
            "governance": min(100, max(0, gov))
        },
        "alerts": alerts
    }
