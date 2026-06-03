from langchain_core.tools import tool
import yfinance as yf
from typing import Dict, Any

@tool
def get_stock_price(ticker: str) -> str:
    """Get the latest stock price and basic information for a given ticker."""
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        
        current_price = info.get('currentPrice') or info.get('regularMarketPrice')
        previous_close = info.get('regularMarketPreviousClose')
        
        if current_price is None:
            return f"Could not fetch price for {ticker.upper()}. Please check the ticker symbol."
        
        change = current_price - previous_close if previous_close else 0
        change_percent = (change / previous_close * 100) if previous_close else 0
        
        return f"""
Ticker: {ticker.upper()}
Current Price: ${current_price:,.2f}
Previous Close: ${previous_close:,.2f if previous_close else 'N/A'}
Change: ${change:,.2f} ({change_percent:+.2f}%)
        """.strip()
        
    except Exception as e:
        return f"Error fetching data for {ticker}: {str(e)}"


@tool
def get_company_info(ticker: str) -> str:
    """Get basic company information like name, sector, and summary."""
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info
        return f"""
Company: {info.get('longName', 'N/A')}
Sector: {info.get('sector', 'N/A')}
Industry: {info.get('industry', 'N/A')}
Market Cap: ${info.get('marketCap', 0):,}
Summary: {info.get('longBusinessSummary', 'No summary available')[:300]}...
        """.strip()
    except Exception as e:
        return f"Error getting info for {ticker}: {str(e)}"


def get_finance_tools():
    """Return list of available finance tools."""
    return [get_stock_price, get_company_info]