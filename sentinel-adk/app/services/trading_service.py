import os
import uuid
import logging
from typing import Dict, Any

try:
    import alpaca_trade_api as tradeapi
    ALPACA_AVAILABLE = True
except ImportError:
    ALPACA_AVAILABLE = False

logger = logging.getLogger(__name__)

def execute_alpaca_trade(trade: Dict[str, Any]) -> Dict[str, Any]:
    """Alpaca python SDK bindings and fallback simulated ID generation."""
    api_key = os.getenv("ALPACA_API_KEY")
    api_secret = os.getenv("ALPACA_SECRET_KEY")
    base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    
    ticker = trade.get("ticker", "UNKNOWN")
    action = trade.get("action", "buy").lower()
    quantity = trade.get("quantity", 0)

    if quantity <= 0:
        return {
            "status": "FAILED",
            "order_id": None,
            "symbol": ticker,
            "qty": quantity,
            "message": "Invalid or blocked trade quantity."
        }

    if ALPACA_AVAILABLE and api_key and api_secret:
        try:
            api = tradeapi.REST(api_key, api_secret, base_url, api_version='v2')
            order = api.submit_order(
                symbol=ticker,
                qty=quantity,
                side=action,
                type='market',
                time_in_force='gtc'
            )
            return {
                "status": "EXECUTED_LIVE_PAPER",
                "order_id": order.id,
                "symbol": order.symbol,
                "qty": float(order.qty),
                "message": f"Successfully placed {action} order for {quantity} shares of {ticker} on Alpaca Paper."
            }
        except Exception as e:
            logger.warning(f"Alpaca API failed, falling back to simulation. Error: {str(e)}")

    logger.info(f"Using fallback simulated paper-trade execution for {action} {quantity} {ticker}")
    return {
        "status": "EXECUTED_SIMULATED",
        "order_id": f"mock_alpaca_{uuid.uuid4().hex[:8]}",
        "symbol": ticker,
        "qty": quantity,
        "message": f"Simulated execution for {action} {quantity} shares of {ticker}."
    }
