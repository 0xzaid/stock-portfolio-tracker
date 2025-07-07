import requests
import time
from typing import Dict, List, Optional, Any
import os
from datetime import datetime
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from utils.logger import setup_logger

class TelegramBot:
    """
    Telegram bot for sending portfolio updates and recommendations
    """
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.logger = setup_logger("telegram_bot")
        
        if not self.bot_token or not self.chat_id:
            raise ValueError("Telegram bot token and chat ID must be provided")
    
    def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """Send a message to Telegram"""
        url = f"{self.base_url}/sendMessage"
        
        payload = {
            'chat_id': self.chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }
        
        try:
            response = requests.post(url, data=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                self.logger.info("Message sent successfully to Telegram")
                return True
            else:
                self.logger.error(f"Telegram API error: {result}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to send Telegram message: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending message: {e}")
            return False
    
    def send_portfolio_update(self, portfolio_analysis: Dict[str, Any]) -> bool:
        """Send formatted portfolio performance update"""
        message = self._format_portfolio_message(portfolio_analysis)
        return self.send_message(message)
    
    def send_recommendations(self, recommendations: Dict[str, Any]) -> bool:
        """Send AI recommendations"""
        message = self._format_recommendations_message(recommendations)
        return self.send_message(message)
    
    def send_price_alerts(self, alerts: List[Dict[str, Any]]) -> bool:
        """Send price movement alerts"""
        if not alerts:
            return True
        
        message = self._format_price_alerts_message(alerts)
        return self.send_message(message)
    
    def send_daily_report(self, portfolio_analysis: Dict[str, Any], 
                         recommendations: Dict[str, Any], 
                         alerts: List[Dict[str, Any]] = None) -> bool:
        """Send comprehensive daily report"""
        message = self._format_daily_report_message(portfolio_analysis, recommendations, alerts)
        return self.send_message(message)
    
    def _format_portfolio_message(self, analysis: Dict[str, Any]) -> str:
        """Format portfolio analysis for Telegram"""
        current_time = datetime.now().strftime("%B %d, %Y at %H:%M")
        
        total_value = analysis['current_value'] + analysis['cash']
        total_gain = analysis['total_gain_loss']
        total_pct = analysis['total_gain_loss_pct']
        
        # Main header
        gain_emoji = "🟢" if total_gain >= 0 else "🔴"
        sign = "+" if total_gain >= 0 else ""
        
        message = f"📊 *Portfolio Update* - {current_time}\n\n"
        
        # Portfolio summary
        message += f"💰 *Total Value:* ${total_value:,.2f}\n"
        message += f"{gain_emoji} *Performance:* {sign}${total_gain:,.2f} ({sign}{total_pct:.1f}%)\n"
        message += f"💵 *Available Cash:* ${analysis['cash']:,.2f}\n\n"
        
        # Individual holdings
        message += f"📈 *Holdings Performance:*\n"
        
        for symbol, stock in analysis['stocks'].items():
            stock_gain = stock['gain_loss']
            stock_pct = stock['gain_loss_pct']
            current_price = stock['current_price']
            
            stock_emoji = "🟢" if stock_gain >= 0 else "🔴"
            stock_sign = "+" if stock_gain >= 0 else ""
            
            message += f"{stock_emoji} *{symbol}:* ${current_price:.2f} ({stock_sign}{stock_pct:.1f}%)\n"
        
        # Price alerts if any
        if analysis.get('alerts'):
            message += f"\n🚨 *Price Alerts:*\n"
            for alert in analysis['alerts']:
                alert_emoji = "📈" if alert['type'] == 'gain' else "📉"
                message += f"{alert_emoji} {alert['symbol']}: {alert['change_pct']:+.1f}%\n"
        
        return message
    
    def _format_recommendations_message(self, recommendations: Dict[str, Any]) -> str:
        """Format AI recommendations for Telegram"""
        message = f"🤖 *AI Investment Recommendations*\n\n"
        
        # Priority actions
        priority_actions = recommendations.get('prioritized_actions', [])
        if priority_actions:
            message += f"🎯 *Top Actions:*\n"
            
            for i, action in enumerate(priority_actions[:3], 1):  # Top 3
                if action['type'] == 'stock_action':
                    symbol = action['symbol']
                    action_text = action['action']
                    confidence = action.get('confidence', 0)
                    
                    if action_text in ['STRONG BUY', 'BUY']:
                        emoji = "🟢"
                    elif action_text in ['STRONG SELL', 'SELL']:
                        emoji = "🔴"
                    else:
                        emoji = "🟡"
                    
                    message += f"{emoji} *{action_text}:* {symbol} ({confidence:.0%})\n"
                else:
                    message += f"💡 {action['action']}\n"
        
        # Portfolio health
        market_context = recommendations.get('market_context', {})
        portfolio_recs = recommendations.get('portfolio_recommendations', {})
        
        if portfolio_recs:
            health = portfolio_recs.get('portfolio_health', 'unknown')
            risk = portfolio_recs.get('risk_level', 'unknown')
            
            health_emoji = {"excellent": "🎉", "good": "✅", "fair": "⚠️", "poor": "❌"}.get(health, "📊")
            risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk, "⚪")
            
            message += f"\n📊 *Portfolio Health:* {health_emoji} {health.title()}\n"
            message += f"⚠️ *Risk Level:* {risk_emoji} {risk.title()}\n"
        
        # Market sentiment
        if market_context:
            portfolio_sentiment = market_context.get('portfolio_sentiment', {})
            if portfolio_sentiment:
                sentiment_label = portfolio_sentiment.get('label', 'neutral')
                sentiment_emoji = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}.get(sentiment_label, "⚪")
                message += f"📰 *News Sentiment:* {sentiment_emoji} {sentiment_label.title()}\n"
        
        message += f"\n🕐 *Analysis Time:* {datetime.now().strftime('%H:%M')}"
        
        return message
    
    def _format_price_alerts_message(self, alerts: List[Dict[str, Any]]) -> str:
        """Format price alerts for Telegram"""
        message = f"🚨 *Price Alerts* - {datetime.now().strftime('%H:%M')}\n\n"
        
        for alert in alerts[:5]:  # Top 5 alerts
            symbol = alert['symbol']
            change_pct = alert['change_pct']
            current_price = alert['current_price']
            position_value = alert['position_value']
            
            if change_pct > 0:
                emoji = "📈"
                alert_type = "GAIN"
            else:
                emoji = "📉"
                alert_type = "LOSS"
            
            message += f"{emoji} *{symbol} - {alert_type}*\n"
            message += f"   Change: {change_pct:+.1f}%\n"
            message += f"   Price: ${current_price:.2f}\n"
            message += f"   Position: ${position_value:.2f}\n\n"
        
        return message
    
    def _format_daily_report_message(self, portfolio_analysis: Dict[str, Any], 
                                   recommendations: Dict[str, Any], 
                                   alerts: List[Dict[str, Any]] = None) -> str:
        """Format comprehensive daily report"""
        current_date = datetime.now().strftime("%B %d, %Y")
        
        message = f"📊 *Daily Portfolio Report*\n"
        message += f"📅 {current_date}\n\n"
        
        # Portfolio performance summary
        total_value = portfolio_analysis['current_value'] + portfolio_analysis['cash']
        total_gain = portfolio_analysis['total_gain_loss']
        total_pct = portfolio_analysis['total_gain_loss_pct']
        
        gain_emoji = "🟢" if total_gain >= 0 else "🔴"
        sign = "+" if total_gain >= 0 else ""
        
        message += f"💰 *Portfolio Value:* ${total_value:,.2f}\n"
        message += f"{gain_emoji} *Total P&L:* {sign}${total_gain:,.2f} ({sign}{total_pct:.1f}%)\n\n"
        
        # Top performing stocks
        stocks = portfolio_analysis['stocks']
        if stocks:
            # Find best and worst performers
            best_stock = max(stocks.items(), key=lambda x: x[1]['gain_loss_pct'])
            worst_stock = min(stocks.items(), key=lambda x: x[1]['gain_loss_pct'])
            
            message += f"🏆 *Best:* {best_stock[0]} ({best_stock[1]['gain_loss_pct']:+.1f}%)\n"
            message += f"📉 *Worst:* {worst_stock[0]} ({worst_stock[1]['gain_loss_pct']:+.1f}%)\n\n"
        
        # AI recommendations summary
        priority_actions = recommendations.get('prioritized_actions', [])
        if priority_actions:
            top_action = priority_actions[0]
            if top_action['type'] == 'stock_action':
                action_emoji = "🟢" if 'BUY' in top_action['action'] else "🔴" if 'SELL' in top_action['action'] else "🟡"
                message += f"{action_emoji} *Top AI Rec:* {top_action['action']} {top_action['symbol']}\n\n"
        
        # Price alerts
        if alerts:
            message += f"🚨 *Alerts:* {len(alerts)} significant movements\n\n"
        
        # Market sentiment
        market_context = recommendations.get('market_context', {})
        portfolio_sentiment = market_context.get('portfolio_sentiment', {})
        if portfolio_sentiment:
            sentiment_label = portfolio_sentiment.get('label', 'neutral')
            sentiment_emoji = {"positive": "🟢", "negative": "🔴", "neutral": "🟡"}.get(sentiment_label, "⚪")
            message += f"📰 *Market Mood:* {sentiment_emoji} {sentiment_label.title()}\n"
        
        message += f"\n🤖 _Full analysis available in portfolio manager_"
        
        return message
    
    def test_connection(self) -> bool:
        """Test bot connection"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('ok'):
                bot_info = result.get('result', {})
                self.logger.info(f"Bot connected: {bot_info.get('first_name')} (@{bot_info.get('username')})")
                return True
            else:
                self.logger.error(f"Bot test failed: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Bot connection test failed: {e}")
            return False
    
    def send_test_message(self) -> bool:
        """Send a test message"""
        test_message = f"🧪 *Portfolio Bot Test*\n\n"
        test_message += f"✅ Bot is working correctly!\n"
        test_message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        test_message += f"Ready to send daily portfolio updates 📊"
        
        return self.send_message(test_message)