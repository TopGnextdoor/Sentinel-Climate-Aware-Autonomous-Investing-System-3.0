# Sentinel Climate-Aware Autonomous Investing System 3.0

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
[Explain Agent] ────► Final Report Generation (Direct OpenRouter LLM Fallback)
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

## 6. Real-time Multi-Model LLM Fallback
To ensure high availability and bypass potential rate-limiting, the Final Report Generation (`Explain Agent` stage) is executed using a direct OpenRouter connection with automated multi-model fallback. The pipeline queries the following models sequentially until a successful response is received:
1. `meta-llama/llama-3.3-70b-instruct:free`
2. `google/gemma-4-31b-it:free`
3. `google/gemma-4-26b-a4b-it:free`
4. `qwen/qwen3-coder:free`
5. `openai/gpt-oss-120b:free`
6. `meta-llama/llama-3.2-3b-instruct:free`

## 7. Setup Instructions

**Prerequisites:** Python 3.11+ and `uv` installed.

1. **Clone the Repository**
   ```bash
   git clone https://github.com/TopGnextdoor/Sentinel-Climate-Aware-Autonomous-Investing-System-3.0.git
   cd sentinel-adk
   ```
2. **Environment Variables**
   Copy the example environment file and add your API keys.
   ```bash
   cp .env.example .env
   # Edit .env with your OPENROUTER_API_KEY and other configuration values
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
   Open your browser to `http://127.0.0.1:8000` to interact with Sentinel's dark glassmorphic user interface.

## 8. Deployment on Render

Sentinel can be easily hosted on [Render](https://render.com/) using the provided `Dockerfile`.

1. Create a new **Web Service** on Render and link it to your GitHub Repository.
2. Select **Docker** as the Runtime.
3. In the environment variables configuration on Render, add:
   - `OPENROUTER_API_KEY`: Your OpenRouter API Key (required for report generation)
4. Render will automatically build the image using the `Dockerfile` and bind it to the dynamic `$PORT` specified at runtime.

## 9. Security Features
Sentinel is built with a secure-by-design philosophy:
- **STRIDE Threat Modeling**: The architecture has been analyzed against the STRIDE framework to mitigate LLM prompt injection and credential leakage.
- **Guard Agent**: A dedicated agent with absolute authority to block transactions. It cannot generate trades, only veto them if they violate ESG thresholds or portfolio limits.
- **Immutable Audit Logging**: Every trade decision—whether approved or blocked—is permanently logged in `data/audit_log.json` for forensic review.

## 10. Tech Stack

| Component | Technology |
|---|---|
| **Language** | Python 3.11 |
| **Agent Framework** | Agent Development Kit (ADK) |
| **LLM Engine** | OpenRouter Free Tier (Llama 3.3 70B, Gemma 4, Qwen 3) |
| **Tool Protocol** | Model Context Protocol (MCP) |
| **API Backend** | FastAPI |
| **Package Manager**| `uv` |
| **Trading API** | Alpaca |
| **Deployment** | Render, Docker |
