#!/usr/bin/env python3
"""
Test the integrated portfolio manager with live analytics
Quick test of the new real-time functionality
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.config_loader import ConfigLoader
from api_clients.alpha_vantage import AlphaVantageClient
from api_clients.finnhub import FinnhubClient
from analyzers.portfolio_analyzer import PortfolioAnalyzer

def quick_portfolio_test():
    """Quick test of live portfolio functionality"""
    print("🧪 Testing Integrated Portfolio with Live Analytics")
    print("=" * 60)
    
    try:
        # Initialize
        config = ConfigLoader()
        portfolio = config.load_portfolio()
        
        print("✅ Portfolio loaded")
        print(f"📊 Found {len(portfolio.get('stocks', {}))} stocks")
        
        # Test API connections
        print("\n🔌 Testing API connections...")
        av_client = AlphaVantageClient()
        fh_client = FinnhubClient()
        analyzer = PortfolioAnalyzer(av_client, fh_client)
        
        print("✅ APIs connected")
        
        # Test real-time analysis
        print("\n📈 Testing real-time portfolio analysis...")
        analysis = analyzer.get_current_portfolio_value(portfolio)
        
        print(f"✅ Analysis complete!")
        print(f"💰 Total Portfolio Value: ${analysis['current_value'] + analysis['cash']:.2f}")
        print(f"📊 Total Gain/Loss: {analysis['total_gain_loss']:+.2f} ({analysis['total_gain_loss_pct']:+.1f}%)")
        
        if analysis.get('alerts'):
            print(f"🚨 Price Alerts: {len(analysis['alerts'])}")
        else:
            print("✅ No price alerts")
        
        # Test individual stock data
        print(f"\n📈 Individual Stock Performance:")
        for symbol, stock in analysis['stocks'].items():
            gain_pct = stock['gain_loss_pct']
            indicator = "🟢" if gain_pct >= 0 else "🔴"
            print(f"{indicator} {symbol}: {gain_pct:+.1f}% (${stock['current_price']:.2f})")
        
        print(f"\n🎉 Integration Test PASSED!")
        print(f"💡 You can now run: python portfolio_manager.py")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        print(f"💡 Check your API keys in .env.local")
        return False

def demo_live_vs_static():
    """Show difference between live and static data"""
    print("\n🔍 Live vs Static Data Comparison")
    print("=" * 40)
    
    try:
        config = ConfigLoader()
        portfolio = config.load_portfolio()
        
        # Show static data from JSON
        print("📄 Static Data (from portfolio.json):")
        stocks = portfolio.get('stocks', {})
        for symbol, data in stocks.items():
            static_price = data.get('current_price', data['avg_price'])
            print(f"   {symbol}: ${static_price:.2f} (static)")
        
        # Show live data from APIs
        print("\n📡 Live Data (from market APIs):")
        av_client = AlphaVantageClient()
        fh_client = FinnhubClient()
        analyzer = PortfolioAnalyzer(av_client, fh_client)
        
        for symbol in stocks.keys():
            live_price = analyzer._get_current_price(symbol)
            if live_price:
                static_price = stocks[symbol].get('current_price', stocks[symbol]['avg_price'])
                difference = live_price - static_price
                print(f"   {symbol}: ${live_price:.2f} (live) - diff: {difference:+.2f}")
            else:
                print(f"   {symbol}: Price unavailable")
        
        return True
        
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        return False

def main():
    """Run integration tests"""
    print("🚀 Portfolio Integration Tester")
    print("=" * 40)
    
    # Quick functionality test
    success = quick_portfolio_test()
    
    if success:
        # Demo live vs static data
        demo_live_vs_static()
        
        print(f"\n{'='*60}")
        print("🎯 INTEGRATION COMPLETE!")
        print("=" * 60)
        print("✅ Your portfolio manager now has live analytics:")
        print("   📊 Real-time prices and performance")
        print("   🚨 Price movement alerts")
        print("   📈 Live gain/loss calculations")
        print("   🔍 Detailed portfolio analysis")
        print(f"\n🚀 Run the full portfolio manager:")
        print("   python portfolio_manager.py")
        print(f"\n💡 Menu Options Available:")
        print("   1. Show Portfolio (with live data)")
        print("   2. Detailed Live Analysis")
        print("   3. Check Price Alerts")
        print("   4. Refresh Portfolio Data")
    else:
        print(f"\n❌ Integration failed - check API setup")

if __name__ == "__main__":
    main()