#!/usr/bin/env python3
"""
Phase 2 Core Analytics Tester
Test portfolio performance calculations, price alerts, and technical analysis
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api_clients.alpha_vantage import AlphaVantageClient
from api_clients.finnhub import FinnhubClient
from analyzers.portfolio_analyzer import PortfolioAnalyzer
from analyzers.technical_analyzer import TechnicalAnalyzer
from utils.config_loader import ConfigLoader

def test_portfolio_analysis():
    """Test real-time portfolio performance analysis"""
    print("📊 Portfolio Performance Analysis")
    print("=" * 50)
    
    try:
        # Initialize clients
        config = ConfigLoader()
        av_client = AlphaVantageClient()
        fh_client = FinnhubClient()
        
        # Load portfolio
        portfolio = config.load_portfolio()
        analyzer = PortfolioAnalyzer(av_client, fh_client)
        
        print("🔄 Fetching current market prices...")
        analysis = analyzer.get_current_portfolio_value(portfolio)
        
        # Display results
        print(f"\n💰 Portfolio Summary:")
        print(f"   Total Invested: ${analysis['total_invested']:.2f}")
        print(f"   Current Value: ${analysis['current_value']:.2f}")
        print(f"   Available Cash: ${analysis['cash']:.2f}")
        print(f"   Total Portfolio: ${analysis['current_value'] + analysis['cash']:.2f}")
        
        gain_loss = analysis['total_gain_loss']
        gain_pct = analysis['total_gain_loss_pct']
        indicator = "🟢" if gain_loss >= 0 else "🔴"
        sign = "+" if gain_loss >= 0 else ""
        
        print(f"{indicator} Total Gain/Loss: {sign}${gain_loss:.2f} ({sign}{gain_pct:.1f}%)")
        
        # Show individual stocks
        print(f"\n📈 Individual Holdings:")
        for symbol, stock in analysis['stocks'].items():
            stock_gain = stock['gain_loss']
            stock_pct = stock['gain_loss_pct']
            stock_indicator = "🟢" if stock_gain >= 0 else "🔴"
            stock_sign = "+" if stock_gain >= 0 else ""
            
            print(f"{stock_indicator} {symbol}: ${stock['current_price']:.2f} "
                  f"({stock_sign}${stock_gain:.2f}, {stock_sign}{stock_pct:.1f}%)")
        
        # Check for price alerts
        if analysis['alerts']:
            print(f"\n🚨 Price Alerts ({len(analysis['alerts'])}):")
            for alert in analysis['alerts']:
                alert_type = "📈" if alert['type'] == 'gain' else "📉"
                print(f"{alert_type} {alert['symbol']}: {alert['change_pct']:+.1f}% "
                      f"(>${alert['current_price']:.2f})")
        else:
            print(f"\n✅ No significant price movements (>5%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Portfolio analysis failed: {e}")
        return False

def test_technical_analysis():
    """Test technical analysis for portfolio stocks"""
    print("\n🔍 Technical Analysis")
    print("=" * 30)
    
    try:
        # Initialize
        config = ConfigLoader()
        av_client = AlphaVantageClient()
        tech_analyzer = TechnicalAnalyzer(av_client)
        
        # Load portfolio
        portfolio = config.load_portfolio()
        symbols = list(portfolio.get('stocks', {}).keys())
        
        if not symbols:
            print("❌ No stocks in portfolio")
            return False
        
        # Test with first stock (avoid rate limits)
        test_symbol = symbols[0]
        print(f"🧪 Testing technical analysis for {test_symbol}...")
        
        # Get comprehensive analysis
        analysis = tech_analyzer.get_comprehensive_analysis(test_symbol)
        
        if analysis['rsi']:
            rsi_data = analysis['rsi']
            print(f"\n📊 RSI Analysis:")
            print(f"   Current RSI: {rsi_data['current_rsi']:.1f}")
            print(f"   Signal: {rsi_data['signal']['action'].upper()} ({rsi_data['signal']['strength']})")
            print(f"   Reason: {rsi_data['signal']['reason']}")
        
        if analysis['macd']:
            macd_data = analysis['macd']
            print(f"\n📈 MACD Analysis:")
            print(f"   MACD Line: {macd_data['macd_line']:.4f}")
            print(f"   Signal Line: {macd_data['signal_line']:.4f}")
            print(f"   Signal: {macd_data['signal']['action'].upper()}")
            print(f"   Reason: {macd_data['signal']['reason']}")
        
        if analysis['sma']:
            sma_data = analysis['sma']
            print(f"\n📉 SMA Analysis:")
            print(f"   20-day SMA: ${sma_data['short_sma']:.2f}")
            print(f"   50-day SMA: ${sma_data['long_sma']:.2f}")
            print(f"   Signal: {sma_data['signal']['action'].upper()} ({sma_data['signal']['strength']})")
            print(f"   Reason: {sma_data['signal']['reason']}")
        
        # Overall recommendation
        overall = analysis['overall_signal']
        print(f"\n🎯 Overall Recommendation:")
        print(f"   Action: {overall['action'].upper()} ({overall['strength']})")
        print(f"   Reason: {overall['reason']}")
        print(f"   Confidence: {overall['confidence']:.1%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Technical analysis failed: {e}")
        return False

def test_benchmark_comparison():
    """Test benchmark comparison"""
    print("\n📊 Benchmark Comparison")
    print("=" * 25)
    
    try:
        # Initialize
        config = ConfigLoader()
        av_client = AlphaVantageClient()
        fh_client = FinnhubClient()
        analyzer = PortfolioAnalyzer(av_client, fh_client)
        
        # Load portfolio
        portfolio = config.load_portfolio()
        benchmark_symbol = portfolio.get('settings', {}).get('benchmark', 'VOO')
        
        print(f"🔄 Comparing portfolio vs {benchmark_symbol}...")
        comparison = analyzer.compare_to_benchmark(portfolio, benchmark_symbol)
        
        portfolio_return = comparison['portfolio_return_pct']
        benchmark_return = comparison['benchmark_change_pct']
        outperforming = comparison['outperforming']
        performance_diff = comparison['performance_difference']
        
        print(f"\n📈 Performance Comparison:")
        print(f"   Portfolio Return: {portfolio_return:+.1f}%")
        print(f"   {benchmark_symbol} Return: {benchmark_return:+.1f}%")
        print(f"   Difference: {performance_diff:+.1f}%")
        
        if outperforming:
            print(f"🎉 Portfolio is OUTPERFORMING {benchmark_symbol}!")
        else:
            print(f"📉 Portfolio is underperforming {benchmark_symbol}")
        
        return True
        
    except Exception as e:
        print(f"❌ Benchmark comparison failed: {e}")
        return False

def test_price_alerts():
    """Test price movement detection"""
    print("\n🚨 Price Alert Testing")
    print("=" * 25)
    
    try:
        # Initialize
        config = ConfigLoader()
        av_client = AlphaVantageClient()
        fh_client = FinnhubClient()
        analyzer = PortfolioAnalyzer(av_client, fh_client)
        
        # Load portfolio
        portfolio = config.load_portfolio()
        
        print("🔄 Checking for significant price movements...")
        alerts = analyzer.detect_price_alerts(portfolio)
        
        if alerts:
            print(f"\n🚨 Found {len(alerts)} price alerts:")
            for alert in alerts:
                severity_icon = "🔥" if alert['severity'] == 'high' else "⚠️"
                change_sign = "+" if alert['change_pct'] > 0 else ""
                
                print(f"{severity_icon} {alert['symbol']}: {change_sign}{alert['change_pct']:.1f}% "
                      f"(${alert['current_price']:.2f})")
                print(f"   Position Value: ${alert['position_value']:.2f}")
        else:
            print("✅ No significant price movements detected (threshold: 5%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Price alert testing failed: {e}")
        return False

def main():
    """Run all Phase 2 tests"""
    print("🧪 Phase 2 Core Analytics Tester")
    print("=" * 50)
    
    tests = [
        ("Portfolio Performance Analysis", test_portfolio_analysis),
        ("Technical Analysis", test_technical_analysis),
        ("Benchmark Comparison", test_benchmark_comparison),
        ("Price Alert Detection", test_price_alerts)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 Phase 2 Test Summary")
    print("=" * 30)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All Phase 2 analytics are working!")
        print("📈 Ready for daily tracking and Telegram integration")
    elif passed > 0:
        print("⚠️ Some analytics working. Check API rate limits.")
    else:
        print("❌ Phase 2 analytics failed. Check API connections.")

if __name__ == "__main__":
    main()