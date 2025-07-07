import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api_clients.alpha_vantage import AlphaVantageClient
from api_clients.finnhub import FinnhubClient
from api_clients.marketaux import MarketAuxClient
from analyzers.portfolio_analyzer import PortfolioAnalyzer
from analyzers.technical_analyzer import TechnicalAnalyzer
from analyzers.sentiment_analyzer import SentimentAnalyzer
from utils.logger import setup_logger

class RecommendationEngine:
    """
    Generate buy/sell/hold recommendations by combining technical analysis,
    sentiment analysis, and portfolio context
    """
    
    def __init__(self, av_client: AlphaVantageClient, fh_client: FinnhubClient, ma_client: MarketAuxClient):
        self.av_client = av_client
        self.fh_client = fh_client
        self.ma_client = ma_client
        
        # Initialize analyzers
        self.portfolio_analyzer = PortfolioAnalyzer(av_client, fh_client)
        self.technical_analyzer = TechnicalAnalyzer(av_client)
        self.sentiment_analyzer = SentimentAnalyzer(ma_client, fh_client)
        
        self.logger = setup_logger("recommendation_engine")
        
        # Recommendation settings
        self.settings = {
            'max_position_size': 0.15,  # Max 15% of portfolio in one stock
            'profit_taking_threshold': 0.20,  # Take profits at 20% gain
            'stop_loss_threshold': -0.10,  # Stop loss at 10% loss
            'min_cash_reserve': 0.05,  # Keep 5% in cash
            'high_volatility_threshold': 0.10,  # 10% daily move = high volatility
            'strong_signal_threshold': 2,  # Need 2+ strong signals for strong recommendation
        }
    
    def generate_portfolio_recommendations(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive recommendations for entire portfolio
        """
        self.logger.info("Generating portfolio recommendations...")
        
        # Get current portfolio analysis
        portfolio_analysis = self.portfolio_analyzer.get_current_portfolio_value(portfolio_data)
        
        # Get sentiment analysis
        print("🔄 Analyzing news sentiment...")
        sentiment_analysis = self.sentiment_analyzer.analyze_portfolio_sentiment(portfolio_data)
        
        # Generate recommendations for each stock
        stock_recommendations = {}
        stocks = portfolio_data.get('stocks', {})
        
        for symbol in stocks.keys():
            print(f"🔄 Analyzing {symbol}...")
            recommendation = self._generate_stock_recommendation(
                symbol, 
                stocks[symbol], 
                portfolio_analysis, 
                sentiment_analysis.get('stock_sentiments', {}).get(symbol)
            )
            if recommendation:
                stock_recommendations[symbol] = recommendation
            
            # Rate limiting between technical analysis calls
            time.sleep(1)
        
        # Generate portfolio-level recommendations
        portfolio_recommendations = self._generate_portfolio_level_recommendations(
            portfolio_analysis, sentiment_analysis, stock_recommendations
        )
        
        # Prioritize recommendations
        prioritized_actions = self._prioritize_recommendations(stock_recommendations, portfolio_recommendations)
        
        return {
            'stock_recommendations': stock_recommendations,
            'portfolio_recommendations': portfolio_recommendations,
            'prioritized_actions': prioritized_actions,
            'market_context': {
                'portfolio_sentiment': sentiment_analysis.get('portfolio_sentiment'),
                'market_sentiment': sentiment_analysis.get('market_sentiment'),
                'portfolio_performance': {
                    'total_return_pct': portfolio_analysis['total_gain_loss_pct'],
                    'total_value': portfolio_analysis['current_value'] + portfolio_analysis['cash']
                }
            },
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _generate_stock_recommendation(self, symbol: str, position: Dict[str, Any], 
                                     portfolio_analysis: Dict[str, Any], 
                                     sentiment_data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Generate recommendation for individual stock"""
        
        try:
            # Get technical analysis
            technical = self.technical_analyzer.get_comprehensive_analysis(symbol)
            
            # Get position context from portfolio
            position_analysis = portfolio_analysis['stocks'].get(symbol, {})
            current_gain_pct = position_analysis.get('gain_loss_pct', 0)
            position_value = position_analysis.get('current_value', 0)
            total_portfolio_value = portfolio_analysis['current_value'] + portfolio_analysis['cash']
            position_weight = position_value / total_portfolio_value if total_portfolio_value > 0 else 0
            
            # Calculate signals
            signals = self._calculate_signals(technical, sentiment_data, position_analysis)
            
            # Generate recommendation based on signals
            recommendation = self._determine_recommendation(signals, position_weight, current_gain_pct)
            
            return {
                'symbol': symbol,
                'recommendation': recommendation,
                'signals': signals,
                'context': {
                    'current_gain_pct': current_gain_pct,
                    'position_weight': position_weight * 100,  # Convert to percentage
                    'current_price': position_analysis.get('current_price'),
                    'avg_cost': position.get('avg_price'),
                },
                'technical_summary': self._summarize_technical(technical),
                'sentiment_summary': self._summarize_sentiment(sentiment_data),
                'risk_factors': self._identify_risk_factors(signals, position_weight, current_gain_pct)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate recommendation for {symbol}: {e}")
            return None
    
    def _calculate_signals(self, technical: Dict[str, Any], sentiment_data: Optional[Dict[str, Any]], 
                          position_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate buy/sell signals from all sources"""
        
        signals = {
            'technical_score': 0,
            'sentiment_score': 0,
            'risk_score': 0,
            'total_score': 0,
            'signal_breakdown': {}
        }
        
        # Technical signals
        if technical.get('overall_signal'):
            tech_signal = technical['overall_signal']
            if tech_signal['action'] == 'buy':
                signals['technical_score'] = 2 if tech_signal['strength'] == 'strong' else 1
            elif tech_signal['action'] == 'sell':
                signals['technical_score'] = -2 if tech_signal['strength'] == 'strong' else -1
            
            signals['signal_breakdown']['technical'] = {
                'action': tech_signal['action'],
                'strength': tech_signal['strength'],
                'confidence': tech_signal.get('confidence', 0),
                'reason': tech_signal.get('reason', '')
            }
        
        # Sentiment signals
        if sentiment_data:
            sentiment_score = sentiment_data.get('sentiment_score', 0)
            if sentiment_score > 0.2:
                signals['sentiment_score'] = 2
            elif sentiment_score > 0.05:
                signals['sentiment_score'] = 1
            elif sentiment_score < -0.2:
                signals['sentiment_score'] = -2
            elif sentiment_score < -0.05:
                signals['sentiment_score'] = -1
            
            signals['signal_breakdown']['sentiment'] = {
                'label': sentiment_data.get('sentiment_label', 'neutral'),
                'score': sentiment_score,
                'confidence': sentiment_data.get('confidence', 0),
                'news_count': sentiment_data.get('news_count', 0)
            }
        
        # Risk management signals
        current_gain_pct = position_analysis.get('gain_loss_pct', 0)
        price_change_pct = position_analysis.get('price_change_pct', 0)
        
        # Profit taking signal
        if current_gain_pct >= self.settings['profit_taking_threshold'] * 100:
            signals['risk_score'] -= 2  # Strong sell signal for profit taking
        elif current_gain_pct >= 15:  # 15% gain
            signals['risk_score'] -= 1  # Moderate sell signal
        
        # Stop loss signal
        if current_gain_pct <= self.settings['stop_loss_threshold'] * 100:
            signals['risk_score'] -= 3  # Very strong sell signal for stop loss
        
        # High volatility signal
        if abs(price_change_pct or 0) >= self.settings['high_volatility_threshold'] * 100:
            signals['risk_score'] -= 1  # Caution due to high volatility
        
        signals['signal_breakdown']['risk_management'] = {
            'profit_taking': current_gain_pct >= 15,
            'stop_loss': current_gain_pct <= -8,
            'high_volatility': abs(price_change_pct or 0) >= 8
        }
        
        # Calculate total score
        signals['total_score'] = signals['technical_score'] + signals['sentiment_score'] + signals['risk_score']
        
        return signals
    
    def _determine_recommendation(self, signals: Dict[str, Any], position_weight: float, 
                                 current_gain_pct: float) -> Dict[str, Any]:
        """Determine final recommendation based on signals"""
        
        total_score = signals['total_score']
        
        # Strong signals
        if total_score >= 3:
            action = 'STRONG BUY'
            strength = 'high'
        elif total_score >= 2:
            action = 'BUY'
            strength = 'moderate'
        elif total_score <= -3:
            action = 'STRONG SELL'
            strength = 'high'
        elif total_score <= -2:
            action = 'SELL'
            strength = 'moderate'
        else:
            action = 'HOLD'
            strength = 'low'
        
        # Override for position sizing
        if action in ['STRONG BUY', 'BUY'] and position_weight >= self.settings['max_position_size']:
            action = 'HOLD'
            strength = 'low'
            override_reason = f"Position already {position_weight*100:.1f}% of portfolio (max: {self.settings['max_position_size']*100:.0f}%)"
        else:
            override_reason = None
        
        # Generate reasoning
        reasoning_parts = []
        if signals['technical_score'] != 0:
            tech_action = "bullish" if signals['technical_score'] > 0 else "bearish"
            reasoning_parts.append(f"Technical indicators {tech_action}")
        
        if signals['sentiment_score'] != 0:
            sent_action = "positive" if signals['sentiment_score'] > 0 else "negative"
            reasoning_parts.append(f"News sentiment {sent_action}")
        
        if signals['risk_score'] != 0:
            if current_gain_pct >= 15:
                reasoning_parts.append("Consider profit taking")
            elif current_gain_pct <= -8:
                reasoning_parts.append("Stop loss triggered")
        
        reasoning = " + ".join(reasoning_parts) if reasoning_parts else "Mixed signals"
        
        return {
            'action': action,
            'strength': strength,
            'confidence': self._calculate_confidence(signals),
            'reasoning': reasoning,
            'total_score': total_score,
            'override_reason': override_reason
        }
    
    def _generate_portfolio_level_recommendations(self, portfolio_analysis: Dict[str, Any], 
                                                sentiment_analysis: Dict[str, Any], 
                                                stock_recommendations: Dict[str, Any]) -> Dict[str, Any]:
        """Generate portfolio-level recommendations"""
        
        total_value = portfolio_analysis['current_value'] + portfolio_analysis['cash']
        cash_percentage = portfolio_analysis['cash'] / total_value * 100 if total_value > 0 else 0
        total_return_pct = portfolio_analysis['total_gain_loss_pct']
        
        recommendations = []
        
        # Cash management
        if cash_percentage < self.settings['min_cash_reserve'] * 100:
            recommendations.append({
                'type': 'cash_management',
                'action': 'Consider taking profits to build cash reserves',
                'priority': 'medium',
                'reason': f"Cash only {cash_percentage:.1f}% of portfolio"
            })
        elif cash_percentage > 20:
            recommendations.append({
                'type': 'cash_management',
                'action': 'Consider deploying excess cash',
                'priority': 'low',
                'reason': f"High cash allocation ({cash_percentage:.1f}%)"
            })
        
        # Portfolio performance
        if total_return_pct >= 25:
            recommendations.append({
                'type': 'profit_taking',
                'action': 'Consider rebalancing - portfolio up significantly',
                'priority': 'high',
                'reason': f"Portfolio up {total_return_pct:.1f}% - consider taking some profits"
            })
        elif total_return_pct <= -15:
            recommendations.append({
                'type': 'loss_management',
                'action': 'Review underperforming positions',
                'priority': 'high',
                'reason': f"Portfolio down {total_return_pct:.1f}% - assess risk management"
            })
        
        # Market sentiment context
        market_sentiment = sentiment_analysis.get('market_sentiment', {})
        if market_sentiment.get('label') == 'negative':
            recommendations.append({
                'type': 'market_timing',
                'action': 'Exercise caution - negative market sentiment',
                'priority': 'medium',
                'reason': 'Broader market sentiment is negative'
            })
        
        # Concentration risk
        position_weights = []
        for symbol, rec in stock_recommendations.items():
            weight = rec.get('context', {}).get('position_weight', 0)
            if weight > 15:  # More than 15% in one position
                recommendations.append({
                    'type': 'concentration_risk',
                    'action': f'Consider reducing {symbol} position',
                    'priority': 'medium',
                    'reason': f'{symbol} is {weight:.1f}% of portfolio (high concentration)'
                })
        
        return {
            'recommendations': recommendations,
            'portfolio_health': self._assess_portfolio_health(portfolio_analysis, sentiment_analysis),
            'risk_level': self._assess_risk_level(portfolio_analysis, stock_recommendations)
        }
    
    def _prioritize_recommendations(self, stock_recommendations: Dict[str, Any], 
                                  portfolio_recommendations: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize all recommendations by urgency and impact"""
        
        priority_actions = []
        
        # Add stock recommendations
        for symbol, rec in stock_recommendations.items():
            if rec['recommendation']['action'] in ['STRONG BUY', 'STRONG SELL']:
                priority = 'high'
            elif rec['recommendation']['action'] in ['BUY', 'SELL']:
                priority = 'medium'
            else:
                priority = 'low'
            
            if rec['recommendation']['action'] != 'HOLD':
                priority_actions.append({
                    'type': 'stock_action',
                    'symbol': symbol,
                    'action': rec['recommendation']['action'],
                    'reasoning': rec['recommendation']['reasoning'],
                    'priority': priority,
                    'confidence': rec['recommendation']['confidence']
                })
        
        # Add portfolio-level recommendations
        for rec in portfolio_recommendations.get('recommendations', []):
            priority_actions.append(rec)
        
        # Sort by priority (high -> medium -> low) and confidence
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        priority_actions.sort(
            key=lambda x: (priority_order.get(x.get('priority', 'low'), 1), 
                          x.get('confidence', 0)), 
            reverse=True
        )
        
        return priority_actions[:10]  # Top 10 actions
    
    def _summarize_technical(self, technical: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize technical analysis"""
        if not technical:
            return {'available': False}
        
        summary = {'available': True}
        
        if technical.get('rsi'):
            rsi_data = technical['rsi']
            summary['rsi'] = {
                'value': rsi_data['current_rsi'],
                'signal': rsi_data['signal']['action'],
                'interpretation': rsi_data['signal']['reason']
            }
        
        if technical.get('overall_signal'):
            summary['overall'] = {
                'action': technical['overall_signal']['action'],
                'strength': technical['overall_signal']['strength'],
                'confidence': technical['overall_signal']['confidence']
            }
        
        return summary
    
    def _summarize_sentiment(self, sentiment_data: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize sentiment analysis"""
        if not sentiment_data:
            return {'available': False}
        
        return {
            'available': True,
            'label': sentiment_data.get('sentiment_label', 'neutral'),
            'score': sentiment_data.get('sentiment_score', 0),
            'confidence': sentiment_data.get('confidence', 0),
            'news_count': sentiment_data.get('news_count', 0),
            'key_themes': sentiment_data.get('key_themes', [])
        }
    
    def _identify_risk_factors(self, signals: Dict[str, Any], position_weight: float, 
                              current_gain_pct: float) -> List[str]:
        """Identify risk factors for the position"""
        risks = []
        
        if position_weight > 0.15:
            risks.append(f"High concentration ({position_weight*100:.1f}% of portfolio)")
        
        if current_gain_pct >= 20:
            risks.append("Large unrealized gains - consider profit taking")
        elif current_gain_pct <= -10:
            risks.append("Significant losses - review thesis")
        
        if signals['signal_breakdown'].get('risk_management', {}).get('high_volatility'):
            risks.append("High recent volatility")
        
        technical_conf = signals['signal_breakdown'].get('technical', {}).get('confidence', 1)
        sentiment_conf = signals['signal_breakdown'].get('sentiment', {}).get('confidence', 1)
        
        if technical_conf < 0.5 and sentiment_conf < 0.5:
            risks.append("Low signal confidence")
        
        return risks
    
    def _calculate_confidence(self, signals: Dict[str, Any]) -> float:
        """Calculate overall confidence in recommendation"""
        technical_conf = signals['signal_breakdown'].get('technical', {}).get('confidence', 0)
        sentiment_conf = signals['signal_breakdown'].get('sentiment', {}).get('confidence', 0)
        
        # Weight technical analysis more heavily
        weighted_confidence = (technical_conf * 0.6 + sentiment_conf * 0.4)
        
        # Boost confidence if signals agree
        if abs(signals['technical_score']) > 0 and abs(signals['sentiment_score']) > 0:
            if (signals['technical_score'] > 0) == (signals['sentiment_score'] > 0):
                weighted_confidence = min(1.0, weighted_confidence * 1.2)  # 20% boost for agreement
        
        return round(weighted_confidence, 2)
    
    def _assess_portfolio_health(self, portfolio_analysis: Dict[str, Any], 
                                sentiment_analysis: Dict[str, Any]) -> str:
        """Assess overall portfolio health"""
        total_return = portfolio_analysis['total_gain_loss_pct']
        portfolio_sentiment = sentiment_analysis.get('portfolio_sentiment', {}).get('label', 'neutral')
        
        if total_return > 15 and portfolio_sentiment in ['positive', 'neutral']:
            return 'excellent'
        elif total_return > 5 and portfolio_sentiment != 'negative':
            return 'good'
        elif total_return > -5 and portfolio_sentiment != 'negative':
            return 'fair'
        else:
            return 'poor'
    
    def _assess_risk_level(self, portfolio_analysis: Dict[str, Any], 
                          stock_recommendations: Dict[str, Any]) -> str:
        """Assess overall portfolio risk level"""
        total_return = portfolio_analysis['total_gain_loss_pct']
        
        # Count high-risk positions
        high_risk_count = 0
        for symbol, rec in stock_recommendations.items():
            risks = rec.get('risk_factors', [])
            if any('concentration' in risk.lower() or 'volatility' in risk.lower() for risk in risks):
                high_risk_count += 1
        
        if high_risk_count >= 2 or total_return <= -15:
            return 'high'
        elif high_risk_count == 1 or abs(total_return) >= 20:
            return 'medium'
        else:
            return 'low'