# Sentinel Climate-Aware Autonomous Investing System 2.0

## 1. Project Overview
Sentinel is a multi-agent autonomous investment system built on the Agent Development Kit (ADK). It orchestrates specialized AI agents to analyze live market data, evaluate environmental, social, and governance (ESG) metrics, simulate portfolio risk, and securely execute paper trades. By seamlessly integrating traditional finance with sustainability metrics, Sentinel empowers users to build robust, climate-conscious portfolios.

## 2. The Problem
Traditional automated investing platforms optimize purely for historical returns and volatility, treating climate risk as an afterthought. Conversely, dedicated ESG funds often suffer from rigid, opaque methodologies that lack real-time financial agility. Investors are forced to compromise—sacrificing either nuanced climate-awareness or responsive market execution.

## 3. The Solution
Sentinel bridges this gap using a **Sequential Multi-Agent Architecture**. Rather than a single monolithic AI, Sentinel splits the workflow into distinct expert agents. A climate expert evaluates carbon footprints, a financial analyst reviews market trends, a portfolio manager optimizes allocation, and a strict security guard enforces compliance. This modular approach ensures that every investment decision is rigorously vetted for both financial viability and climate impact before any trade is executed.

## 4. Architecture Pipeline
The ADK `SequentialAgent` passes context linearly through the following stages:

```text
User Request
     │
     ▼
[Climate Agent] ────► ESG & Emissions Analysis
     │
     ▼
[Financial Agent] ──► Market Trend & Price Analysis
     │
     ▼
[Simulation Agent] ─► Monte Carlo Risk Projections
     │
     ▼
[Portfolio Agent] ──► Asset Allocation & Optimization
     │
     ▼
[Trader Agent] ─────► Trade Proposal Generation
     │
     ▼
[Guard Agent] ──────► Policy Enforcement & Auditing
     │
     ▼
[Explain Agent] ────► Final Report Generation
     │
     ▼
User Response
```

## 5. Meet the Agents
- **Climate Agent**: Assesses the environmental viability of assets using ESG scores, carbon intensity metrics, and green sector classifications.
- **Financial Agent**: Evaluates traditional market signals, fetching live stock prices and assessing risk levels to ensure financial health.
- **Simulation Agent**: Runs Monte Carlo simulations based on budget and projected volatility to stress-test the proposed portfolio.
- **Portfolio Agent**: Synthesizes climate data and financial data to generate an optimized asset allocation strategy.
- **Trader Agent**: Converts the optimized allocation into actionable paper trade proposals for execution via the Alpaca API.
- **Guard Agent**: The final security checkpoint. It strictly enforces exclusion policies (e.g., blocking fossil fuels) and validates trade amounts against predefined constraints.
- **Explain Agent**: Translates the complex multi-agent JSON state into a clear, human-readable summary of actions taken and trades proposed.

## 6. MCP Servers
Sentinel utilizes the Model Context Protocol (MCP) to isolate tool execution into dedicated micro-servers. These servers are executed as child processes over STDIO:
- **ESG Server (`mcp_servers/esg/server.py`)**: Exposes tools for fetching ESG scores, carbon footprints, and tracking green sectors.
- **Market Server (`mcp_servers/market/server.py`)**: Interfaces with financial APIs to provide real-time stock prices and market trend indicators.
- **Policy Server (`mcp_servers/policy/server.py`)**: Stores active trading constraints, validates proposed trades against these rules, and writes immutable audit logs.

## 7. Setup Instructions

**Prerequisites:** Python 3.11+ and `uv` installed.

1. **Clone the Repository**
   ```bash
   git clone https://github.com/TopGnextdoor/Sentinel-Climate-Aware-Autonomous-Investing-System-2.0.git
   cd sentinel-adk
   ```
2. **Environment Variables**
   Copy the example environment file and add your API keys.
   ```bash
   cp .env.example .env
   # Edit .env with your GEMINI_API_KEY, ALPACA_KEY, and ALPACA_SECRET
   ```
3. **Install Dependencies**
   ```bash
   uv pip install --system -r pyproject.toml
   ```
4. **Run the Server Locally**
   ```bash
   uv run adk web
   ```
5. **Access the UI**
   Open your browser to `http://127.0.0.1:8000` to interact with Sentinel.

## 8. Security Features
Sentinel is built with a secure-by-design philosophy:
- **STRIDE Threat Modeling**: The architecture has been rigorously analyzed against the STRIDE framework, mitigating risks like LLM prompt injection and API key leakage.
- **Guard Agent**: A dedicated agent with absolute authority to block transactions. It cannot generate trades, only veto them if they violate ESG thresholds or portfolio limits.
- **Immutable Audit Logging**: Every trade decision—whether approved or blocked—is permanently logged in `data/audit_log.json` for forensic review.

## 9. Deployment
Sentinel is production-ready for Google Cloud Run via the `agents-cli`. 
For complete deployment instructions, including Secret Manager setup, please refer to the [Deployment Guide](docs/DEPLOYMENT.md).

## 10. Tech Stack

| Component | Technology |
|---|---|
| **Language** | Python 3.11 |
| **Agent Framework** | Agent Development Kit (ADK) |
| **LLM Engine** | Google Gemini (2.5 Flash & Flash-Lite) |
| **Tool Protocol** | Model Context Protocol (MCP) |
| **API Backend** | FastAPI |
| **Package Manager**| `uv` |
| **Trading API** | Alpaca |
| **Deployment** | Google Cloud Run, Docker |
