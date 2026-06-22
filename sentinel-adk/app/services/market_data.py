import yfinance as yf
from typing import Dict, List, Any

# Fallback fake data in case API fails
FALLBACK_PRICES = {
    "AAPL": 189.23,
    "MSFT": 402.11,
    "TSLA": 251.44,
    "XOM": 105.30,
    "NEE": 70.00
}

def get_stock_price(ticker: str) -> float:
    """Fetch real-time stock price for a single ticker."""
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if not data.empty:
            return float(data["Close"].iloc[-1])
        else:
            return float(FALLBACK_PRICES.get(ticker, 100.0))
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return float(FALLBACK_PRICES.get(ticker, 100.0))

def get_multiple_prices(tickers: List[str]) -> Dict[str, float]:
    """Fetch real-time stock prices for multiple tickers."""
    prices = {}
    for ticker in tickers:
        prices[ticker] = get_stock_price(ticker)
    return prices

def get_stock_prices() -> Dict[str, float]:
    """Retrieve sample stock prices (backward compatible wrapper)."""
    return get_multiple_prices(list(FALLBACK_PRICES.keys()))

def get_market_signals(ticker: str) -> Dict[str, Any]:
    """
    Fetch recent price history for a ticker and compute:
      - daily_return  : percentage price change over the last 2 closes
      - volatility    : std dev of daily returns over the last 5 days
      - volume        : most recent volume
      - sentiment     : 'bullish' | 'bearish' | 'neutral'
      - sentiment_label: human-readable explanation
    Falls back to neutral signals if data is unavailable.
    """
    try:
        data = yf.Ticker(ticker).history(period="5d")
        if data.empty or len(data) < 2:
            raise ValueError("Insufficient data")

        closes = data["Close"].tolist()
        volumes = data["Volume"].tolist()

        # Daily percentage returns
        daily_returns = [
            (closes[i] - closes[i - 1]) / closes[i - 1]
            for i in range(1, len(closes))
        ]

        daily_return  = round(daily_returns[-1] * 100, 4)   # most recent day, in %
        avg_return    = sum(daily_returns) / len(daily_returns)
        n             = len(daily_returns)
        variance      = sum((r - avg_return) ** 2 for r in daily_returns) / n
        volatility    = round(variance ** 0.5 * 100, 4)     # std dev in %
        volume        = int(volumes[-1])

        # Sentiment logic: driven by the 5-day average trend
        if avg_return > 0.003:       # +0.3 % avg → bullish
            sentiment = "bullish"
            label = f"Bullish based on {round(avg_return*100,2)}% avg 5-day return"
        elif avg_return < -0.003:    # -0.3 % avg → bearish
            sentiment = "bearish"
            label = f"Bearish based on {round(avg_return*100,2)}% avg 5-day return"
        else:
            sentiment = "neutral"
            label = f"Neutral — minimal price movement ({round(avg_return*100,2)}% avg)"

        return {
            "ticker": ticker,
            "daily_return_pct": daily_return,
            "volatility_pct": volatility,
            "volume": volume,
            "sentiment": sentiment,
            "sentiment_label": label,
        }

    except Exception as e:
        return {
            "ticker": ticker,
            "daily_return_pct": 0.0,
            "volatility_pct": 0.0,
            "volume": 0,
            "sentiment": "neutral",
            "sentiment_label": f"Neutral — data unavailable ({e})",
        }

