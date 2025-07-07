#!/usr/bin/env python3
"""
Phase 3 Recommendation Engine Tester
Test AI-powered recommendations combining technical analysis and news sentiment
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api_clients.alpha_vantage import AlphaVantageClient
from api_clients.finnhub import FinnhubClient
from api_clients.marketaux import MarketAuxClient
from analyzers.recommendation_engine import RecommendationEngine
from analyzers.sentiment_analyzer import SentimentAnalyzer
from utils.config_loader import ConfigLoader

def test_sentiment_analysis():
    """Test news sentiment analysis"""
    print("📰 Testing News Sentiment Analysis")
    print("=" * 40)
    
    try:
        # Initialize
        config = ConfigLoader()
        ma_client = MarketAuxClient()
        fh_client = FinnhubClient()
        sentiment_analyzer = SentimentAnalyzer(ma_client, fh_client)
        
        # Load portfolio
        portfolio = config.load_portfolio()
        symbols = list(portfolio.get('stocks', {}).keys())
        
        if not symbols:
            print("❌ No stocks in portfolio")
            return False
        
        print(f"🔄 Analyzing sentiment for: {', '.join(symbols)}")
        
        # Get portfolio sentiment
        sentiment_analysis = sentiment_analyzer.analyze_portfolio_sentiment(portfolio)
        
        # Display results
        portfolio_sentiment = sentiment_analysis['portfolio_sentiment']
        print(f"\n📊 Portfolio Sentiment: {portfolio_sentiment.get('label', 'neutral').title()}")
        print(f"   Score: {portfolio_sentiment.get('score', 0):.2f}")
        print(f"   Confidence: {portfolio_sentiment.get('confidence', 0):.1%}")
        
        # Individual stocks
        stock_sentiments = sentiment_analysis['stock_sentiments']
        print(f"\n📈 Individual Stock Sentiments:")
        for symbol, sentiment in stock_sentiments.items():
            label = sentiment.get('sentiment_label', 'neutral')
            score = sentiment.get('sentiment_score', 0)
            news_count = sentiment.get('news_count', 0)
            
            if label == 'positive':
                icon = "🟢"
            elif label == 'negative':
                icon = "🔴"
            else:
                icon = "🟡"
            
            print(f"{icon} {symbol}: {label.title()} (Score: {score:.2f}, {news_count} articles)")
        
        # Market sentiment
        market_sentiment = sentiment_analysis['market_sentiment']
        print(f"\n🌍 Market Sentiment: {market_sentiment.get('label', 'neutral').title()}")
        
        # News highlights
        highlights = sentiment_analysis.get('news_highlights', [])
        if highlights:
            print(f"\n📰 Top News Headlines:")
            for highlight in highlights[:3]:
                sentiment_icon = "🟢" if highlight['sentiment'] == 'positive' else "🔴"
                print(f"{sentiment_icon} {highlight['symbol']}: {highlight['title'][:80]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Sentiment analysis test failed: {e}")
        return False

def test_recommendation_engine():
    """Test the full recommendation engine"""
    print("\n🤖 Testing AI Recommendation Engine")
    print("=" * 45)
    
    try:
        # Initialize all clients
        config = ConfigLoader()
        av_client = AlphaVantageClient()
        fh_client = FinnhubClient()
        ma_client = MarketAuxClient()
        
        # Initialize recommendation engine
        rec_engine = RecommendationEngine(av_client, fh_client, ma_client)
        
        # Load portfolio
        portfolio = config.load_portfolio()
        
        print("🔄 Generating comprehensive recommendations...")
        print("⏳ This will take a moment (analyzing technical + sentiment data)...")
        
        # Generate recommendations
        recommendations = rec_engine.generate_portfolio_recommendations(portfolio)
        
        # Display prioritized actions
        priority_actions = recommendations['prioritized_actions']
        print(f"\n🎯 TOP PRIORITY ACTIONS ({len(priority_actions)})")
        print("-" * 40)
        
        for i, action in enumerate(priority_actions[:5], 1):
            priority_icon = "🔥" if action['priority'] == 'high' else "⚠️"
            
            if action['type'] == 'stock_action':
                symbol = action['symbol']
                action_text = action['action']
                reasoning = action['reasoning']
                confidence = action.get('confidence', 0)
                
                print(f"{priority_icon} {i}. {action_text}: {symbol}")
                print(f"   Reason: {reasoning}")
                print(f"   Confidence: {confidence:.0%}")
            else:
                print(f"{priority_icon} {i}. {action['action']}")
                print(f"   Reason: {action['reason']}")
            print()
        
        # Display individual stock recommendations
        stock_recs = recommendations['stock_recommendations']
        print(f"\n📈 INDIVIDUAL STOCK RECOMMENDATIONS")
        print("-" * 45)
        
        for symbol, rec in stock_recs.items():
            recommendation = rec['recommendation']
            context = rec['context']
            
            if recommendation['action'] in ['STRONG BUY', 'BUY']:
                action_icon = "🟢"
            elif recommendation['action'] in ['STRONG SELL', 'SELL']:
                action_icon = "🔴"
            else:
                action_icon = "🟡"
            
            print(f"{action_icon} {symbol}: {recommendation['action']}")
            print(f"   Current: ${context['current_price']:.2f} | Position: {context['position_weight']:.1f}% | P&L: {context['current_gain_pct']:+.1f}%")
            print(f"   Reasoning: {recommendation['reasoning']}")
            print(f"   Confidence: {recommendation['confidence']:.0%}")
            
            # Show technical and sentiment summary
            tech_summary = rec.get('technical_summary', {})
            if tech_summary.get('available') and tech_summary.get('rsi'):
                rsi_data = tech_summary['rsi']
                print(f"   📊 RSI: {rsi_data['value']:.0f} ({rsi_data['signal']})")
            
            sent_summary = rec.get('sentiment_summary', {})
            if sent_summary.get('available'):
                print(f"   📰 Sentiment: {sent_summary['label'].title()} ({sent_summary['news_count']} articles)")
            
            print()
        
        # Portfolio overview
        market_context = recommendations['market_context']
        portfolio_recs = recommendations['portfolio_recommendations']
        
        print(f"📊 PORTFOLIO HEALTH CHECK")
        print("-" * 30)
        print(f"Total Value: ${market_context['portfolio_performance']['total_value']:.2f}")
        print(f"Performance: {market_context['portfolio_performance']['total_return_pct']:+.1f}%")
        print(f"Health: {portfolio_recs['portfolio_health'].title()}")
        print(f"Risk Level: {portfolio_recs['risk_level'].title()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Recommendation engine test failed: {e}")
        print(f"💡 This might be due to API rate limits - try again in a few minutes")
        return False

def test_individual_stock_analysis():
    """Test detailed analysis for one stock"""
    print("\n🔍 Testing Individual Stock Analysis")
    print("=" * 40)
    
    try:
        # Get first stock from portfolio
        config = ConfigLoader()
        portfolio = config.load_portfolio()
        symbols = list(portfolio.get('stocks', {}).keys())
        
        if not symbols:
            print("❌ No stocks in portfolio")
            return False
        
        test_symbol = symbols[0]
        print(f"🧪 Testing detailed analysis for {test_symbol}")
        
        # Initialize clients
        av_client = AlphaVantageClient()
        fh_client = FinnhubClient()
        ma_client = MarketAuxClient()
        
        rec_engine = RecommendationEngine(av_client, fh_client, ma_client)
        
        # Get technical analysis
        print(f"📊 Getting technical analysis...")
        technical = rec_engine.technical_analyzer.get_comprehensive_analysis(test_symbol)
        
        if technical.get('overall_signal'):
            overall = technical['overall_signal']
            print(f"   Technical Signal: {overall['action'].upper()} ({overall['strength']})")
            print(f"   Confidence: {overall['confidence']:.1%}")
            print(f"   Reason: {overall['reason']}")
        
        # Get sentiment analysis
        print(f"📰 Getting sentiment analysis...")
        sentiment = rec_engine.sentiment_analyzer.get_sentiment_for_symbol(test_symbol)
        
        if sentiment:
            print(f"   Sentiment: {sentiment.get('sentiment_label', 'neutral').title()}")
            print(f"   Score: {sentiment.get('sentiment_score', 0):.2f}")
            print(f"   News Articles: {sentiment.get('news_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Individual stock analysis failed: {e}")
        return False

def main():
    """Run all Phase 3 tests"""
    print("🧪 Phase 3 AI Recommendation Engine Tester")
    print("=" * 60)
    
    tests = [
        ("News Sentiment Analysis", test_sentiment_analysis),
        ("Individual Stock Analysis", test_individual_stock_analysis),
        ("Full Recommendation Engine", test_recommendation_engine)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*70}")
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 Phase 3 Test Summary")
    print("=" * 30)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 Phase 3 AI Recommendations are working!")
        print("🤖 Your portfolio manager now has:")
        print("   📊 Technical analysis (RSI, MACD, SMA)")
        print("   📰 News sentiment analysis")
        print("   🎯 AI-powered buy/sell recommendations")
        print("   ⚠️ Risk management alerts")
        print("\n🚀 Ready to use: python portfolio_manager.py")
        print("   Try menu option 3: 🤖 AI Recommendations")
    elif passed > 0:
        print("⚠️ Some AI features working. Check API rate limits.")
        print("💡 Wait a few minutes and try again if you hit rate limits")
    else:
        print("❌ AI recommendation system failed. Check API connections.")

if __name__ == "__main__":
    main()