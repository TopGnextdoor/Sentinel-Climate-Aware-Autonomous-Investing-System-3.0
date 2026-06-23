from mcp.server.fastmcp import FastMCP

mcp = FastMCP("sentinel-esg-mcp")

@mcp.tool()
def get_esg_score(ticker: str) -> dict:
    """Get the ESG score and risk breakdown for a ticker."""
    ticker_upper = ticker.upper()
    
    # Mock data for demonstration purposes
    esg_data = {
        "AAPL": {"esg_score": 75.5, "environmental_risk": "low", "social_risk": "medium", "governance_risk": "low", "climate_exposure": "low"},
        "TSLA": {"esg_score": 60.0, "environmental_risk": "medium", "social_risk": "high", "governance_risk": "high", "climate_exposure": "low"},
        "XOM": {"esg_score": 25.0, "environmental_risk": "high", "social_risk": "medium", "governance_risk": "medium", "climate_exposure": "high"},
        "NEE": {"esg_score": 85.0, "environmental_risk": "low", "social_risk": "low", "governance_risk": "low", "climate_exposure": "positive_impact"},
    }
    
    return esg_data.get(ticker_upper, {
        "esg_score": 50.0, 
        "environmental_risk": "unknown", 
        "social_risk": "unknown", 
        "governance_risk": "unknown", 
        "climate_exposure": "unknown"
    })

@mcp.tool()
def get_carbon_footprint(ticker: str) -> dict:
    """Get the carbon footprint metrics for a ticker."""
    ticker_upper = ticker.upper()
    footprints = {
        "AAPL": {"scope_1_2_emissions_mt": 300000, "carbon_intensity": 15.2, "net_zero_target_year": 2030},
        "TSLA": {"scope_1_2_emissions_mt": 2500000, "carbon_intensity": 45.0, "net_zero_target_year": 2050},
        "XOM": {"scope_1_2_emissions_mt": 110000000, "carbon_intensity": 850.5, "net_zero_target_year": 2050},
        "NEE": {"scope_1_2_emissions_mt": 40000000, "carbon_intensity": 250.0, "net_zero_target_year": 2045},
    }
    
    return footprints.get(ticker_upper, {
        "scope_1_2_emissions_mt": None, 
        "carbon_intensity": None, 
        "net_zero_target_year": None
    })

@mcp.tool()
def list_green_sectors() -> list[str]:
    """List sectors considered low-risk for climate exposure."""
    return ["renewable_energy", "technology", "healthcare", "education", "water_utilities"]

if __name__ == "__main__":
    mcp.run(transport="stdio")
