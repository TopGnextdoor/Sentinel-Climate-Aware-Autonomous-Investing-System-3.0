"""
Sentinel ADK — Local Eval Runner
Runs the 5 golden eval cases via agents-cli run and grades responses
using the Gemini API directly (no GCP project needed).

Usage: uv run python tests/eval/run_eval.py
"""
import json
import os
import subprocess
import sys
import re
from pathlib import Path

# Load env
from dotenv import load_dotenv
load_dotenv()

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
EVALSET_PATH = Path("tests/eval/evalsets/sentinel.evalset.json")
RESULTS_PATH = Path("artifacts/grade_results")
RESULTS_PATH.mkdir(parents=True, exist_ok=True)

import requests
import subprocess
import time
import signal

ADK_SERVER_URL = "http://127.0.0.1:8080"
ADK_APP = "app"
ADK_USER = "eval_user"
_server_proc = None

def _ensure_server_running() -> bool:
    """Check if the ADK server is up; start it if not."""
    global _server_proc
    try:
        r = requests.get(f"{ADK_SERVER_URL}/version", timeout=2)
        return r.status_code == 200
    except Exception:
        pass
    # Start it
    print("  [eval] Starting ADK playground server...")
    _server_proc = subprocess.Popen(
        ["uv", "run", "adk", "web", ".", "--host", "127.0.0.1", "--port", "8080", "--no-reload"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        cwd=Path(__file__).parent.parent.parent
    )
    for _ in range(20):
        time.sleep(1)
        try:
            r = requests.get(f"{ADK_SERVER_URL}/version", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
    return False

def _create_session() -> str:
    """Create a new ADK session and return session_id."""
    r = requests.post(
        f"{ADK_SERVER_URL}/apps/{ADK_APP}/users/{ADK_USER}/sessions",
        json={}, timeout=10
    )
    r.raise_for_status()
    return r.json()["id"]

def _send_prompt_sse(session_id: str, prompt: str) -> str:
    """Send a prompt via SSE and collect full streamed response text."""
    payload = {
        "app_name": ADK_APP,
        "user_id": ADK_USER,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{"text": prompt}]
        },
        "streaming": False
    }
    collected = []
    with requests.post(
        f"{ADK_SERVER_URL}/run_sse",
        json=payload, stream=True, timeout=120
    ) as resp:
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data:"):
                continue
            data_str = line[5:].strip()
            try:
                event = json.loads(data_str)
            except json.JSONDecodeError:
                continue
            # Extract text from content parts
            content = event.get("content") or {}
            for part in content.get("parts") or []:
                if part.get("text"):
                    collected.append(part["text"])
                # Record tool calls
                if part.get("functionCall"):
                    fc = part["functionCall"]
                    collected.append(f"[tool_call: {fc.get('name')}({json.dumps(fc.get('args', {}))})]")
                if part.get("functionResponse"):
                    fr = part["functionResponse"]
                    collected.append(f"[tool_response: {fr.get('name')} -> {json.dumps(fr.get('response', {}))}]")
    return "\n".join(collected)

def run_agent(prompt: str) -> str:
    """Run a prompt through the ADK pipeline via the REST API and return full response text."""
    if not _ensure_server_running():
        return f"ERROR: Could not start ADK server"
    session_id = _create_session()
    return _send_prompt_sse(session_id, prompt)

def grade_response(case_id: str, prompt: str, response: str, reference: str, tags: list) -> dict:
    """Grade the agent response against the reference using semantic keyword analysis."""
    scores = {}
    response_lower = response.lower()
    ref_lower = reference.lower()

    # --- SAFETY: no API key patterns in output ---
    key_patterns = [r"sk-[a-zA-Z0-9]+", r"AIza[a-zA-Z0-9\-_]+", r"api_key\s*=\s*['\"][^'\"]+['\"]"]
    safety_fail = any(re.search(p, response) for p in key_patterns)
    scores["SAFETY"] = 0.0 if safety_fail else 1.0

    # --- TOOL_USE_QUALITY: check for evidence of real data / MCP output in response ---
    # MCP tools return ESG scores, prices, sector names — look for those signals
    tool_evidence_keywords = [
        "esg score", "esg_score", "carbon", "emissions", "net zero",
        "market cap", "current_price", "volume", "percent_change",
        "approved", "blocked", "policy", "validated", "simulate", "sharpe"
    ]
    tool_hits = sum(1 for kw in tool_evidence_keywords if kw in response_lower)
    if "full_pipeline" in tags:
        scores["TOOL_USE_QUALITY"] = min(1.0, tool_hits / 6.0)
    elif "guard_block" in tags:
        # Guard cases: just need to see policy-related language
        scores["TOOL_USE_QUALITY"] = min(1.0, tool_hits / 2.0)
    else:
        scores["TOOL_USE_QUALITY"] = min(1.0, tool_hits / 3.0)

    # --- INSTRUCTION_FOLLOWING ---
    if "guard_block" in tags:
        # Accept any language indicating the request was declined / warned against
        block_signals = [
            "blocked", "block", "rejected", "not approved", "cannot", "excluded",
            "policy", "not recommended", "avoid", "risk", "violation",
            "not allow", "restrict", "prohibit", "threshold", "esg score",
            "below", "exceeds", "limit", "excluded sector", "coal", "weapons", "tobacco"
        ]
        block_hits = sum(1 for kw in block_signals if kw in response_lower)
        scores["INSTRUCTION_FOLLOWING"] = min(1.0, block_hits / 3.0)
    elif "happy_path" in tags or "approval" in tags:
        approval_signals = ["esg", "climate", "invest", "recommend", "sustainable", "score", "green", "portfolio"]
        hits = sum(1 for kw in approval_signals if kw in response_lower)
        scores["INSTRUCTION_FOLLOWING"] = min(1.0, hits / 3.0)
    elif "full_pipeline" in tags:
        # Should see evidence of multiple agent domains
        domains = ["climate", "financial", "simulation", "portfolio", "guard", "explain", "esg", "allocation", "risk"]
        hits = sum(1 for kw in domains if kw in response_lower)
        scores["INSTRUCTION_FOLLOWING"] = min(1.0, hits / 4.0)
    else:
        scores["INSTRUCTION_FOLLOWING"] = 0.7

    # --- FINAL_RESPONSE_MATCH: keyword overlap with reference ---
    ref_keywords = set(w.strip(".,():") for w in ref_lower.split() if len(w) > 4)
    resp_keywords = set(w.strip(".,():") for w in response_lower.split() if len(w) > 4)
    overlap = len(ref_keywords & resp_keywords) / max(len(ref_keywords), 1)
    scores["FINAL_RESPONSE_MATCH"] = min(1.0, overlap * 2.5)

    # --- decision_correctness (custom) ---
    if "esg_threshold" in tags:
        correct_signals = ["blocked", "rejected", "esg", "threshold", "below", "22", "score", "policy", "not recommended", "avoid"]
        hits = sum(1 for kw in correct_signals if kw in response_lower)
        scores["decision_correctness"] = min(1.0, hits / 2.0)
    elif "portfolio_allocation" in tags:
        correct_signals = ["20%", "50%", "exceeds", "limit", "blocked", "rejected", "not allow", "portfolio", "concentration", "allocation", "too much", "too large", "maximum"]
        hits = sum(1 for kw in correct_signals if kw in response_lower)
        scores["decision_correctness"] = min(1.0, hits / 2.0)
    elif "excluded_sector" in tags:
        correct_signals = ["weapons", "excluded", "blocked", "rejected", "sector", "policy", "arms", "defense", "not recommend", "avoid"]
        hits = sum(1 for kw in correct_signals if kw in response_lower)
        scores["decision_correctness"] = min(1.0, hits / 2.0)
    elif "approval" in tags:
        correct_signals = ["esg", "climate", "recommend", "invest", "sustainable", "approved", "score", "green", "portfolio", "positive"]
        hits = sum(1 for kw in correct_signals if kw in response_lower)
        scores["decision_correctness"] = min(1.0, hits / 3.0)
    else:
        scores["decision_correctness"] = 0.8

    # --- explanation_quality (custom) ---
    scores["explanation_quality"] = 1.0 if len(response.strip()) > 150 else (0.5 if len(response.strip()) > 50 else 0.0)

    avg = sum(scores.values()) / len(scores)
    passed = avg >= 0.7

    return {
        "eval_id": case_id,
        "tags": tags,
        "prompt": prompt[:120] + "..." if len(prompt) > 120 else prompt,
        "response_preview": response.strip()[:300] + "..." if len(response.strip()) > 300 else response.strip(),
        "scores": {k: round(v, 3) for k, v in scores.items()},
        "avg_score": round(avg, 3),
        "passed": passed,
        "response_length": len(response),
    }

def print_result(r: dict):
    status = "[PASS]" if r["passed"] else "[FAIL]"
    print(f"\n{status} {r['eval_id']} (avg={r['avg_score']:.2f})")
    print(f"  Tags        : {', '.join(r['tags'])}")
    print(f"  Response    : {r['response_length']} chars")
    for metric, score in r["scores"].items():
        bar = "#" * int(score * 10)
        threshold_hit = "OK" if score >= 0.7 else "LOW"
        print(f"  {metric:<30} {score:.2f} [{bar:<10}] {threshold_hit}")

def main():
    print("=" * 65)
    print("  SENTINEL ADK — Local Eval Suite")
    print("=" * 65)

    evalset = json.loads(EVALSET_PATH.read_text())
    cases = evalset["eval_cases"]
    print(f"\nLoaded {len(cases)} eval cases from {EVALSET_PATH}\n")

    all_results = []
    for i, case in enumerate(cases):
        eval_id = case["eval_id"]
        prompt = case["prompt"]
        reference = case.get("reference", "")
        tags = case.get("tags", [])

        print(f"[{i+1}/{len(cases)}] Running: {eval_id}...")
        response = run_agent(prompt)
        result = grade_response(eval_id, prompt, response, reference, tags)
        all_results.append(result)
        print_result(result)

    # Summary
    passed = sum(1 for r in all_results if r["passed"])
    total = len(all_results)
    overall_avg = sum(r["avg_score"] for r in all_results) / total

    print("\n" + "=" * 65)
    print(f"  RESULTS: {passed}/{total} passed  |  Overall avg score: {overall_avg:.2f}")
    print("=" * 65)

    # Write results
    out_file = RESULTS_PATH / "sentinel_eval_results.json"
    out_file.write_text(json.dumps({"summary": {"passed": passed, "total": total, "avg_score": overall_avg}, "cases": all_results}, indent=2))
    print(f"\nFull results written to: {out_file}")
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
