import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api_clients.alpha_vantage import AlphaVantageClient
from utils.cache_manager import CacheManager
from utils.logger import setup_logger

class TechnicalAnalyzer:
    """
    Technical analysis for stocks using RSI, MACD, SMA indicators
    """
    
    def __init__(self, alpha_vantage_client: AlphaVantageClient):
        self.av_client = alpha_vantage_client
        self.cache = CacheManager()
        self.logger = setup_logger("technical_analyzer")
    
    def get_rsi_analysis(self, symbol: str, period: int = 14) -> Optional[Dict[str, Any]]:
        """
        Get RSI (Relative Strength Index) analysis
        RSI > 70: Overbought, RSI < 30: Oversold
        """
        cache_key = f"rsi_{symbol}_{period}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Get RSI data from Alpha Vantage
            rsi_data = self.av_client.get_technical_indicator(
                symbol=symbol,
                indicator='RSI',
                time_period=period,
                series_type='close'
            )
            
            if not rsi_data or 'Technical Analysis: RSI' not in rsi_data:
                self.logger.warning(f"No RSI data available for {symbol}")
                return None
            
            rsi_series = rsi_data['Technical Analysis: RSI']
            
            # Get latest RSI value
            latest_date = max(rsi_series.keys())
            latest_rsi = float(rsi_series[latest_date]['RSI'])
            
            # Analyze RSI signal
            signal = self._analyze_rsi_signal(latest_rsi)
            
            # Get historical values for trend
            dates = sorted(rsi_series.keys(), reverse=True)[:5]  # Last 5 days
            historical_rsi = [float(rsi_series[date]['RSI']) for date in dates]
            
            analysis = {
                'symbol': symbol,
                'current_rsi': latest_rsi,
                'signal': signal,
                'trend': self._calculate_rsi_trend(historical_rsi),
                'historical_values': historical_rsi,
                'last_updated': latest_date,
                'period': period
            }
            
            # Cache for 1 hour
            self.cache.set(cache_key, analysis, ttl=3600)
            return analysis
            
        except Exception as e:
            self.logger.error(f"RSI analysis failed for {symbol}: {e}")
            return None
    
    def get_macd_analysis(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get MACD (Moving Average Convergence Divergence) analysis
        """
        cache_key = f"macd_{symbol}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Get MACD data from Alpha Vantage
            macd_data = self.av_client.get_technical_indicator(
                symbol=symbol,
                indicator='MACD',
                series_type='close'
            )
            
            if not macd_data or 'Technical Analysis: MACD' not in macd_data:
                self.logger.warning(f"No MACD data available for {symbol}")
                return None
            
            macd_series = macd_data['Technical Analysis: MACD']
            
            # Get latest MACD values
            latest_date = max(macd_series.keys())
            latest_data = macd_series[latest_date]
            
            macd_line = float(latest_data['MACD'])
            macd_signal = float(latest_data['MACD_Signal'])
            macd_histogram = float(latest_data['MACD_Hist'])
            
            # Analyze MACD signal
            signal = self._analyze_macd_signal(macd_line, macd_signal, macd_histogram)
            
            analysis = {
                'symbol': symbol,
                'macd_line': macd_line,
                'signal_line': macd_signal,
                'histogram': macd_histogram,
                'signal': signal,
                'last_updated': latest_date
            }
            
            # Cache for 1 hour
            self.cache.set(cache_key, analysis, ttl=3600)
            return analysis
            
        except Exception as e:
            self.logger.error(f"MACD analysis failed for {symbol}: {e}")
            return None
    
    def get_sma_analysis(self, symbol: str, short_period: int = 20, long_period: int = 50) -> Optional[Dict[str, Any]]:
        """
        Get SMA (Simple Moving Average) analysis
        """
        cache_key = f"sma_{symbol}_{short_period}_{long_period}"
        cached_data = self.cache.get(cache_key)
        if cached_data:
            return cached_data
        
        try:
            # Get both SMAs
            short_sma_data = self.av_client.get_technical_indicator(
                symbol=symbol,
                indicator='SMA',
                time_period=short_period,
                series_type='close'
            )
            
            # Small delay to avoid rate limiting
            time.sleep(2)
            
            long_sma_data = self.av_client.get_technical_indicator(
                symbol=symbol,
                indicator='SMA',
                time_period=long_period,
                series_type='close'
            )
            
            if (not short_sma_data or f'Technical Analysis: SMA' not in short_sma_data or
                not long_sma_data or f'Technical Analysis: SMA' not in long_sma_data):
                self.logger.warning(f"No SMA data available for {symbol}")
                return None
            
            short_sma_series = short_sma_data['Technical Analysis: SMA']
            long_sma_series = long_sma_data['Technical Analysis: SMA']
            
            # Get latest values
            short_latest_date = max(short_sma_series.keys())
            long_latest_date = max(long_sma_series.keys())
            
            short_sma = float(short_sma_series[short_latest_date]['SMA'])
            long_sma = float(long_sma_series[long_latest_date]['SMA'])
            
            # Analyze SMA crossover
            signal = self._analyze_sma_signal(short_sma, long_sma)
            
            analysis = {
                'symbol': symbol,
                'short_sma': short_sma,
                'long_sma': long_sma,
                'short_period': short_period,
                'long_period': long_period,
                'signal': signal,
                'last_updated': min(short_latest_date, long_latest_date)
            }
            
            # Cache for 1 hour
            self.cache.set(cache_key, analysis, ttl=3600)
            return analysis
            
        except Exception as e:
            self.logger.error(f"SMA analysis failed for {symbol}: {e}")
            return None
    
    def get_comprehensive_analysis(self, symbol: str) -> Dict[str, Any]:
        """
        Get comprehensive technical analysis combining all indicators
        """
        self.logger.info(f"Running comprehensive technical analysis for {symbol}")
        
        # Get all indicators (with delays to avoid rate limiting)
        rsi = self.get_rsi_analysis(symbol)
        time.sleep(2)
        
        macd = self.get_macd_analysis(symbol)
        time.sleep(2)
        
        sma = self.get_sma_analysis(symbol)
        
        # Combine signals
        signals = []
        if rsi:
            signals.append(rsi['signal'])
        if macd:
            signals.append(macd['signal'])
        if sma:
            signals.append(sma['signal'])
        
        # Calculate overall signal
        overall_signal = self._calculate_overall_signal(signals)
        
        return {
            'symbol': symbol,
            'rsi': rsi,
            'macd': macd,
            'sma': sma,
            'overall_signal': overall_signal,
            'signal_strength': self._calculate_signal_strength(signals),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _analyze_rsi_signal(self, rsi: float) -> Dict[str, Any]:
        """Analyze RSI value and return signal"""
        if rsi >= 70:
            return {
                'action': 'sell',
                'strength': 'strong' if rsi >= 80 else 'moderate',
                'reason': f'Overbought (RSI: {rsi:.1f})',
                'score': -2 if rsi >= 80 else -1
            }
        elif rsi <= 30:
            return {
                'action': 'buy',
                'strength': 'strong' if rsi <= 20 else 'moderate',
                'reason': f'Oversold (RSI: {rsi:.1f})',
                'score': 2 if rsi <= 20 else 1
            }
        else:
            return {
                'action': 'hold',
                'strength': 'neutral',
                'reason': f'Neutral (RSI: {rsi:.1f})',
                'score': 0
            }
    
    def _analyze_macd_signal(self, macd_line: float, signal_line: float, histogram: float) -> Dict[str, Any]:
        """Analyze MACD values and return signal"""
        if macd_line > signal_line and histogram > 0:
            return {
                'action': 'buy',
                'strength': 'moderate',
                'reason': 'MACD bullish crossover',
                'score': 1
            }
        elif macd_line < signal_line and histogram < 0:
            return {
                'action': 'sell',
                'strength': 'moderate',
                'reason': 'MACD bearish crossover',
                'score': -1
            }
        else:
            return {
                'action': 'hold',
                'strength': 'neutral',
                'reason': 'MACD neutral',
                'score': 0
            }
    
    def _analyze_sma_signal(self, short_sma: float, long_sma: float) -> Dict[str, Any]:
        """Analyze SMA crossover and return signal"""
        if short_sma > long_sma:
            strength = 'strong' if (short_sma - long_sma) / long_sma > 0.02 else 'moderate'
            return {
                'action': 'buy',
                'strength': strength,
                'reason': f'Short SMA above long SMA ({short_sma:.2f} > {long_sma:.2f})',
                'score': 2 if strength == 'strong' else 1
            }
        elif short_sma < long_sma:
            strength = 'strong' if (long_sma - short_sma) / long_sma > 0.02 else 'moderate'
            return {
                'action': 'sell',
                'strength': strength,
                'reason': f'Short SMA below long SMA ({short_sma:.2f} < {long_sma:.2f})',
                'score': -2 if strength == 'strong' else -1
            }
        else:
            return {
                'action': 'hold',
                'strength': 'neutral',
                'reason': 'SMAs converged',
                'score': 0
            }
    
    def _calculate_rsi_trend(self, historical_rsi: List[float]) -> str:
        """Calculate RSI trend from historical values"""
        if len(historical_rsi) < 2:
            return 'unknown'
        
        recent_avg = sum(historical_rsi[:2]) / 2
        older_avg = sum(historical_rsi[2:]) / len(historical_rsi[2:]) if len(historical_rsi) > 2 else recent_avg
        
        if recent_avg > older_avg + 5:
            return 'rising'
        elif recent_avg < older_avg - 5:
            return 'falling'
        else:
            return 'stable'
    
    def _calculate_overall_signal(self, signals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall signal from multiple indicators"""
        if not signals:
            return {
                'action': 'hold',
                'strength': 'neutral',
                'reason': 'No technical data available',
                'confidence': 0
            }
        
        total_score = sum(signal.get('score', 0) for signal in signals)
        signal_count = len(signals)
        
        if total_score >= 2:
            return {
                'action': 'buy',
                'strength': 'strong' if total_score >= 3 else 'moderate',
                'reason': f'Bullish signals from {signal_count} indicators',
                'confidence': min(signal_count / 3, 1.0)
            }
        elif total_score <= -2:
            return {
                'action': 'sell',
                'strength': 'strong' if total_score <= -3 else 'moderate',
                'reason': f'Bearish signals from {signal_count} indicators',
                'confidence': min(signal_count / 3, 1.0)
            }
        else:
            return {
                'action': 'hold',
                'strength': 'neutral',
                'reason': 'Mixed or neutral signals',
                'confidence': min(signal_count / 3, 1.0)
            }
    
    def _calculate_signal_strength(self, signals: List[Dict[str, Any]]) -> float:
        """Calculate overall signal strength (0-1)"""
        if not signals:
            return 0.0
        
        total_score = sum(abs(signal.get('score', 0)) for signal in signals)
        max_possible_score = len(signals) * 2  # Max score per signal is 2
        
        return min(total_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0