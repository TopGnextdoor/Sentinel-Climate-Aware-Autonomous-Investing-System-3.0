import yfinance as yf
from mcp.server.fastmcp import FastMCP
import requests

mcp = FastMCP("sentinel-market-mcp")

@mcp.tool()
def get_stock_price(ticker: str) -> dict:
    """Get the current stock price, volume, and market cap for a ticker."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        return {
            "current_price": info.get("currentPrice", info.get("regularMarketPrice")),
            "volume": info.get("volume"),
            "market_cap": info.get("marketCap")
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def get_market_trends(sector: str) -> dict:
    """Get trend data for the last 30 days for a given sector. 
    Maps sectors to common ETFs (e.g., tech -> XLK)."""
    sector_etf_map = {
        "technology": "XLK",
        "energy": "XLE",
        "renewables": "ICLN",
        "healthcare": "XLV",
        "finance": "XLF",
    }
    etf_ticker = sector_etf_map.get(sector.lower(), "SPY") # fallback to SP500
    try:
        stock = yf.Ticker(etf_ticker)
        hist = stock.history(period="1mo")
        
        if hist.empty:
            return {"error": "No data found"}
            
        start_price = float(hist['Close'].iloc[0])
        end_price = float(hist['Close'].iloc[-1])
        percent_change = ((end_price - start_price) / start_price) * 100
        
        return {
            "sector": sector,
            "proxy_etf": etf_ticker,
            "start_price": round(start_price, 2),
            "end_price": round(end_price, 2),
            "percent_change_30d": round(percent_change, 2),
            "trend": "up" if percent_change > 0 else "down"
        }
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def search_stocks(query: str) -> list:
    """Search for stocks matching a query string."""
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            quotes = response.json().get("quotes", [])
            results = []
            for q in quotes:
                if q.get("quoteType") == "EQUITY":
                    results.append({
                        "ticker": q.get("symbol"),
                        "name": q.get("shortname"),
                        "exchange": q.get("exchange")
                    })
            return results[:5]
    except Exception as e:
        return [{"error": str(e)}]
    return []

if __name__ == "__main__":
    mcp.run(transport="stdio")
