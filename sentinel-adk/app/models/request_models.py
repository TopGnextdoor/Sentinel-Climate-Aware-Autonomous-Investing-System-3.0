from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict, Any

class AnalyzeRequest(BaseModel):
    budget: float
    risk_level: str
    max_trade: float
    avoid_sectors: List[str]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "budget": 10000.0,
                "risk_level": "Moderate",
                "max_trade": 5000.0,
                "avoid_sectors": ["Fossil Fuels", "Tobacco"]
            }
        }
    )

class PortfolioRequest(BaseModel):
    user_id: Optional[str] = None
    portfolio: Optional[List[Dict[str, Any]]] = None
    budget: Optional[float] = None
    risk_level: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "usr_123",
                "portfolio": [{"ticker": "AAPL", "shares": 50}],
                "budget": 10000.0,
                "risk_level": "moderate"
            }
        }
    )

class ClimateScoresRequest(BaseModel):
    tickers: List[str]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "tickers": ["AAPL", "MSFT"]
            }
        }
    )

class SimulateRequest(BaseModel):
    scenario: Optional[str] = None
    portfolio: Optional[List[Dict[str, Any]]] = None
    parameters: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scenario": "Carbon Tax +50%",
                "portfolio": [{"ticker": "AAPL", "shares": 50}],
                "parameters": {"tax_increase": 0.5}
            }
        }
    )

class ValidateTradeRequest(BaseModel):
    trade: Optional[Dict[str, Any]] = None
    portfolio: Optional[List[Dict[str, Any]]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "trade": {"ticker": "AAPL", "action": "buy", "quantity": 10},
                "portfolio": [{"ticker": "AAPL", "shares": 50}]
            }
        }
    )

class PoliciesRequest(BaseModel):
    region: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "region": "Global"
            }
        }
    )

class ExecuteTradeRequest(BaseModel):
    trade: Optional[Dict[str, Any]] = None
    max_trade: Optional[float] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "trade": {"ticker": "AAPL", "action": "buy", "quantity": 10},
                "max_trade": 5000.0
            }
        }
    )

class ExplainRequest(BaseModel):
    guard_decision: Optional[str] = None
    trade: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "guard_decision": "Trade blocked due to high climate risk.",
                "trade": {"ticker": "XOM", "action": "buy", "quantity": 100}
            }
        }
    )
