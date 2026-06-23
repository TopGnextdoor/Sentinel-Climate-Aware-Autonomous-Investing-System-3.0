import logging
import pytest
from unittest.mock import patch, MagicMock
from google.api_core.exceptions import ResourceExhausted
from app.agents.base_agent import BaseAgent

class MockAgent(BaseAgent):
    pass

@patch("time.sleep", return_value=None)
def test_gemini_retry_twice_then_succeeds(mock_sleep, caplog):
    # Set caplog to capture WARNING logs
    caplog.set_level(logging.WARNING)
    
    agent = MockAgent(name="retry_test_agent")
    
    # Mock _execute_llm_call to raise ResourceExhausted twice, then return "final_success"
    mock_call = MagicMock()
    mock_call.side_effect = [
        ResourceExhausted("Quota limit exceeded"),
        ResourceExhausted("Quota limit exceeded"),
        "final_success"
    ]
    
    agent._execute_llm_call = mock_call
    
    # Call call_llm
    result = agent.call_llm("test prompt")
    
    # Asserts
    assert result == "final_success"
    assert mock_call.call_count == 3
    
    # Verify warning logs
    warning_logs = [record.message for record in caplog.records if record.levelno == logging.WARNING]
    assert len(warning_logs) == 2
    
    # Logs should contain attempt number, wait time, and which agent triggered it
    assert "Retry attempt 1" in warning_logs[0]
    assert "retry_test_agent" in warning_logs[0]
    assert "Waiting" in warning_logs[0]
    
    assert "Retry attempt 2" in warning_logs[1]
    assert "retry_test_agent" in warning_logs[1]
    assert "Waiting" in warning_logs[1]
