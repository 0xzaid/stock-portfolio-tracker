#!/usr/bin/env python3
"""
Daily Portfolio Tracker with AI Recommendations
Automated script that runs daily to:
1. Analyze portfolio performance
2. Generate AI recommendations
3. Send updates via Telegram
4. Handle errors gracefully
"""

import sys
import os
import time
import traceback
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.config_loader import ConfigLoader
from utils.logger import setup_logger
from api_clients.alpha_vantage import AlphaVantageClient
from api_clients.finnhub import FinnhubClient
from api_clients.marketaux import MarketAuxClient
from analyzers.portfolio_analyzer import PortfolioAnalyzer
from analyzers.recommendation_engine import RecommendationEngine
from notifications.telegram_bot import TelegramBot
from notifications.message_formatter import MessageFormatter

class DailyPortfolioTracker:
    """
    Daily automated portfolio analysis and reporting
    """
    
    def __init__(self):
        self.logger = setup_logger("daily_tracker")
        self.config = ConfigLoader()
        
        # Initialize components
        self.portfolio_data = None
        self.analyzer = None
        self.recommendation_engine = None
        self.telegram_bot = None
        
        self.logger.info("Daily Portfolio Tracker initialized")
    
    def initialize_apis(self) -> bool:
        """Initialize all API clients"""
        try:
            self.av_client = AlphaVantageClient()
            self.fh_client = FinnhubClient()
            self.ma_client = MarketAuxClient()
            
            self.analyzer = PortfolioAnalyzer(self.av_client, self.fh_client)
            self.recommendation_engine = RecommendationEngine(self.av_client, self.fh_client, self.ma_client)
            
            self.logger.info("APIs initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize APIs: {e}")
            return False
    
    def initialize_telegram(self) -> bool:
        """Initialize Telegram bot"""
        try:
            self.telegram_bot = TelegramBot()
            
            # Test connection
            if self.telegram_bot.test_connection():
                self.logger.info("Telegram bot connected successfully")
                return True
            else:
                self.logger.error("Telegram bot connection test failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to initialize Telegram bot: {e}")
            return False
    
    def load_portfolio(self) -> bool:
        """Load portfolio data"""
        try:
            self.portfolio_data = self.config.load_portfolio()
            
            stocks = self.portfolio_data.get('stocks', {})
            if not stocks:
                self.logger.warning("Portfolio is empty - no stocks to analyze")
                return False
            
            self.logger.info(f"Portfolio loaded with {len(stocks)} stocks: {list(stocks.keys())}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load portfolio: {e}")
            return False
    
    def analyze_portfolio(self) -> dict:
        """Run complete portfolio analysis"""
        self.logger.info("Starting portfolio analysis...")
        
        try:
            # Get current portfolio value with live prices
            portfolio_analysis = self.analyzer.get_current_portfolio_value(self.portfolio_data)
            
            # Detect price alerts
            price_alerts = self.analyzer.detect_price_alerts(self.portfolio_data)
            
            self.logger.info(f"Portfolio analysis complete - Value: ${portfolio_analysis['current_value'] + portfolio_analysis['cash']:.2f}")
            
            if price_alerts:
                self.logger.info(f"Detected {len(price_alerts)} price alerts")
            
            return {
                'portfolio_analysis': portfolio_analysis,
                'price_alerts': price_alerts,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"Portfolio analysis failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_recommendations(self) -> dict:
        """Generate AI recommendations"""
        self.logger.info("Generating AI recommendations...")
        
        try:
            recommendations = self.recommendation_engine.generate_portfolio_recommendations(self.portfolio_data)
            
            priority_actions = recommendations.get('prioritized_actions', [])
            self.logger.info(f"Generated {len(priority_actions)} prioritized recommendations")
            
            return {
                'recommendations': recommendations,
                'success': True
            }
            
        except Exception as e:
            self.logger.error(f"AI recommendation generation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_daily_report(self, portfolio_analysis: dict, recommendations: dict, price_alerts: list) -> bool:
        """Send comprehensive daily report via Telegram"""
        try:
            # Send daily summary (always)
            summary_message = MessageFormatter.format_daily_summary(portfolio_analysis, recommendations)
            success = self.telegram_bot.send_message(summary_message)
            
            if not success:
                self.logger.error("Failed to send daily summary")
                return False
            
            self.logger.info("Daily summary sent successfully")
            
            # Send price alerts if any
            if price_alerts:
                alert_message = MessageFormatter.format_price_alerts(price_alerts)
                alert_success = self.telegram_bot.send_message(alert_message)
                
                if alert_success:
                    self.logger.info(f"Price alerts sent for {len(price_alerts)} stocks")
                else:
                    self.logger.warning("Failed to send price alerts")
            
            # Send detailed recommendations (if we have good data)
            priority_actions = recommendations.get('prioritized_actions', [])
            if priority_actions:
                rec_message = MessageFormatter.format_ai_recommendations(recommendations)
                rec_success = self.telegram_bot.send_message(rec_message)
                
                if rec_success:
                    self.logger.info("AI recommendations sent successfully")
                else:
                    self.logger.warning("Failed to send AI recommendations")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send daily report: {e}")
            return False
    
    def send_error_notification(self, error_type: str, error_details: str) -> bool:
        """Send error notification to user"""
        try:
            if self.telegram_bot:
                error_message = MessageFormatter.format_error_message(error_type, error_details)
                return self.telegram_bot.send_message(error_message)
            return False
        except Exception as e:
            self.logger.error(f"Failed to send error notification: {e}")
            return False
    
    def run_daily_analysis(self) -> bool:
        """Run complete daily analysis and reporting"""
        start_time = datetime.now()
        self.logger.info(f"Starting daily portfolio analysis at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Step 1: Initialize everything
        if not self.load_portfolio():
            self.send_error_notification("Portfolio Loading Failed", "Could not load portfolio data")
            return False
        
        if not self.initialize_apis():
            self.send_error_notification("API Connection Failed", "Could not connect to market data APIs")
            return False
        
        if not self.initialize_telegram():
            self.logger.error("Telegram initialization failed - cannot send reports")
            return False
        
        # Step 2: Run analysis
        analysis_result = self.analyze_portfolio()
        if not analysis_result['success']:
            self.send_error_notification("Portfolio Analysis Failed", analysis_result.get('error', 'Unknown error'))
            return False
        
        portfolio_analysis = analysis_result['portfolio_analysis']
        price_alerts = analysis_result['price_alerts']
        
        # Step 3: Generate AI recommendations (with error handling)
        recommendation_result = self.generate_recommendations()
        if recommendation_result['success']:
            recommendations = recommendation_result['recommendations']
        else:
            # If AI fails, send basic portfolio update only
            self.logger.warning("AI recommendations failed, sending basic update only")
            summary_message = MessageFormatter.format_detailed_performance(portfolio_analysis)
            self.telegram_bot.send_message(summary_message)
            
            if price_alerts:
                alert_message = MessageFormatter.format_price_alerts(price_alerts)
                self.telegram_bot.send_message(alert_message)
            
            self.send_error_notification("AI Analysis Failed", recommendation_result.get('error', 'Unknown error'))
            return True  # Partial success
        
        # Step 4: Send comprehensive report
        report_success = self.send_daily_report(portfolio_analysis, recommendations, price_alerts)
        
        if not report_success:
            self.send_error_notification("Report Delivery Failed", "Could not send daily report")
            return False
        
        # Step 5: Log completion
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        total_value = portfolio_analysis['current_value'] + portfolio_analysis['cash']
        total_gain_pct = portfolio_analysis['total_gain_loss_pct']
        
        self.logger.info(f"Daily analysis completed successfully in {duration:.1f}s")
        self.logger.info(f"Portfolio value: ${total_value:.2f} ({total_gain_pct:+.1f}%)")
        self.logger.info(f"Price alerts: {len(price_alerts)}")
        self.logger.info(f"AI recommendations: {len(recommendations.get('prioritized_actions', []))}")
        
        return True
    
    def test_system(self) -> bool:
        """Test all system components"""
        self.logger.info("Running system test...")
        
        try:
            # Test portfolio loading
            if not self.load_portfolio():
                print("❌ Portfolio loading failed")
                return False
            print("✅ Portfolio loaded")
            
            # Test API connections
            if not self.initialize_apis():
                print("❌ API initialization failed")
                return False
            print("✅ APIs connected")
            
            # Test Telegram
            if not self.initialize_telegram():
                print("❌ Telegram bot failed")
                return False
            print("✅ Telegram bot connected")
            
            # Test analysis (quick version)
            print("🔄 Testing portfolio analysis...")
            stocks = list(self.portfolio_data['stocks'].keys())
            test_symbol = stocks[0] if stocks else None
            
            if test_symbol:
                # Quick price check
                current_price = self.analyzer._get_current_price(test_symbol)
                if current_price:
                    print(f"✅ Live data working - {test_symbol}: ${current_price:.2f}")
                else:
                    print("⚠️ Live data may be limited")
            
            # Send test message
            test_message = MessageFormatter.format_test_message()
            if self.telegram_bot.send_message(test_message):
                print("✅ Test message sent to Telegram")
            else:
                print("❌ Failed to send test message")
                return False
            
            print("🎉 All systems working!")
            return True
            
        except Exception as e:
            print(f"❌ System test failed: {e}")
            self.logger.error(f"System test failed: {e}")
            return False

def main():
    """Main entry point for daily tracker"""
    tracker = DailyPortfolioTracker()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            # Run system test
            success = tracker.test_system()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "--help":
            print("Daily Portfolio Tracker")
            print("Usage:")
            print("  python daily_tracker.py           # Run daily analysis")
            print("  python daily_tracker.py --test    # Test system components")
            print("  python daily_tracker.py --help    # Show this help")
            sys.exit(0)
    
    # Run daily analysis
    try:
        success = tracker.run_daily_analysis()
        
        if success:
            print("✅ Daily portfolio analysis completed successfully")
            sys.exit(0)
        else:
            print("❌ Daily portfolio analysis failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Daily tracker interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error in daily tracker: {e}")
        tracker.logger.error(f"Fatal error: {e}")
        tracker.logger.error(traceback.format_exc())
        
        # Try to send error notification
        try:
            if tracker.telegram_bot:
                tracker.send_error_notification("Daily Tracker Crashed", str(e))
        except:
            pass
        
        sys.exit(1)

if __name__ == "__main__":
    main()