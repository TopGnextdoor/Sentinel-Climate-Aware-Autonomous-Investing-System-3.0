# Sentinel ESG MCP Server

**Purpose**: This Model Context Protocol (MCP) server provides ESG (Environmental, Social, Governance) scores, carbon footprints, and green sector classifications for Sentinel's climate-aware investing agents.

## Implementation Details
The server currently uses **mock data** to satisfy the tool schemas required by the autonomous agents (`climate_agent`). 

## Future Enhancements
When deploying to production, these tools should be wired into real ESG API providers:
- **MSCI ESG Ratings API**: For `get_esg_score`.
- **Sustainalytics API**: For `get_carbon_footprint`.
