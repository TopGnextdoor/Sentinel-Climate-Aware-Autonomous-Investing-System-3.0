from pydantic import BaseModel, ConfigDict
from typing import List, Dict, Any, Optional

class HealthResponse(BaseModel):
    status: str
    message: Optional[str] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "message": "Sentinel API is healthy"
            }
        }
    )

class GenericResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class AnalyzeResponse(BaseModel):
    climate_data: Optional[Dict[str, Any]] = None
    climate_scores: Optional[Dict[str, Any]] = None
    financial_data: Optional[Dict[str, Any]] = None
    portfolio: Optional[Dict[str, Any]] = None
    trade: Optional[Dict[str, Any]] = None
    guard: Optional[Dict[str, Any]] = None
    simulation: Optional[Dict[str, Any]] = None
    execution: Optional[Dict[str, Any]] = None
    explanation: Optional[str] = None
    orchestration: Optional[List[Dict[str, Any]]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticker": "AAPL",
                "insight": "Strong potential for green transition.",
                "score": 85.5
            }
        }
    )

class PortfolioResponse(BaseModel):
    user_id: Optional[str] = None
    total_value: float
    portfolio: Optional[List[Dict[str, Any]]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "usr_123",
                "total_value": 150000.0,
                "portfolio": [{"ticker": "AAPL", "shares": 50}]
            }
        }
    )

class ClimateScoresResponse(BaseModel):
    ticker: str
    climate_scores: Dict[str, Any]
    risk_level: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "ticker": "AAPL",
                "climate_scores": {"e_score": 88, "s_score": 75, "g_score": 90},
                "risk_level": "Low"
            }
        }
    )

class SimulateResponse(BaseModel):
    scenario: Optional[str] = None
    simulation_metrics: Dict[str, Any]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scenario": "Carbon Tax +50%",
                "simulation_metrics": {"portfolio_impact": -2.5, "var": 5.0}
            }
        }
    )

class ValidateTradeResponse(BaseModel):
    is_valid: bool
    guard_decision: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "is_valid": False,
                "guard_decision": "Trade exceeds sector concentration limits."
            }
        }
    )

class PoliciesResponse(BaseModel):
    policy: Dict[str, Any]
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "policy": {
                    "id": "p1", 
                    "name": "Carbon Tax", 
                    "description": "Tax on carbon emissions."
                }
            }
        }
    )

class ExecuteTradeResponse(BaseModel):
    trade_id: str
    execution_result: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "trade_id": "trd_987",
                "execution_result": "executed"
            }
        }
    )

class ExplainResponse(BaseModel):
    explanation_text: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "explanation_text": "Trade was rejected because the portfolio is currently overweight in the Energy sector."
            }
        }
    )
