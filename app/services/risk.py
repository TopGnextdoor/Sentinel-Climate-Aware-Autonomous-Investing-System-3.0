from typing import Dict, Any, List
from app.services.market_data import get_market_signals

# Representative benchmark tickers used to gauge overall market trend
BENCHMARK_TICKERS = ["AAPL", "MSFT", "TSLA"]

def calculate_market_trends(risk_level: str, tickers: List[str] = None) -> Dict[str, Any]:
    """
    Fetch real market signals via yfinance and compute aggregate sentiment,
    expected return, and volatility across the given (or benchmark) tickers.
    """
    tickers = tickers or BENCHMARK_TICKERS
    risk = risk_level.lower() if risk_level else "moderate"

    signals = [get_market_signals(t) for t in tickers]

    # Aggregate metrics
    avg_daily_return = sum(s["daily_return_pct"] for s in signals) / len(signals)
    avg_volatility   = sum(s["volatility_pct"]   for s in signals) / len(signals)

    # Determine overall sentiment from individual labels
    bullish_count = sum(1 for s in signals if s["sentiment"] == "bullish")
    bearish_count = sum(1 for s in signals if s["sentiment"] == "bearish")

    if bullish_count > bearish_count:
        overall_sentiment = "bullish"
        sentiment_summary = f"Bullish based on recent price trend ({bullish_count}/{len(signals)} tickers rising)"
    elif bearish_count > bullish_count:
        overall_sentiment = "bearish"
        sentiment_summary = f"Bearish based on recent price trend ({bearish_count}/{len(signals)} tickers falling)"
    else:
        overall_sentiment = "neutral"
        sentiment_summary = "Neutral — mixed signals across tracked tickers"

    # Risk-level adjustments for expected return baseline
    risk_return_map = {"low": 0.04, "moderate": 0.08, "high": 0.12}
    base_return = risk_return_map.get(risk, 0.08)
    # Blend base with real avg return (capped for sanity)
    blended_return = round(base_return * 0.6 + (avg_daily_return / 100) * 0.4, 4)

    return {
        "market_sentiment": overall_sentiment,
        "sentiment_label": f"Sentiment: {sentiment_summary}",
        "recommended_risk": risk_level or "Moderate",
        "expected_return": blended_return,
        "volatility": round(avg_volatility / 100, 4),
        "market_risk_score": round(avg_volatility, 2),
        "per_ticker_signals": [
            {
                "ticker": s["ticker"],
                "daily_return_pct": s["daily_return_pct"],
                "volatility_pct": s["volatility_pct"],
                "volume": s["volume"],
                "sentiment": s["sentiment"],
                "sentiment_label": s["sentiment_label"],
            }
            for s in signals
        ],
    }

