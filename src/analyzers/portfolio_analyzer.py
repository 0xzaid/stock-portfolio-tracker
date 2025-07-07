import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api_clients.alpha_vantage import AlphaVantageClient
from api_clients.finnhub import FinnhubClient
from utils.cache_manager import CacheManager
from utils.logger import setup_logger

class PortfolioAnalyzer:
    """
    Analyzes portfolio performance, calculates gains/losses, detects price movements
    """
    
    def __init__(self, alpha_vantage_client: AlphaVantageClient, finnhub_client: FinnhubClient = None):
        self.av_client = alpha_vantage_client
        self.fh_client = finnhub_client
        self.cache = CacheManager()
        self.logger = setup_logger("portfolio_analyzer")
        
        # Price alert settings
        self.price_alert_threshold = 5.0  # 5% change threshold
        
    def get_current_portfolio_value(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate current portfolio value with real-time prices
        """
        stocks = portfolio_data.get('stocks', {})
        cash = portfolio_data.get('cash', {}).get('available', 0)
        
        if not stocks:
            return {
                'total_invested': 0,
                'current_value': cash,
                'total_gain_loss': 0,
                'total_gain_loss_pct': 0,
                'cash': cash,
                'total_portfolio_value': cash,
                'stocks': {},
                'last_updated': datetime.now().isoformat()
            }
        
        results = {
            'stocks': {},
            'total_invested': 0,
            'current_value': 0,
            'total_gain_loss': 0,
            'alerts': [],
            'cash': cash,
            'last_updated': datetime.now().isoformat()
        }
        
        self.logger.info(f"Analyzing portfolio with {len(stocks)} stocks")
        
        for symbol, position in stocks.items():
            stock_analysis = self._analyze_stock_position(symbol, position)
            results['stocks'][symbol] = stock_analysis
            
            # Accumulate totals
            results['total_invested'] += stock_analysis['total_invested']
            results['current_value'] += stock_analysis['current_value']
            
            # Check for price alerts
            if stock_analysis['price_change_pct'] and abs(stock_analysis['price_change_pct']) >= self.price_alert_threshold:
                alert = {
                    'symbol': symbol,
                    'change_pct': stock_analysis['price_change_pct'],
                    'current_price': stock_analysis['current_price'],
                    'previous_price': stock_analysis.get('previous_close'),
                    'threshold': self.price_alert_threshold,
                    'type': 'gain' if stock_analysis['price_change_pct'] > 0 else 'loss'
                }
                results['alerts'].append(alert)
        
        # Calculate portfolio totals
        results['total_gain_loss'] = results['current_value'] - results['total_invested']
        results['total_gain_loss_pct'] = (results['total_gain_loss'] / results['total_invested'] * 100) if results['total_invested'] > 0 else 0
        results['total_portfolio_value'] = results['current_value'] + results['cash']
        
        self.logger.info(f"Portfolio analysis complete - Total value: ${results['total_portfolio_value']:.2f}")
        
        return results
    
    def _analyze_stock_position(self, symbol: str, position: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze individual stock position"""
        shares = position['shares']
        avg_price = position['avg_price']
        total_invested = position['total_invested']
        
        # Get current price with fallback
        current_price = self._get_current_price(symbol)
        if current_price is None:
            self.logger.warning(f"Could not get current price for {symbol}, using average price")
            current_price = avg_price
        
        current_value = shares * current_price
        gain_loss = current_value - total_invested
        gain_loss_pct = (gain_loss / total_invested * 100) if total_invested > 0 else 0
        
        # Get additional quote data
        quote_data = self._get_quote_data(symbol)
        
        return {
            'symbol': symbol,
            'shares': shares,
            'avg_price': avg_price,
            'current_price': current_price,
            'total_invested': total_invested,
            'current_value': current_value,
            'gain_loss': gain_loss,
            'gain_loss_pct': gain_loss_pct,
            'price_change': quote_data.get('change'),
            'price_change_pct': quote_data.get('change_percent'),
            'volume': quote_data.get('volume'),
            'high': quote_data.get('high'),
            'low': quote_data.get('low'),
            'previous_close': quote_data.get('previous_close'),
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current stock price with caching and fallback"""
        # Check cache first (5 minute expiry for real-time data)
        cache_key = f"price_{symbol}"
        cached_price = self.cache.get(cache_key)
        if cached_price:
            return cached_price
        
        # Try Alpha Vantage first
        try:
            quote = self.av_client.get_quote(symbol)
            if quote and quote['price']:
                price = float(quote['price'])
                self.cache.set(cache_key, price, ttl=300)  # 5 minute cache
                return price
        except Exception as e:
            self.logger.warning(f"Alpha Vantage failed for {symbol}: {e}")
        
        # Fallback to Finnhub
        if self.fh_client:
            try:
                quote = self.fh_client.get_quote(symbol)
                if quote and quote['price']:
                    price = float(quote['price'])
                    self.cache.set(cache_key, price, ttl=300)
                    return price
            except Exception as e:
                self.logger.warning(f"Finnhub fallback failed for {symbol}: {e}")
        
        return None
    
    def _get_quote_data(self, symbol: str) -> Dict[str, Any]:
        """Get full quote data with daily change info"""
        cache_key = f"quote_{symbol}"
        cached_quote = self.cache.get(cache_key)
        if cached_quote:
            return cached_quote
        
        # Try Alpha Vantage first
        try:
            quote = self.av_client.get_quote(symbol)
            if quote:
                quote_data = {
                    'change': float(quote.get('change', 0)),
                    'change_percent': float(quote.get('change_percent', 0)),
                    'volume': quote.get('volume'),
                    'high': quote.get('high'),
                    'low': quote.get('low'),
                    'previous_close': quote.get('price', 0) - quote.get('change', 0)
                }
                self.cache.set(cache_key, quote_data, ttl=300)
                return quote_data
        except Exception as e:
            self.logger.warning(f"Could not get quote data for {symbol}: {e}")
        
        # Fallback to Finnhub
        if self.fh_client:
            try:
                quote = self.fh_client.get_quote(symbol)
                if quote:
                    quote_data = {
                        'change': quote.get('change', 0),
                        'change_percent': quote.get('change_percent', 0),
                        'volume': quote.get('volume'),
                        'high': quote.get('high'),
                        'low': quote.get('low'),
                        'previous_close': quote.get('previous_close')
                    }
                    self.cache.set(cache_key, quote_data, ttl=300)
                    return quote_data
            except Exception as e:
                self.logger.warning(f"Finnhub quote fallback failed for {symbol}: {e}")
        
        return {}
    
    def detect_price_alerts(self, portfolio_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect significant price movements (5%+ changes)
        """
        alerts = []
        stocks = portfolio_data.get('stocks', {})
        
        self.logger.info(f"Checking price alerts for {len(stocks)} stocks")
        
        for symbol, position in stocks.items():
            quote_data = self._get_quote_data(symbol)
            change_pct = quote_data.get('change_percent')
            
            if change_pct and abs(float(change_pct)) >= self.price_alert_threshold:
                current_price = self._get_current_price(symbol)
                alert = {
                    'symbol': symbol,
                    'current_price': current_price,
                    'change_pct': float(change_pct),
                    'change_amount': quote_data.get('change', 0),
                    'threshold': self.price_alert_threshold,
                    'alert_type': 'price_movement',
                    'severity': 'high' if abs(float(change_pct)) >= 10 else 'medium',
                    'timestamp': datetime.now().isoformat(),
                    'position_value': position['shares'] * current_price if current_price else 0
                }
                alerts.append(alert)
                self.logger.info(f"Price alert: {symbol} {change_pct}%")
        
        return alerts
    
    def compare_to_benchmark(self, portfolio_data: Dict[str, Any], benchmark_symbol: str = "VOO") -> Dict[str, Any]:
        """
        Compare portfolio performance to benchmark
        """
        benchmark_price = self._get_current_price(benchmark_symbol)
        benchmark_quote = self._get_quote_data(benchmark_symbol)
        
        portfolio_analysis = self.get_current_portfolio_value(portfolio_data)
        
        return {
            'portfolio_return_pct': portfolio_analysis['total_gain_loss_pct'],
            'benchmark_symbol': benchmark_symbol,
            'benchmark_change_pct': benchmark_quote.get('change_percent', 0),
            'benchmark_price': benchmark_price,
            'outperforming': portfolio_analysis['total_gain_loss_pct'] > float(benchmark_quote.get('change_percent', 0)),
            'performance_difference': portfolio_analysis['total_gain_loss_pct'] - float(benchmark_quote.get('change_percent', 0)),
            'analysis_date': datetime.now().isoformat()
        }
    
    def get_portfolio_summary(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get comprehensive portfolio summary with all analytics
        """
        analysis = self.get_current_portfolio_value(portfolio_data)
        alerts = self.detect_price_alerts(portfolio_data)
        benchmark = self.compare_to_benchmark(portfolio_data)
        
        return {
            'portfolio_value': analysis,
            'price_alerts': alerts,
            'benchmark_comparison': benchmark,
            'summary': {
                'total_stocks': len(portfolio_data.get('stocks', {})),
                'alerts_count': len(alerts),
                'biggest_gainer': self._find_biggest_mover(analysis['stocks'], 'gain'),
                'biggest_loser': self._find_biggest_mover(analysis['stocks'], 'loss'),
                'analysis_timestamp': datetime.now().isoformat()
            }
        }
    
    def _find_biggest_mover(self, stocks: Dict[str, Any], direction: str) -> Optional[Dict[str, Any]]:
        """Find biggest gainer or loser"""
        if not stocks:
            return None
        
        best_stock = None
        best_pct = 0 if direction == 'gain' else float('inf')
        
        for symbol, data in stocks.items():
            gain_loss_pct = data.get('gain_loss_pct', 0)
            
            if direction == 'gain' and gain_loss_pct > best_pct:
                best_pct = gain_loss_pct
                best_stock = {'symbol': symbol, 'gain_loss_pct': gain_loss_pct}
            elif direction == 'loss' and gain_loss_pct < best_pct:
                best_pct = gain_loss_pct
                best_stock = {'symbol': symbol, 'gain_loss_pct': gain_loss_pct}
        
        return best_stock