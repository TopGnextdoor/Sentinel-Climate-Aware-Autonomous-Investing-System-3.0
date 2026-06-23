"""
Sentinel — Virtual Portfolio Model
In-memory paper trading system per user.
"""
import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


# ─── Pydantic Schemas ─────────────────────────────────────────

class TradeRecord(BaseModel):
    """Represents a single completed paper trade."""
    trade_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    action: str          # "BUY" | "SELL"
    ticker: str
    quantity: float
    price_per_share: float
    total_value: float
    notes: Optional[str] = None


class PortfolioHolding(BaseModel):
    """A single stock position in a portfolio."""
    ticker: str
    quantity: float
    avg_cost: float      # Average cost basis per share


class Portfolio(BaseModel):
    """Full virtual portfolio for one user."""
    portfolio_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    cash_balance: float = 100_000.0   # Start every user with $100k paper money
    initial_investment: float = 100_000.0
    holdings: Dict[str, PortfolioHolding] = {}
    trade_history: List[TradeRecord] = []


class PortfolioSummary(BaseModel):
    """API-safe summary returned to the frontend."""
    portfolio_id: str
    user_id: str
    cash_balance: float
    initial_investment: float
    holdings: Dict[str, PortfolioHolding]
    total_invested: float
    trade_count: int


# ─── In-Memory Store ──────────────────────────────────────────
# Keyed by user_id → Portfolio
# NOTE: Replace with SQLite or PostgreSQL for persistence.
_portfolio_store: Dict[str, Portfolio] = {}


# ─── CRUD Helpers ─────────────────────────────────────────────

def get_or_create_portfolio(user_id: str) -> Portfolio:
    """Return an existing portfolio or provision a fresh one for the user."""
    if user_id not in _portfolio_store:
        _portfolio_store[user_id] = Portfolio(user_id=user_id)
    return _portfolio_store[user_id]


def get_portfolio(user_id: str) -> Optional[Portfolio]:
    """Return portfolio for user, or None if not found."""
    return _portfolio_store.get(user_id)


def execute_buy(user_id: str, ticker: str, quantity: float, price: float) -> TradeRecord:
    """
    Execute a paper BUY order.
    Deducts cash and adds/increases the stock holding.
    Raises ValueError if insufficient funds.
    """
    portfolio = get_or_create_portfolio(user_id)
    total_cost = quantity * price

    if total_cost > portfolio.cash_balance:
        raise ValueError(
            f"Insufficient funds. Required: ${total_cost:,.2f}, "
            f"Available: ${portfolio.cash_balance:,.2f}"
        )

    # Deduct cash
    portfolio.cash_balance -= total_cost

    # Update holding (compute weighted average cost)
    if ticker in portfolio.holdings:
        existing = portfolio.holdings[ticker]
        total_qty = existing.quantity + quantity
        avg = ((existing.avg_cost * existing.quantity) + (price * quantity)) / total_qty
        portfolio.holdings[ticker] = PortfolioHolding(
            ticker=ticker, quantity=total_qty, avg_cost=avg
        )
    else:
        portfolio.holdings[ticker] = PortfolioHolding(
            ticker=ticker, quantity=quantity, avg_cost=price
        )

    # Log the trade
    record = TradeRecord(
        action="BUY",
        ticker=ticker,
        quantity=quantity,
        price_per_share=price,
        total_value=total_cost,
    )
    portfolio.trade_history.append(record)
    return record


def execute_sell(user_id: str, ticker: str, quantity: float, price: float) -> TradeRecord:
    """
    Execute a paper SELL order.
    Returns cash and reduces/removes the stock holding.
    Raises ValueError if insufficient shares.
    """
    portfolio = get_or_create_portfolio(user_id)

    if ticker not in portfolio.holdings:
        raise ValueError(f"No position in {ticker} to sell.")

    holding = portfolio.holdings[ticker]
    if quantity > holding.quantity:
        raise ValueError(
            f"Insufficient shares. Trying to sell {quantity}, "
            f"but only hold {holding.quantity} of {ticker}."
        )

    total_proceeds = quantity * price

    # Return cash
    portfolio.cash_balance += total_proceeds

    # Update or remove holding
    remaining = holding.quantity - quantity
    if remaining <= 0:
        del portfolio.holdings[ticker]
    else:
        portfolio.holdings[ticker] = PortfolioHolding(
            ticker=ticker, quantity=remaining, avg_cost=holding.avg_cost
        )

    # Log the trade
    record = TradeRecord(
        action="SELL",
        ticker=ticker,
        quantity=quantity,
        price_per_share=price,
        total_value=total_proceeds,
    )
    portfolio.trade_history.append(record)
    return record


def get_portfolio_summary(user_id: str) -> PortfolioSummary:
    """Returns a clean summary of the user's portfolio."""
    portfolio = get_or_create_portfolio(user_id)
    total_invested = sum(
        h.quantity * h.avg_cost for h in portfolio.holdings.values()
    )
    return PortfolioSummary(
        portfolio_id=portfolio.portfolio_id,
        user_id=user_id,
        cash_balance=portfolio.cash_balance,
        initial_investment=portfolio.initial_investment,
        holdings=portfolio.holdings,
        total_invested=total_invested,
        trade_count=len(portfolio.trade_history),
    )
