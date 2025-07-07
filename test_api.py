#!/usr/bin/env python3
"""
API Connection Tester
Test all API clients to ensure they're working properly
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api_clients.alpha_vantage import AlphaVantageClient
from api_clients.finnhub import FinnhubClient
from api_clients.marketaux import MarketAuxClient
from utils.config_loader import ConfigLoader

def test_all_apis():
    """Test all API connections"""
    print("🧪 API Connection Tester")
    print("=" * 50)
    
    config = ConfigLoader()
    
    # Test results
    results = {
        'alpha_vantage': False,
        'finnhub': False,
        'marketaux': False
    }
    
    # Test Alpha Vantage
    print("\n1. Alpha Vantage API")
    print("-" * 20)
    try:
        alpha_key = config.get_env('ALPHA_VANTAGE_API_KEY')
        if not alpha_key:
            print("❌ ALPHA_VANTAGE_API_KEY not found in .env")
        else:
            av_client = AlphaVantageClient(alpha_key)
            results['alpha_vantage'] = av_client.test_connection()
    except Exception as e:
        print(f"❌ Alpha Vantage error: {e}")
    
    # Test Finnhub
    print("\n2. Finnhub API")
    print("-" * 15)
    try:
        finnhub_key = config.get_env('FINNHUB_API_KEY')
        if not finnhub_key:
            print("❌ FINNHUB_API_KEY not found in .env")
        else:
            fh_client = FinnhubClient(finnhub_key)
            results['finnhub'] = fh_client.test_connection()
    except Exception as e:
        print(f"❌ Finnhub error: {e}")
    
    # Test MarketAux
    print("\n3. MarketAux API")
    print("-" * 17)
    try:
        marketaux_key = config.get_env('MARKETAUX_API_KEY')
        if not marketaux_key:
            print("❌ MARKETAUX_API_KEY not found in .env")
        else:
            ma_client = MarketAuxClient(marketaux_key)
            results['marketaux'] = ma_client.test_connection()
    except Exception as e:
        print(f"❌ MarketAux error: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 API Test Summary")
    print("=" * 50)
    
    working_apis = sum(results.values())
    total_apis = len(results)
    
    for api_name, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {api_name.replace('_', ' ').title()}: {'Working' if status else 'Failed'}")
    
    print(f"\n📈 APIs Working: {working_apis}/{total_apis}")
    
    if working_apis == total_apis:
        print("🎉 All APIs are working perfectly!")
    elif working_apis > 0:
        print("⚠️ Some APIs are working. You can proceed with limited functionality.")
    else:
        print("❌ No APIs are working. Please check your .env file and API keys.")
    
    return results

def demo_portfolio_data():
    """Demo fetching data for your actual portfolio"""
    print("\n🔍 Portfolio Data Demo")
    print("=" * 30)
    
    config = ConfigLoader()
    portfolio = config.load_portfolio()
    symbols = list(portfolio.get('stocks', {}).keys())
    
    if not symbols:
        print("❌ No stocks found in portfolio.json")
        return
    
    print(f"📊 Testing data fetch for: {', '.join(symbols)}")
    
    # Test Alpha Vantage for one symbol
    try:
        av_client = AlphaVantageClient()
        symbol = symbols[0]  # Test first symbol
        print(f"\n📈 Getting {symbol} quote from Alpha Vantage...")
        quote = av_client.get_quote(symbol)
        if quote:
            print(f"   Price: ${quote['price']:.2f}")
            print(f"   Change: {quote['change']:.2f} ({quote['change_percent']}%)")
        else:
            print("   ❌ Failed to get quote")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test Finnhub for company news
    try:
        fh_client = FinnhubClient()
        print(f"\n📰 Getting {symbol} news from Finnhub...")
        news = fh_client.get_company_news(symbol, days_back=3)
        if news:
            print(f"   Found {len(news)} news articles")
            if news:
                print(f"   Latest: {news[0]['headline'][:60]}...")
        else:
            print("   ❌ Failed to get news")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    # Test API connections
    test_all_apis()
    
    # Demo portfolio data fetching
    demo_portfolio_data()
    
    print("\n👋 API testing complete!")
    print("💡 Tip: Set up all three API keys for full functionality")