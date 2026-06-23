"""
Sentinel — Portfolio Service Layer
Centralizes all portfolio operations: init, query, and trade execution.
Delegates storage to app.models.portfolio and price fetching to market_data.
"""
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.models.portfolio import (
    Portfolio,
    PortfolioSummary,
    TradeRecord,
    get_or_create_portfolio,
    get_portfolio,
    get_portfolio_summary,
    execute_buy,
    execute_sell,
)
from app.services.market_data import get_stock_price


# ─── Public Service API ───────────────────────────────────────

def initialize_portfolio(user_id: str, initial_cash: float = 100_000.0) -> PortfolioSummary:
    """
    Provision a brand-new paper portfolio for a user.
    If one already exists, returns its current state unchanged.

    Args:
        user_id:      The authenticated user's ID (from JWT 'sub').
        initial_cash: Starting balance, defaults to $100,000.

    Returns:
        PortfolioSummary
    """
    from app.models.portfolio import _portfolio_store, Portfolio

    if user_id not in _portfolio_store:
        _portfolio_store[user_id] = Portfolio(
            user_id=user_id,
            cash_balance=initial_cash,
        )

    return get_portfolio_summary(user_id)


def get_portfolio_for_user(user_id: str) -> PortfolioSummary:
    """
    Fetch and return the current portfolio summary for a user.
    Auto-provisions with default $100k if none exists yet.

    Args:
        user_id: The authenticated user's ID.

    Returns:
        PortfolioSummary (safe for JSON serialization)
    """
    return get_portfolio_summary(user_id)


def update_portfolio_after_trade(
    user_id: str,
    trade: Dict[str, Any],
    price_override: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Execute a BUY or SELL paper trade and update the user's portfolio.

    Trade format:
        {
            "stock":    "AAPL",
            "quantity": 10,
            "action":   "BUY"   # or "SELL"
        }

    Args:
        user_id:        Authenticated user's ID.
        trade:          Trade dict with stock, quantity, action.
        price_override: Optional price (skips live fetch). Used in tests or
                        when caller already has the current price.

    Returns:
        Dict with trade_record, updated portfolio summary, and live price used.

    Raises:
        ValueError: On bad trade data, insufficient funds, or insufficient shares.
    """
    # ── Validate input ────────────────────────────────────────
    ticker   = str(trade.get("stock", "")).upper().strip()
    quantity = float(trade.get("quantity", 0))
    action   = str(trade.get("action", "")).upper().strip()

    if not ticker:
        raise ValueError("Trade must include a valid 'stock' ticker.")
    if quantity <= 0:
        raise ValueError("Trade 'quantity' must be a positive number.")
    if action not in ("BUY", "SELL"):
        raise ValueError(f"Trade 'action' must be 'BUY' or 'SELL', got '{action}'.")

    # ── Fetch live price ──────────────────────────────────────
    price = price_override if price_override is not None else get_stock_price(ticker)

    if price <= 0:
        raise ValueError(f"Could not determine a valid price for '{ticker}'.")

    # ── Execute trade ─────────────────────────────────────────
    if action == "BUY":
        record: TradeRecord = execute_buy(user_id, ticker, quantity, price)
    else:
        record: TradeRecord = execute_sell(user_id, ticker, quantity, price)

    # ── Return result ─────────────────────────────────────────
    summary = get_portfolio_summary(user_id)

    return {
        "status":    "executed",
        "action":    action,
        "ticker":    ticker,
        "quantity":  quantity,
        "price":     price,
        "total_value": record.total_value,
        "trade_id":  record.trade_id,
        "timestamp": record.timestamp,
        "portfolio": summary.model_dump(),
    }


def get_trade_history(user_id: str) -> list:
    """
    Return the full trade log for a user.

    Args:
        user_id: Authenticated user's ID.

    Returns:
        List of TradeRecord dicts, newest first.
    """
    portfolio = get_or_create_portfolio(user_id)
    return [t.model_dump() for t in reversed(portfolio.trade_history)]


def get_portfolio_value(user_id: str) -> Dict[str, Any]:
    """
    Compute total portfolio value including cash + current market value of holdings.

    Returns:
        Dict with cash, holdings_value, total_value, and per-holding breakdown.
    """
    portfolio = get_or_create_portfolio(user_id)
    breakdown = []
    holdings_value = 0.0

    for ticker, holding in portfolio.holdings.items():
        current_price = get_stock_price(ticker)
        market_value  = holding.quantity * current_price
        cost_basis    = holding.quantity * holding.avg_cost
        pnl           = market_value - cost_basis
        pnl_pct       = (pnl / cost_basis * 100) if cost_basis > 0 else 0.0
        holdings_value += market_value

        breakdown.append({
            "ticker":        ticker,
            "quantity":      holding.quantity,
            "avg_cost":      round(holding.avg_cost, 2),
            "current_price": round(current_price, 2),
            "market_value":  round(market_value, 2),
            "cost_basis":    round(cost_basis, 2),
            "pnl":           round(pnl, 2),
            "pnl_pct":       round(pnl_pct, 2),
        })

    total_value = portfolio.cash_balance + holdings_value
    profit_loss = total_value - portfolio.initial_investment

    return {
        "user_id":            user_id,
        "cash":               round(portfolio.cash_balance, 2),
        # Legacy aliases kept for backward compatibility
        "cash_balance":       round(portfolio.cash_balance, 2),
        "holdings_value":     round(holdings_value, 2),
        "total_value":        round(total_value, 2),
        "initial_investment": round(portfolio.initial_investment, 2),
        "profit_loss":        round(profit_loss, 2),
        "holdings":           breakdown,
    }


def get_performance_summary(user_id: str) -> Dict[str, Any]:
    """
    Full performance snapshot for the authenticated user.

    Computes every metric the frontend Performance panel needs:
      - total_value, cash, holdings_value
      - overall_pnl, overall_pnl_pct  (unrealized gain/loss vs cost basis)
      - initial_capital                (inferred from trade history)
      - per-holding breakdown with unrealized P&L
      - best_performer / worst_performer
      - trade_count, win_rate          (realized trades where proceeds > cost)

    Returns a dict safe for direct JSON serialization.
    """
    portfolio        = get_or_create_portfolio(user_id)
    holdings_value   = 0.0
    total_cost_basis = 0.0
    breakdown        = []

    # ── Live holding valuations ───────────────────────────────────────────────
    for ticker, holding in portfolio.holdings.items():
        current_price = get_stock_price(ticker)
        market_value  = holding.quantity * current_price
        cost_basis    = holding.quantity * holding.avg_cost
        pnl           = market_value - cost_basis
        pnl_pct       = (pnl / cost_basis * 100) if cost_basis > 0 else 0.0

        holdings_value   += market_value
        total_cost_basis += cost_basis

        breakdown.append({
            "ticker":        ticker,
            "quantity":      holding.quantity,
            "avg_cost":      round(holding.avg_cost, 2),
            "current_price": round(current_price, 2),
            "market_value":  round(market_value, 2),
            "cost_basis":    round(cost_basis, 2),
            "pnl":           round(pnl, 2),
            "pnl_pct":       round(pnl_pct, 2),
        })

    # ── Aggregate portfolio-level figures ─────────────────────────────────────
    total_value  = portfolio.cash_balance + holdings_value
    overall_pnl  = holdings_value - total_cost_basis
    overall_pnl_pct = (
        (overall_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0.0
    )

    # ── Best / worst performers ───────────────────────────────────────────────
    best  = max(breakdown, key=lambda h: h["pnl_pct"], default=None)
    worst = min(breakdown, key=lambda h: h["pnl_pct"], default=None)

    # ── Trade win-rate (realized: SELL proceeds > buy cost basis) ─────────────
    sell_trades  = [t for t in portfolio.trade_history if t.action == "SELL"]
    buy_map: Dict[str, float] = {}   # ticker → avg_cost at time of buy (approx)
    # Build a running avg_cost from BUY records in order
    for t in portfolio.trade_history:
        if t.action == "BUY":
            prev = buy_map.get(t.ticker, t.price_per_share)
            buy_map[t.ticker] = (prev + t.price_per_share) / 2

    win_trades = sum(
        1 for t in sell_trades
        if t.price_per_share > buy_map.get(t.ticker, t.price_per_share)
    )
    win_rate = (win_trades / len(sell_trades) * 100) if sell_trades else None

    # ── Initial investment & absolute profit ──────────────────────────────────
    total_bought = sum(t.total_value for t in portfolio.trade_history if t.action == "BUY")
    total_sold   = sum(t.total_value for t in portfolio.trade_history if t.action == "SELL")
    profit_loss  = total_value - portfolio.initial_investment

    return {
        # ── Core valuation ─────────────────────────────────────────────────
        "user_id":            user_id,
        "total_value":        round(total_value, 2),
        "cash":               round(portfolio.cash_balance, 2),
        "cash_balance":       round(portfolio.cash_balance, 2),   # alias
        "holdings_value":     round(holdings_value, 2),

        # ── P&L ────────────────────────────────────────────────────────────
        "initial_investment": round(portfolio.initial_investment, 2),
        "profit_loss":        round(profit_loss, 2),
        "total_cost_basis":   round(total_cost_basis, 2),
        "overall_pnl":      round(overall_pnl, 2),
        "overall_pnl_pct":  round(overall_pnl_pct, 2),

        # ── Holdings breakdown ─────────────────────────────────────────────
        "holdings":         breakdown,

        # ── Star performers ────────────────────────────────────────────────
        "best_performer":  {
            "ticker":  best["ticker"],
            "pnl_pct": best["pnl_pct"],
            "pnl":     best["pnl"],
        } if best else None,
        "worst_performer": {
            "ticker":  worst["ticker"],
            "pnl_pct": worst["pnl_pct"],
            "pnl":     worst["pnl"],
        } if worst else None,

        # ── Activity stats ─────────────────────────────────────────────────
        "trade_count":      len(portfolio.trade_history),
        "buy_count":        sum(1 for t in portfolio.trade_history if t.action == "BUY"),
        "sell_count":       len(sell_trades),
        "win_rate_pct":     round(win_rate, 1) if win_rate is not None else None,
        "total_bought":     round(total_bought, 2),
        "total_sold":       round(total_sold, 2),
    }

