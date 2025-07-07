import requests
import time
from typing import Dict, Optional, Any
import os

class AlphaVantageClient:
    """
    Alpha Vantage API client for stock prices, technical indicators, and news
    Free tier: 25 requests per day, 5 per minute
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY')
        self.base_url = "https://www.alphavantage.co/query"
        self.last_request_time = 0
        self.min_request_interval = 12  # 5 per minute = 12 seconds between requests
        
        if not self.api_key:
            raise ValueError("Alpha Vantage API key not found. Set ALPHA_VANTAGE_API_KEY in .env")
    
    def _make_request(self, params: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Make rate-limited API request"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            print(f"⏳ Rate limiting: waiting {sleep_time:.1f}s...")
            time.sleep(sleep_time)
        
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            self.last_request_time = time.time()
            
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                print(f"❌ Alpha Vantage Error: {data['Error Message']}")
                return None
            
            if 'Note' in data:
                print(f"⚠️ Alpha Vantage Note: {data['Note']}")
                return None
                
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Alpha Vantage request failed: {e}")
            return None
        except ValueError as e:
            print(f"❌ Alpha Vantage JSON decode error: {e}")
            return None
    
    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote for a symbol"""
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol
        }
        
        data = self._make_request(params)
        if data and 'Global Quote' in data:
            quote = data['Global Quote']
            return {
                'symbol': quote.get('01. symbol'),
                'price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%').replace('%', ''),
                'volume': int(quote.get('06. volume', 0)),
                'latest_day': quote.get('07. latest trading day')
            }
        return None
    
    def get_daily_prices(self, symbol: str, outputsize: str = 'compact') -> Optional[Dict[str, Any]]:
        """Get daily historical prices (compact = last 100 days)"""
        params = {
            'function': 'TIME_SERIES_DAILY_ADJUSTED',
            'symbol': symbol,
            'outputsize': outputsize
        }
        
        data = self._make_request(params)
        if data and 'Time Series (Daily)' in data:
            return {
                'meta_data': data.get('Meta Data'),
                'time_series': data['Time Series (Daily)']
            }
        return None
    
    def get_company_news(self, symbol: str, limit: int = 50) -> Optional[list]:
        """Get news for a specific company"""
        params = {
            'function': 'NEWS_SENTIMENT',
            'tickers': symbol,
            'limit': str(limit)
        }
        
        data = self._make_request(params)
        if data and 'feed' in data:
            return data['feed']
        return None
    
    def get_technical_indicator(self, symbol: str, indicator: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Get technical indicator data
        Common indicators: RSI, MACD, SMA, EMA
        """
        params = {
            'function': indicator,
            'symbol': symbol,
            'interval': kwargs.get('interval', 'daily'),
            'time_period': str(kwargs.get('time_period', 14)),
            'series_type': kwargs.get('series_type', 'close')
        }
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in ['interval', 'time_period', 'series_type']:
                params[key] = str(value)
        
        return self._make_request(params)
    
    def test_connection(self) -> bool:
        """Test API connection with a simple quote request"""
        print("🧪 Testing Alpha Vantage connection...")
        
        result = self.get_quote('AAPL')
        if result:
            print(f"✅ Alpha Vantage connected - AAPL: ${result['price']:.2f}")
            return True
        else:
            print("❌ Alpha Vantage connection failed")
            return False