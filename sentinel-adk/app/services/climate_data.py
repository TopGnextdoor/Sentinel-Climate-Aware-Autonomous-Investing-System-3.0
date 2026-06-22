import json
import os
from typing import Dict, Any, List
import yfinance as yf

def get_esg_score(ticker: str, fallback: float = 50.0) -> float:
    """Fetch real ESG score from Yahoo Finance, with a fallback if missing."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        if "esgScores" in info and isinstance(info["esgScores"], dict):
            score = info["esgScores"].get("totalEsg", None)
            if score is not None:
                return float(score)
    except Exception:
        pass
        
    static_mapping = {
        "AAPL": 72.0,
        "MSFT": 68.0,
        "TSLA": 55.0
    }
    return float(static_mapping.get(ticker, fallback))



def fetch_climate_metrics(avoid_sectors: List[str], esg_threshold: float = 60.0) -> Dict[str, Any]:
    """Load climate_data.json and compute raw risk ratings and sector metrics, filtering by ESG threshold."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    climate_path = os.path.join(base_dir, "data", "climate_data.json")
    
    climate_data = []
    if os.path.exists(climate_path):
        with open(climate_path, "r") as f:
            climate_data = json.load(f)
        
    sector_map = {
        "AAPL": "Technology",
        "MSFT": "Technology",
        "TSLA": "Automotive",
        "XOM": "Fossil Fuels"
    }
    
    avoid_sectors_lower = [s.lower() for s in (avoid_sectors or [])]
    allowed_assets = []
    total_green_score = 0
    count = 0
    
    for item in climate_data:
        ticker = item["ticker"]
        sector = sector_map.get(ticker, "Unknown")
        
        if sector.lower() in avoid_sectors_lower:
            continue
            
        real_esg = get_esg_score(ticker, item["climate_score"])
        
        if real_esg < esg_threshold:
            continue
            
        allowed_assets.append({
            "ticker": ticker,
            "sector": sector,
            "climate_score": real_esg,
            "risk_level": item["risk_level"]
        })
        total_green_score += real_esg
        count += 1
        
    avg_green_score = total_green_score / count if count > 0 else 0
    
    return {
        "green_score": round(avg_green_score, 2),
        "avoided_sectors_applied": avoid_sectors or [],
        "eligible_assets": allowed_assets
    }
