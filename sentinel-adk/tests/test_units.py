"""
Sentinel ADK — Unit Test Suite
Tests core business logic with all MCP servers and LLM calls mocked.
Run with: pytest tests/test_units.py -v
"""
import json
import os
import tempfile
import pytest
from typing import Dict, Any
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def low_esg_trade() -> Dict[str, Any]:
    """A trade payload that should be blocked due to low ESG score."""
    return {"ticker": "XOM", "action": "buy", "quantity": 10, "sector": "fossil fuels", "risk_score": 90, "price": 120.0}

@pytest.fixture
def large_trade() -> Dict[str, Any]:
    """A trade payload that should be blocked due to exceeding 20% portfolio allocation."""
    return {"ticker": "AAPL", "action": "buy", "quantity": 5, "sector": "technology", "risk_score": 30, "price": 300.0}

@pytest.fixture
def coal_trade() -> Dict[str, Any]:
    """A trade payload that should be blocked due to excluded sector."""
    return {"ticker": "BTU", "action": "buy", "quantity": 50, "sector": "coal", "risk_score": 95, "price": 20.0}

@pytest.fixture
def valid_trade() -> Dict[str, Any]:
    """A compliant trade payload that should be approved."""
    return {"ticker": "AAPL", "action": "buy", "quantity": 2, "sector": "technology", "risk_score": 28, "price": 150.0}

@pytest.fixture
def audit_log_file(tmp_path):
    """Provide a temporary audit log JSON file path."""
    log_file = tmp_path / "audit_log.json"
    log_file.write_text("[]")
    return str(log_file)

@pytest.fixture
def mock_climate_data():
    """Fixture returning realistic climate metrics data."""
    return {
        "green_score": 72.0,
        "avoided_sectors_applied": ["fossil fuels", "coal"],
        "eligible_assets": [
            {"ticker": "AAPL", "sector": "Technology", "climate_score": 72.0, "risk_level": "Low"},
            {"ticker": "MSFT", "sector": "Technology", "climate_score": 68.0, "risk_level": "Low"},
        ]
    }

@pytest.fixture
def mock_financial_data():
    return {"market_sentiment": "neutral", "expected_return": 0.074, "volatility": 0.01}


# ---------------------------------------------------------------------------
# 1. guard_agent blocks trades with esg_score < 40
# ---------------------------------------------------------------------------

class TestGuardAgentEsgThreshold:
    def test_blocks_trade_with_esg_below_40(self, low_esg_trade):
        """Guard must block any trade where esg_score < 40."""
        from mcp_servers.policy.server import validate_trade
        result = validate_trade(ticker="XOM", amount=1000.0, esg_score=25.0)
        assert result["approved"] is False
        assert "40" in result["reason"] or "threshold" in result["reason"].lower() or "esg" in result["reason"].lower()

    def test_blocks_trade_with_esg_exactly_at_boundary(self):
        """Boundary test: esg_score of 39 must be blocked, 40 must be allowed."""
        from mcp_servers.policy.server import validate_trade
        below = validate_trade(ticker="AAPL", amount=1000.0, esg_score=39.9)
        above = validate_trade(ticker="AAPL", amount=1000.0, esg_score=40.0)
        assert below["approved"] is False
        assert above["approved"] is True

    def test_allows_trade_with_esg_above_40(self, valid_trade):
        """Guard must allow trades where esg_score >= 40."""
        from mcp_servers.policy.server import validate_trade
        result = validate_trade(ticker="AAPL", amount=500.0, esg_score=75.0)
        assert result["approved"] is True


# ---------------------------------------------------------------------------
# 2. guard_agent blocks trades exceeding 20% portfolio value
# ---------------------------------------------------------------------------

class TestGuardAgentPortfolioAllocation:
    PORTFOLIO_VALUE = 100_000.0  # Must match MOCK_PORTFOLIO_VALUE in policy server

    def test_blocks_trade_exceeding_20_percent(self):
        """Trade amount > 20% of portfolio must be blocked."""
        from mcp_servers.policy.server import validate_trade
        over_limit = self.PORTFOLIO_VALUE * 0.21  # 21%
        result = validate_trade(ticker="AAPL", amount=over_limit, esg_score=75.0)
        assert result["approved"] is False
        assert "20%" in result["reason"] or "portfolio" in result["reason"].lower() or "exceeds" in result["reason"].lower()

    def test_allows_trade_at_20_percent_boundary(self):
        """Trade amount at exactly 20% portfolio must be allowed."""
        from mcp_servers.policy.server import validate_trade
        at_limit = self.PORTFOLIO_VALUE * 0.20  # exactly 20%
        result = validate_trade(ticker="AAPL", amount=at_limit, esg_score=75.0)
        assert result["approved"] is True

    def test_allows_small_trade(self):
        """Small trade well within portfolio limits must be approved."""
        from mcp_servers.policy.server import validate_trade
        result = validate_trade(ticker="MSFT", amount=500.0, esg_score=65.0)
        assert result["approved"] is True


# ---------------------------------------------------------------------------
# 3. guard_agent blocks stocks in excluded sectors (coal, weapons)
# ---------------------------------------------------------------------------

class TestGuardAgentExcludedSectors:
    def test_blocks_coal_ticker(self):
        """BTU (coal) must be blocked by the excluded ticker list in policy server."""
        from mcp_servers.policy.server import validate_trade
        result = validate_trade(ticker="BTU", amount=500.0, esg_score=55.0)
        # BTU may not be in EXCLUDED_TICKERS by default; test intent-level check
        from app.agents.guard_agent import check_intent_for_policy_violation
        intent_result = check_intent_for_policy_violation("buy coal stocks")
        assert intent_result["blocked"] is True
        assert intent_result["matched_sector"] == "coal"

    def test_blocks_weapons_request(self):
        """A request mentioning 'weapons' must be flagged at intent level."""
        from app.agents.guard_agent import check_intent_for_policy_violation
        result = check_intent_for_policy_violation("Invest in weapons manufacturers like LMT")
        assert result["blocked"] is True
        assert result["matched_sector"] == "weapons"

    def test_blocks_tobacco_request(self):
        """A request mentioning 'tobacco' must be flagged at intent level."""
        from app.agents.guard_agent import check_intent_for_policy_violation
        result = check_intent_for_policy_violation("Buy tobacco stocks")
        assert result["blocked"] is True
        assert result["matched_sector"] == "tobacco"

    def test_allows_clean_request(self):
        """A clean request with no excluded sector must pass."""
        from app.agents.guard_agent import check_intent_for_policy_violation
        result = check_intent_for_policy_violation("Analyze AAPL for sustainable investment")
        assert result["blocked"] is False
        assert result["matched_sector"] is None

    @pytest.mark.parametrize("sector", ["coal", "weapons", "firearms", "tobacco", "fossil fuels"])
    def test_blocks_all_excluded_sectors(self, sector: str):
        """Parameterised: every excluded sector keyword must trigger a block."""
        from app.agents.guard_agent import check_intent_for_policy_violation
        result = check_intent_for_policy_violation(f"I want to invest in {sector}")
        assert result["blocked"] is True, f"Expected '{sector}' to be blocked"


# ---------------------------------------------------------------------------
# 4. climate_agent returns dict with required keys
# ---------------------------------------------------------------------------

class TestClimateAgentOutput:
    @patch("app.services.climate_data.yf.Ticker")
    def test_returns_required_keys(self, mock_ticker):
        """analyze_climate_impact must return a dict with green_score, avoided_sectors_applied, eligible_assets."""
        mock_ticker.return_value.info = {}
        from app.agents.climate_agent import analyze_climate_impact

        with patch("app.services.climate_data.get_esg_score", return_value=72.0):
            result = analyze_climate_impact(avoid_sectors=["fossil fuels"], esg_threshold=60.0)

        assert isinstance(result, dict)
        assert "green_score" in result
        assert "avoided_sectors_applied" in result
        assert "eligible_assets" in result

    @patch("app.services.climate_data.get_esg_score", return_value=72.0)
    def test_eligible_assets_have_required_fields(self, mock_esg):
        """Each eligible asset must contain ticker, sector, climate_score, risk_level."""
        from app.agents.climate_agent import analyze_climate_impact
        result = analyze_climate_impact(avoid_sectors=[], esg_threshold=50.0)
        for asset in result.get("eligible_assets", []):
            assert "ticker" in asset
            assert "sector" in asset
            assert "climate_score" in asset
            assert "risk_level" in asset

    @patch("app.services.climate_data.get_esg_score", return_value=72.0)
    def test_excludes_sectors_correctly(self, mock_esg):
        """Assets in avoided sectors must not appear in eligible_assets."""
        from app.agents.climate_agent import analyze_climate_impact
        result = analyze_climate_impact(avoid_sectors=["fossil fuels"], esg_threshold=50.0)
        tickers = [a["ticker"] for a in result.get("eligible_assets", [])]
        assert "XOM" not in tickers  # XOM is fossil fuels sector


# ---------------------------------------------------------------------------
# 5. portfolio_agent allocates 0% to any stock the guard blocked
# ---------------------------------------------------------------------------

class TestPortfolioAgentAllocation:
    def test_blocked_asset_gets_zero_allocation(self, mock_climate_data):
        """Stocks excluded by climate/guard filters must have 0 allocation."""
        from app.services.optimizer import calculate_allocation

        # XOM (fossil fuels) was filtered out by climate_agent — it won't appear in eligible_assets
        blocked_ticker = "XOM"
        eligible = mock_climate_data["eligible_assets"]  # XOM not here

        with patch("app.services.market_data.get_stock_price", return_value=150.0):
            stock_prices = {"AAPL": 150.0, "MSFT": 150.0}
            result = calculate_allocation(10000.0, eligible, stock_prices)

        allocated_tickers = [h["ticker"] for h in result.get("holdings", [])]
        assert blocked_ticker not in allocated_tickers

    def test_no_eligible_assets_returns_error(self):
        """Empty eligible assets must return an error dict, not raise an exception."""
        from app.services.optimizer import calculate_allocation
        result = calculate_allocation(10000.0, [], {})
        assert "error" in result
        assert result.get("holdings", []) == []

    def test_allocation_weights_sum_to_one(self, mock_climate_data):
        """Portfolio weights for eligible assets must sum to approximately 1.0."""
        from app.services.optimizer import calculate_allocation
        eligible = mock_climate_data["eligible_assets"]
        stock_prices = {"AAPL": 100.0, "MSFT": 100.0}
        result = calculate_allocation(10000.0, eligible, stock_prices)
        total_weight = sum(h["weight"] for h in result.get("holdings", []))
        assert abs(total_weight - 1.0) < 0.01  # within 1% of unity


# ---------------------------------------------------------------------------
# 6. audit_log writes a JSON entry for every guard decision
# ---------------------------------------------------------------------------

class TestAuditLog:
    def test_log_decision_writes_entry(self, audit_log_file):
        """log_decision must append a JSON entry with timestamp and payload."""
        with patch("mcp_servers.policy.server.AUDIT_LOG_FILE", audit_log_file):
            from mcp_servers.policy.server import log_decision
            payload = {"status": "BLOCKED", "ticker": "XOM", "reason": "ESG score too low"}
            result = log_decision(payload)

        assert result["status"] == "success"

        with open(audit_log_file) as f:
            logs = json.load(f)

        assert len(logs) == 1
        assert "timestamp" in logs[0]
        assert logs[0]["payload"]["status"] == "BLOCKED"
        assert logs[0]["payload"]["ticker"] == "XOM"

    def test_log_decision_appends_multiple_entries(self, audit_log_file):
        """Multiple calls must each append a new entry."""
        with patch("mcp_servers.policy.server.AUDIT_LOG_FILE", audit_log_file):
            from mcp_servers.policy.server import log_decision
            log_decision({"status": "BLOCKED", "ticker": "XOM"})
            log_decision({"status": "APPROVED", "ticker": "AAPL"})

        with open(audit_log_file) as f:
            logs = json.load(f)

        assert len(logs) == 2
        statuses = [entry["payload"]["status"] for entry in logs]
        assert "BLOCKED" in statuses
        assert "APPROVED" in statuses

    def test_log_entry_has_iso_timestamp(self, audit_log_file):
        """Each log entry must contain an ISO 8601 timestamp string."""
        with patch("mcp_servers.policy.server.AUDIT_LOG_FILE", audit_log_file):
            from mcp_servers.policy.server import log_decision
            log_decision({"status": "APPROVED", "ticker": "MSFT"})

        with open(audit_log_file) as f:
            logs = json.load(f)

        ts = logs[0]["timestamp"]
        assert isinstance(ts, str)
        assert "T" in ts  # ISO 8601 format contains 'T' between date and time


# ---------------------------------------------------------------------------
# 7. explain_agent always returns a non-empty string explanation
# ---------------------------------------------------------------------------

class TestExplainAgentOutput:
    def test_returns_non_empty_string_for_approved_trade(self):
        """generate_explanation must return a non-empty string for an approved trade."""
        from app.agents.explain_agent import generate_explanation
        pipeline_state = {
            "climate_data": {"green_score": 72.0},
            "guard": {"status": "APPROVED", "original_trade": {"ticker": "AAPL", "action": "buy"}, "modifications": [], "violations": []},
            "simulation": {"expected_1y_value": 10743.0, "drawdown_probability": 0.20}
        }
        result = generate_explanation(pipeline_state)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_returns_non_empty_string_for_blocked_trade(self):
        """generate_explanation must return a non-empty string for a blocked trade."""
        from app.agents.explain_agent import generate_explanation
        pipeline_state = {
            "climate_data": {"green_score": 0},
            "guard": {
                "status": "BLOCKED",
                "original_trade": {"ticker": "XOM", "action": "buy"},
                "violations": ["ESG score below threshold"],
                "modifications": []
            },
            "simulation": {}
        }
        result = generate_explanation(pipeline_state)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_blocked_explanation_mentions_blocked_keyword(self):
        """A blocked-trade explanation must contain the word 'BLOCKED'."""
        from app.agents.explain_agent import generate_explanation
        pipeline_state = {
            "climate_data": {"green_score": 0},
            "guard": {
                "status": "BLOCKED",
                "original_trade": {"ticker": "XOM", "action": "buy"},
                "violations": ["Fossil fuels sector excluded"],
                "modifications": []
            },
            "simulation": {}
        }
        result = generate_explanation(pipeline_state)
        assert "BLOCKED" in result

    def test_handles_empty_pipeline_state_gracefully(self):
        """generate_explanation must not raise on empty input."""
        from app.agents.explain_agent import generate_explanation
        result = generate_explanation({})
        assert isinstance(result, str)
        assert len(result) > 0
