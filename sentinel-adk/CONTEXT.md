# Sentinel ADK Context

## 1. Project Purpose
Sentinel is a climate-aware autonomous investing multi-agent system built on the ADK 2.0 graph-based workflow. It leverages a chain of specialized agents to synthesize Environmental, Social, and Governance (ESG) criteria with real-time financial market signals, optimizing portfolios and executing risk-managed, sustainable trades.

## 2. Security Rules
- **No API Keys in Code**: Never commit or hardcode API keys, access tokens, or credentials within source code or configuration files.
- **Secrets via Environment Variables**: All secrets must be securely provided via environment variables (e.g., loading via `python-dotenv`).
- **No PII in Logs**: Strictly ensure that Personally Identifiable Information (PII) and sensitive financial data are stripped from all console outputs and local files (e.g., `audit_log.json`).

## 3. Agent Guardrails
- **Mandatory Guard Validation**: The `guard_agent` must intercept and successfully validate all trade intents against defined constraints (e.g., ESG thresholds, position sizing, restricted sectors) *before* any execution occurs.
- **Mandatory Explanations**: The `explain_agent` must always run as the final step of the pipeline to produce a transparent, human-readable summary of the pipeline's execution state and decisions.

## 4. Coding Standards
- **Type Hints**: All function arguments and return values must be explicitly typed using Python type hints (`typing` module).
- **Docstrings**: All agents, tool wrappers, and primary classes must contain clear, descriptive docstrings explaining their scope, inputs, and outputs.
- **No Bare Excepts**: Bare `except:` blocks are strictly forbidden. Always catch specific exceptions or use `except Exception as e:` and log the error context appropriately.
