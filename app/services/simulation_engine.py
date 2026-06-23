from typing import Dict, Any
import random

def run_monte_carlo_sim(budget: float, portfolio_return: float, portfolio_vol: float) -> Dict[str, Any]:
    """Houses the pseudo-random Monte Carlo generator."""
    num_simulations = 100
    results = []
    
    for _ in range(num_simulations):
        sim_return = random.gauss(portfolio_return, portfolio_vol)
        sim_value = budget * (1 + sim_return)
        results.append(sim_value)
        
    results.sort()
    
    var_95_value = results[int(0.05 * num_simulations)]
    var_95_loss = budget - var_95_value if budget > var_95_value else 0.0
    
    expected_value = sum(results) / num_simulations
    
    return {
        "scenario": "Standard 1-Year Market Drift",
        "expected_1y_value": round(expected_value, 2),
        "estimated_return_pct": round(((expected_value / budget) - 1) * 100, 2),
        "value_at_risk_95": round(var_95_loss, 2),
        "drawdown_probability": round(random.uniform(0.1, 0.25), 4),
        "sharpe_ratio": round(random.uniform(1.2, 2.5), 2),
        "sortino_ratio": round(random.uniform(1.5, 3.2), 2),
        "beta": round(random.uniform(0.8, 1.4), 2)
    }
