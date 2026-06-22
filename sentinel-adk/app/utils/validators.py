def is_valid_ticker(ticker: str) -> bool:
    """Basic validation for a stock ticker."""
    return isinstance(ticker, str) and 1 <= len(ticker) <= 5 and ticker.isalpha()

def is_valid_trade_action(action: str) -> bool:
    """Basic validation for a trade action."""
    return action.lower() in ["buy", "sell"]
