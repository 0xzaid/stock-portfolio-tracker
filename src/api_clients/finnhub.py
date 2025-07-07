import requests
import time
from typing import Dict, Optional, Any, List
import os
from datetime import datetime, timedelta

class FinnhubClient:
    """
    Finnhub API client for market data and news
    Free tier: 60 calls per minute
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('FINNHUB_API_KEY')
        self.base_url = "https://finnhub.io/api/v1"
        self.last_request_time = 0
        self.min_request_interval = 1  # 60 per minute = 1 second between requests
        
        if not self.api_key:
            raise ValueError("Finnhub API key not found. Set FINNHUB_API_KEY in .env")
    
    def _make_request(self, endpoint: str, params: Dict[str, str] = None) -> Optional[Dict[str, Any]]:
        """Make rate-limited API request"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        if params is None:
            params = {}
        params['token'] = self.api_key
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            self.last_request_time = time.time()
            
            data = response.json()
            
            # Check for API errors
            if isinstance(data, dict) and 'error' in data:
                print(f"❌ Finnhub Error: {data['error']}")
                return None
                
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Finnhub request failed: {e}")
            return None
        except ValueError as e:
            print(f"❌ Finnhub JSON decode error: {e}")
            return None
    
    def get_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get real-time quote for a symbol"""
        data = self._make_request('quote', {'symbol': symbol})
        if data and 'c' in data:
            return {
                'symbol': symbol,
                'price': data['c'],  # Current price
                'change': data['d'],  # Change
                'change_percent': data['dp'],  # Change percent
                'high': data['h'],  # High price of the day
                'low': data['l'],  # Low price of the day
                'open': data['o'],  # Open price of the day
                'previous_close': data['pc'],  # Previous close price
                'timestamp': data['t']  # Timestamp
            }
        return None
    
    def get_company_news(self, symbol: str, days_back: int = 7) -> Optional[List[Dict[str, Any]]]:
        """Get company news for the last N days"""
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)
        
        params = {
            'symbol': symbol,
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d')
        }
        
        data = self._make_request('company-news', params)
        if data and isinstance(data, list):
            # Format news items
            formatted_news = []
            for item in data[:20]:  # Limit to 20 items
                formatted_news.append({
                    'headline': item.get('headline'),
                    'summary': item.get('summary'),
                    'url': item.get('url'),
                    'source': item.get('source'),
                    'datetime': datetime.fromtimestamp(item.get('datetime', 0)),
                    'sentiment': None  # Finnhub doesn't provide sentiment directly
                })
            return formatted_news
        return None
    
    def get_general_news(self, category: str = 'general', limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """
        Get general market news
        Categories: general, forex, crypto, merger
        """
        params = {
            'category': category,
            'minId': 0
        }
        
        data = self._make_request('news', params)
        if data and isinstance(data, list):
            return data[:limit]
        return None
    
    def get_company_profile(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get company profile information"""
        data = self._make_request('stock/profile2', {'symbol': symbol})
        if data and 'name' in data:
            return {
                'name': data.get('name'),
                'ticker': data.get('ticker'),
                'exchange': data.get('exchange'),
                'industry': data.get('finnhubIndustry'),
                'sector': data.get('gsubind'),
                'country': data.get('country'),
                'currency': data.get('currency'),
                'market_cap': data.get('marketCapitalization'),
                'website': data.get('weburl'),
                'logo': data.get('logo')
            }
        return None
    
    def get_basic_financials(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get basic financial metrics"""
        data = self._make_request('stock/metric', {'symbol': symbol, 'metric': 'all'})
        if data and 'metric' in data:
            metrics = data['metric']
            return {
                'pe_ratio': metrics.get('peBasicExclExtraTTM'),
                'price_to_book': metrics.get('pbAnnual'),
                'roe': metrics.get('roeRfy'),
                'roa': metrics.get('roaRfy'),
                'debt_to_equity': metrics.get('totalDebt/totalEquityAnnual'),
                'current_ratio': metrics.get('currentRatioAnnual'),
                'gross_margin': metrics.get('grossMarginTTM'),
                'net_margin': metrics.get('netProfitMarginTTM')
            }
        return None
    
    def get_recommendation_trends(self, symbol: str) -> Optional[List[Dict[str, Any]]]:
        """Get analyst recommendation trends"""
        data = self._make_request('stock/recommendation', {'symbol': symbol})
        if data and isinstance(data, list):
            return data
        return None
    
    def test_connection(self) -> bool:
        """Test API connection with a simple quote request"""
        print("🧪 Testing Finnhub connection...")
        
        result = self.get_quote('AAPL')
        if result:
            print(f"✅ Finnhub connected - AAPL: ${result['price']:.2f}")
            return True
        else:
            print("❌ Finnhub connection failed")
            return False