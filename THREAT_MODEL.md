# Sentinel ADK: STRIDE Threat Model Analysis

This document outlines the threat model for the Sentinel ADK climate-aware autonomous investing system. The analysis focuses on four critical attack surfaces:
1. The `/analyze` API endpoint (user-controlled input)
2. The `trader_agent` (Alpaca trade execution)
3. The MCP servers (external tool integrations)
4. The audit log (persistent data store)

---

## 1. Spoofing (Identity verification)
**Top Risk**: An attacker bypasses authentication on the `/analyze` API endpoint to submit unauthorized trade analysis requests, or a malicious local process spoofs an MCP server (e.g., `sentinel-policy-mcp`) to feed false approvals to the `guard_agent`.
**Attack Surface**: `/analyze` API endpoint & MCP servers.
**Mitigation**: 
- **API**: Enforce strict OAuth2/JWT authentication on the `/analyze` endpoint. 
- **MCP**: Require mutually authenticated TLS (mTLS) or secure, authenticated local transport (like secure UNIX domain sockets) between the ADK pipeline and MCP servers to ensure agents only communicate with trusted tool providers.

## 2. Tampering (Data integrity)
**Top Risk**: An attacker or compromised process modifies the local `data/audit_log.json` to cover tracks of an illicit trade or policy violation, destroying the integrity of the compliance trail.
**Attack Surface**: Audit log.
**Mitigation**: 
- Move the audit trail from a local JSON file to a secure, append-only logging system (e.g., Google Cloud Logging, AWS CloudTrail, or a WORM-compliant database). If local files must be used temporarily, implement strict file-system permissions and File Integrity Monitoring (FIM).

## 3. Repudiation (Non-deniability)
**Top Risk**: A user initiates a highly risky trade that bypasses a flawed policy, but later denies making the request. Because the `trader_agent` relies on pipeline context, if the origin identity is lost in the graph execution, the system cannot prove who initiated the trade.
**Attack Surface**: `trader_agent` & Audit log.
**Mitigation**: 
- Implement end-to-end trace context. Pass the authenticated user's ID/token from the `/analyze` endpoint entirely through the ADK sequential pipeline. The `guard_agent` must explicitly bind this User ID to the trade payload when calling the `log_decision` MCP tool.

## 4. Information Disclosure (Data confidentiality)
**Top Risk**: The MCP servers or the ADK framework inadvertently leak sensitive execution context (such as the Alpaca API keys used by the `trader_agent` or proprietary ESG threshold data) into the `explain_agent`'s output or the local audit log during an error stack trace.
**Attack Surface**: MCP servers & Audit log.
**Mitigation**: 
- Implement an outbound data redaction filter. Ensure that all secrets are injected at runtime via secure environment variables and never passed back as tool return values. Apply regex-based secret scrubbing before writing any payload to `audit_log.json` or returning the explanation to the user.

## 5. Denial of Service (System availability)
**Top Risk**: A malicious actor spams the `/analyze` API endpoint with complex, nested prompts. Because the ADK pipeline heavily utilizes LLM inference (Gemini), this could exhaust model quotas, cause financial resource exhaustion (bill shock), and block legitimate trading operations.
**Attack Surface**: `/analyze` API endpoint.
**Mitigation**: 
- Implement aggressive API rate limiting (e.g., token bucket algorithm) per user IP and authenticated identity. Set hard timeout constraints on the ADK execution graph and configure maximum token limits on the Gemini model configurations to cap processing costs per request.

## 6. Elevation of Privilege (Authorization limits)
**Top Risk**: An attacker uses Prompt Injection via the `/analyze` endpoint to trick the `trader_agent` into executing trades outside their authorized scope, or attempts to explicitly instruct the `guard_agent` to ignore the ESG constraints.
**Attack Surface**: `/analyze` API endpoint & `trader_agent`.
**Mitigation**: 
- **Agent Isolation**: Use a Defense-in-Depth strategy. The `guard_agent` must be isolated from user instructions; its prompt must strictly define that it answers *only* to the policy MCP server rules, ignoring any upstream user context regarding safety.
- **Least Privilege Execution**: The `trader_agent` should execute trades using an Alpaca API key that is scoped *only* to the authenticated user's sub-account, with hard API-level limits on maximum trade sizes that physically cannot be overridden by LLM output.
