from typing import Dict, List, Any
from datetime import datetime

class MessageFormatter:
    """
    Format various types of messages for Telegram delivery
    Optimized for mobile viewing with emojis and clean formatting
    """
    
    @staticmethod
    def format_daily_summary(portfolio_analysis: Dict[str, Any], 
                           recommendations: Dict[str, Any]) -> str:
        """Create concise daily summary message"""
        
        current_date = datetime.now().strftime("%B %d, %Y")
        
        # Portfolio basics
        total_value = portfolio_analysis['current_value'] + portfolio_analysis['cash']
        total_gain = portfolio_analysis['total_gain_loss']
        total_pct = portfolio_analysis['total_gain_loss_pct']
        
        gain_emoji = "🟢" if total_gain >= 0 else "🔴"
        sign = "+" if total_gain >= 0 else ""
        
        message = f"📊 *Daily Portfolio Summary*\n"
        message += f"📅 {current_date}\n\n"
        
        message += f"💰 *Value:* ${total_value:,.2f}\n"
        message += f"{gain_emoji} *P&L:* {sign}${total_gain:,.2f} ({sign}{total_pct:.1f}%)\n\n"
        
        # Top AI recommendation
        priority_actions = recommendations.get('prioritized_actions', [])
        if priority_actions:
            top_action = priority_actions[0]
            if top_action['type'] == 'stock_action':
                symbol = top_action['symbol']
                action = top_action['action']
                confidence = top_action.get('confidence', 0)
                
                action_emoji = "🟢" if 'BUY' in action else "🔴" if 'SELL' in action else "🟡"
                message += f"🤖 *AI Recommendation:*\n"
                message += f"{action_emoji} {action}: {symbol} ({confidence:.0%})\n\n"
        
        # Market sentiment
        market_context = recommendations.get('market_context', {})
        portfolio_sentiment = market_context.get('portfolio_sentiment', {})
        if portfolio_sentiment:
            sentiment_label = portfolio_sentiment.get('label', 'neutral')
            sentiment_emoji = {"positive": "📈", "negative": "📉", "neutral": "➡️"}.get(sentiment_label, "⚪")
            message += f"{sentiment_emoji} *Market Sentiment:* {sentiment_label.title()}\n"
        
        return message
    
    @staticmethod
    def format_detailed_performance(portfolio_analysis: Dict[str, Any]) -> str:
        """Create detailed performance breakdown"""
        
        message = f"📊 *Detailed Portfolio Performance*\n\n"
        
        # Individual holdings
        stocks = portfolio_analysis['stocks']
        sorted_stocks = sorted(stocks.items(), key=lambda x: x[1]['gain_loss_pct'], reverse=True)
        
        for symbol, stock in sorted_stocks:
            gain_pct = stock['gain_loss_pct']
            current_price = stock['current_price']
            gain_loss = stock['gain_loss']
            
            # Daily change if available
            daily_change = stock.get('price_change_pct', 0)
            
            gain_emoji = "🟢" if gain_pct >= 0 else "🔴"
            daily_emoji = "📈" if daily_change >= 0 else "📉" if daily_change < 0 else ""
            
            position_sign = "+" if gain_pct >= 0 else ""
            daily_sign = "+" if daily_change >= 0 else ""
            
            message += f"{gain_emoji} *{symbol}:* ${current_price:.2f}\n"
            message += f"   Position: {position_sign}{gain_pct:.1f}% (${gain_loss:+.2f})\n"
            
            if daily_change != 0:
                message += f"   {daily_emoji} Today: {daily_sign}{daily_change:.1f}%\n"
            
            message += "\n"
        
        # Cash
        cash = portfolio_analysis['cash']
        if cash > 0:
            message += f"💵 *Cash:* ${cash:,.2f}\n\n"
        
        # Totals
        total_invested = portfolio_analysis['total_invested']
        total_current = portfolio_analysis['current_value']
        total_gain = portfolio_analysis['total_gain_loss']
        total_pct = portfolio_analysis['total_gain_loss_pct']
        
        message += f"📈 *Summary:*\n"
        message += f"Invested: ${total_invested:,.2f}\n"
        message += f"Current: ${total_current:,.2f}\n"
        message += f"Gain/Loss: ${total_gain:+.2f} ({total_pct:+.1f}%)\n"
        
        return message
    
    @staticmethod
    def format_ai_recommendations(recommendations: Dict[str, Any]) -> str:
        """Format AI recommendations in mobile-friendly way"""
        
        message = f"🤖 *AI Investment Analysis*\n\n"
        
        # Priority actions
        priority_actions = recommendations.get('prioritized_actions', [])
        if priority_actions:
            message += f"🎯 *Recommended Actions:*\n"
            
            for i, action in enumerate(priority_actions[:4], 1):  # Top 4 actions
                priority_emoji = "🔥" if action['priority'] == 'high' else "⚠️" if action['priority'] == 'medium' else "💡"
                
                if action['type'] == 'stock_action':
                    symbol = action['symbol']
                    action_text = action['action']
                    reasoning = action['reasoning']
                    confidence = action.get('confidence', 0)
                    
                    if action_text in ['STRONG BUY', 'BUY']:
                        action_emoji = "🟢"
                    elif action_text in ['STRONG SELL', 'SELL']:
                        action_emoji = "🔴"
                    else:
                        action_emoji = "🟡"
                    
                    message += f"{priority_emoji} {action_emoji} *{action_text}: {symbol}*\n"
                    message += f"   {reasoning}\n"
                    message += f"   Confidence: {confidence:.0%}\n\n"
                else:
                    message += f"{priority_emoji} {action['action']}\n"
                    message += f"   {action['reason']}\n\n"
        
        # Portfolio health assessment
        portfolio_recs = recommendations.get('portfolio_recommendations', {})
        if portfolio_recs:
            health = portfolio_recs.get('portfolio_health', 'unknown')
            risk = portfolio_recs.get('risk_level', 'unknown')
            
            health_emoji = {
                "excellent": "🎉", 
                "good": "✅", 
                "fair": "⚠️", 
                "poor": "❌"
            }.get(health, "📊")
            
            risk_emoji = {
                "low": "🟢", 
                "medium": "🟡", 
                "high": "🔴"
            }.get(risk, "⚪")
            
            message += f"📊 *Portfolio Assessment:*\n"
            message += f"Health: {health_emoji} {health.title()}\n"
            message += f"Risk: {risk_emoji} {risk.title()}\n\n"
        
        # Market sentiment context
        market_context = recommendations.get('market_context', {})
        if market_context:
            portfolio_sentiment = market_context.get('portfolio_sentiment', {})
            market_sentiment = market_context.get('market_sentiment', {})
            
            if portfolio_sentiment:
                p_label = portfolio_sentiment.get('label', 'neutral')
                p_emoji = {"positive": "📈", "negative": "📉", "neutral": "➡️"}.get(p_label, "⚪")
                message += f"{p_emoji} *News Sentiment:* {p_label.title()}\n"
            
            if market_sentiment:
                m_label = market_sentiment.get('label', 'neutral')
                m_emoji = {"positive": "🌟", "negative": "⛈️", "neutral": "☁️"}.get(m_label, "⚪")
                message += f"{m_emoji} *Market Mood:* {m_label.title()}\n"
        
        message += f"\n🕐 {datetime.now().strftime('%H:%M')}"
        
        return message
    
    @staticmethod
    def format_price_alerts(alerts: List[Dict[str, Any]]) -> str:
        """Format price movement alerts"""
        
        if not alerts:
            return "✅ *No Price Alerts*\nAll positions within normal ranges"
        
        message = f"🚨 *Price Movement Alerts*\n\n"
        
        # Sort by magnitude of change
        sorted_alerts = sorted(alerts, key=lambda x: abs(x['change_pct']), reverse=True)
        
        for alert in sorted_alerts[:5]:  # Top 5 alerts
            symbol = alert['symbol']
            change_pct = alert['change_pct']
            current_price = alert['current_price']
            position_value = alert['position_value']
            severity = alert.get('severity', 'medium')
            
            # Determine emoji and alert type
            if change_pct > 0:
                emoji = "📈"
                alert_type = "GAIN"
                color = "🟢"
            else:
                emoji = "📉"
                alert_type = "LOSS"
                color = "🔴"
            
            severity_emoji = "🔥" if severity == 'high' else "⚠️"
            
            message += f"{color} {severity_emoji} *{symbol} - {alert_type}*\n"
            message += f"{emoji} Change: {change_pct:+.1f}%\n"
            message += f"💰 Price: ${current_price:.2f}\n"
            message += f"📊 Position Value: ${position_value:.2f}\n\n"
        
        return message
    
    @staticmethod
    def format_weekly_summary(weekly_data: Dict[str, Any]) -> str:
        """Format weekly performance summary"""
        
        message = f"📅 *Weekly Portfolio Summary*\n"
        message += f"{datetime.now().strftime('%B %d, %Y')}\n\n"
        
        # Weekly performance
        current_value = weekly_data.get('current_value', 0)
        week_start_value = weekly_data.get('week_start_value', current_value)
        weekly_change = current_value - week_start_value
        weekly_pct = (weekly_change / week_start_value * 100) if week_start_value > 0 else 0
        
        weekly_emoji = "🟢" if weekly_change >= 0 else "🔴"
        weekly_sign = "+" if weekly_change >= 0 else ""
        
        message += f"💰 *Current Value:* ${current_value:,.2f}\n"
        message += f"{weekly_emoji} *Weekly Change:* {weekly_sign}${weekly_change:,.2f} ({weekly_sign}{weekly_pct:.1f}%)\n\n"
        
        # Best/worst performers of the week
        stocks_performance = weekly_data.get('stocks_weekly_performance', {})
        if stocks_performance:
            best_symbol = max(stocks_performance.keys(), key=lambda x: stocks_performance[x])
            worst_symbol = min(stocks_performance.keys(), key=lambda x: stocks_performance[x])
            
            message += f"🏆 *Week's Best:* {best_symbol} ({stocks_performance[best_symbol]:+.1f}%)\n"
            message += f"📉 *Week's Worst:* {worst_symbol} ({stocks_performance[worst_symbol]:+.1f}%)\n\n"
        
        # AI insights summary
        insights = weekly_data.get('ai_insights', [])
        if insights:
            message += f"🤖 *Key Insights:*\n"
            for insight in insights[:3]:
                message += f"• {insight}\n"
        
        return message
    
    @staticmethod
    def format_error_message(error_type: str, error_details: str) -> str:
        """Format error notification message"""
        
        message = f"⚠️ *Portfolio Bot Alert*\n\n"
        message += f"❌ *Error Type:* {error_type}\n"
        message += f"📝 *Details:* {error_details}\n\n"
        message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        message += f"💡 The daily update may be delayed. Manual check recommended."
        
        return message
    
    @staticmethod
    def format_test_message() -> str:
        """Format test message to verify bot functionality"""
        
        message = f"🧪 *Portfolio Bot Test*\n\n"
        message += f"✅ Telegram connection working\n"
        message += f"📊 Portfolio analysis ready\n"
        message += f"🤖 AI recommendations active\n"
        message += f"🚨 Price alerts enabled\n\n"
        message += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        message += f"🚀 Daily updates will be sent automatically!"
        
        return message