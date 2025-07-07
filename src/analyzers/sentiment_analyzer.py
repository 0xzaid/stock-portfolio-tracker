import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from api_clients.marketaux import MarketAuxClient
from api_clients.finnhub import FinnhubClient
from utils.cache_manager import CacheManager
from utils.logger import setup_logger

class SentimentAnalyzer:
    """
    Analyze news sentiment for portfolio stocks and overall market
    """
    
    def __init__(self, marketaux_client: MarketAuxClient, finnhub_client: FinnhubClient = None):
        self.ma_client = marketaux_client
        self.fh_client = finnhub_client
        self.cache = CacheManager()
        self.logger = setup_logger("sentiment_analyzer")
    
    def analyze_portfolio_sentiment(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze sentiment for entire portfolio
        """
        stocks = portfolio_data.get('stocks', {})
        if not stocks:
            return {
                'portfolio_sentiment': {'score': 0, 'label': 'neutral', 'confidence': 0},
                'stock_sentiments': {},
                'market_sentiment': {'score': 0, 'label': 'neutral'},
                'analysis_timestamp': datetime.now().isoformat()
            }
        
        symbols = list(stocks.keys())
        self.logger.info(f"Analyzing sentiment for {len(symbols)} stocks: {symbols}")
        
        # Get portfolio-wide sentiment from MarketAux
        portfolio_sentiment = self._get_portfolio_sentiment_marketaux(symbols)
        
        # Get individual stock sentiments
        stock_sentiments = {}
        for symbol in symbols:
            stock_sentiment = self._get_stock_sentiment(symbol)
            if stock_sentiment:
                stock_sentiments[symbol] = stock_sentiment
        
        # Get general market sentiment
        market_sentiment = self._get_market_sentiment()
        
        # Calculate overall portfolio sentiment
        overall_sentiment = self._calculate_overall_sentiment(stock_sentiments, portfolio_sentiment)
        
        return {
            'portfolio_sentiment': overall_sentiment,
            'stock_sentiments': stock_sentiments,
            'market_sentiment': market_sentiment,
            'news_highlights': self._get_top_news_highlights(stock_sentiments),
            'sentiment_summary': self._create_sentiment_summary(overall_sentiment, stock_sentiments),
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _get_portfolio_sentiment_marketaux(self, symbols: List[str]) -> Optional[Dict[str, Any]]:
        """Get portfolio-wide sentiment from MarketAux"""
        cache_key = f"portfolio_sentiment_{'_'.join(sorted(symbols))}"
        cached_sentiment = self.cache.get(cache_key)
        if cached_sentiment:
            return cached_sentiment
        
        try:
            # Use MarketAux portfolio sentiment analysis
            sentiment_data = self.ma_client.analyze_portfolio_sentiment(symbols)
            if sentiment_data:
                portfolio_sentiment = sentiment_data.get('overall_sentiment', {})
                
                # Cache for 2 hours
                self.cache.set(cache_key, portfolio_sentiment, ttl=7200)
                return portfolio_sentiment
        except Exception as e:
            self.logger.warning(f"MarketAux portfolio sentiment failed: {e}")
        
        return None
    
    def _get_stock_sentiment(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get sentiment for individual stock"""
        cache_key = f"stock_sentiment_{symbol}"
        cached_sentiment = self.cache.get(cache_key)
        if cached_sentiment:
            return cached_sentiment
        
        sentiment_data = {
            'symbol': symbol,
            'sentiment_score': 0.0,
            'sentiment_label': 'neutral',
            'confidence': 0,
            'news_count': 0,
            'recent_news': [],
            'key_themes': []
        }
        
        try:
            # Get news from MarketAux
            news_articles = self.ma_client.get_news_by_symbols([symbol], limit=20)
            
            if news_articles:
                scores = []
                themes = []
                recent_news = []
                
                for article in news_articles[:10]:  # Top 10 articles
                    if article.get('sentiment'):
                        score = article['sentiment'].get('score', 0)
                        if score != 0:
                            scores.append(score)
                    
                    # Extract themes from title
                    title = article.get('title', '').lower()
                    if any(word in title for word in ['earnings', 'revenue', 'profit']):
                        themes.append('earnings')
                    if any(word in title for word in ['upgrade', 'buy', 'target']):
                        themes.append('analyst_upgrade')
                    if any(word in title for word in ['downgrade', 'sell', 'cut']):
                        themes.append('analyst_downgrade')
                    if any(word in title for word in ['partnership', 'deal', 'contract']):
                        themes.append('business_development')
                    
                    # Store recent news
                    if len(recent_news) < 3:
                        recent_news.append({
                            'title': article.get('title', '')[:100] + '...' if len(article.get('title', '')) > 100 else article.get('title', ''),
                            'source': article.get('source'),
                            'sentiment': article.get('sentiment', {}).get('label', 'neutral'),
                            'published_at': article.get('published_at')
                        })
                
                if scores:
                    avg_score = sum(scores) / len(scores)
                    sentiment_data.update({
                        'sentiment_score': avg_score,
                        'sentiment_label': self._score_to_label(avg_score),
                        'confidence': min(len(scores) / 10, 1.0),  # Confidence based on article count
                        'news_count': len(news_articles),
                        'recent_news': recent_news,
                        'key_themes': list(set(themes))  # Remove duplicates
                    })
        
        except Exception as e:
            self.logger.warning(f"Sentiment analysis failed for {symbol}: {e}")
        
        # Fallback to Finnhub news if MarketAux fails
        if sentiment_data['news_count'] == 0 and self.fh_client:
            try:
                finnhub_news = self.fh_client.get_company_news(symbol, days_back=3)
                if finnhub_news:
                    sentiment_data['news_count'] = len(finnhub_news)
                    sentiment_data['recent_news'] = [
                        {
                            'title': article['headline'][:100] + '...' if len(article['headline']) > 100 else article['headline'],
                            'source': article['source'],
                            'sentiment': 'neutral',  # Finnhub doesn't provide sentiment
                            'published_at': article['datetime'].isoformat() if article['datetime'] else None
                        }
                        for article in finnhub_news[:3]
                    ]
            except Exception as e:
                self.logger.warning(f"Finnhub news fallback failed for {symbol}: {e}")
        
        # Cache for 1 hour
        self.cache.set(cache_key, sentiment_data, ttl=3600)
        return sentiment_data
    
    def _get_market_sentiment(self) -> Dict[str, Any]:
        """Get general market sentiment"""
        cache_key = "market_sentiment"
        cached_sentiment = self.cache.get(cache_key)
        if cached_sentiment:
            return cached_sentiment
        
        market_sentiment = {
            'score': 0.0,
            'label': 'neutral',
            'trending_topics': [],
            'market_mood': 'neutral'
        }
        
        try:
            # Get trending market news
            trending_news = self.ma_client.get_trending_news(limit=20)
            
            if trending_news:
                scores = []
                topics = []
                
                for article in trending_news:
                    # Extract sentiment if available
                    if article.get('entities'):
                        for entity in article['entities']:
                            if entity.get('sentiment_score'):
                                scores.append(entity['sentiment_score'])
                    
                    # Extract trending topics
                    title = article.get('title', '').lower()
                    if 'fed' in title or 'interest rate' in title:
                        topics.append('monetary_policy')
                    if 'inflation' in title:
                        topics.append('inflation')
                    if 'earnings' in title:
                        topics.append('earnings_season')
                    if any(word in title for word in ['ai', 'artificial intelligence']):
                        topics.append('ai_technology')
                    if 'crypto' in title or 'bitcoin' in title:
                        topics.append('cryptocurrency')
                
                if scores:
                    avg_score = sum(scores) / len(scores)
                    market_sentiment.update({
                        'score': avg_score,
                        'label': self._score_to_label(avg_score),
                        'market_mood': self._score_to_mood(avg_score)
                    })
                
                market_sentiment['trending_topics'] = list(set(topics))[:5]  # Top 5 unique topics
        
        except Exception as e:
            self.logger.warning(f"Market sentiment analysis failed: {e}")
        
        # Cache for 30 minutes
        self.cache.set(cache_key, market_sentiment, ttl=1800)
        return market_sentiment
    
    def _calculate_overall_sentiment(self, stock_sentiments: Dict[str, Any], portfolio_sentiment: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall portfolio sentiment"""
        if not stock_sentiments:
            return {'score': 0.0, 'label': 'neutral', 'confidence': 0}
        
        # If we have MarketAux portfolio sentiment, use that
        if portfolio_sentiment and portfolio_sentiment.get('score') is not None:
            return portfolio_sentiment
        
        # Otherwise, calculate from individual stocks
        scores = []
        confidences = []
        
        for symbol, sentiment in stock_sentiments.items():
            if sentiment.get('sentiment_score') is not None:
                scores.append(sentiment['sentiment_score'])
                confidences.append(sentiment.get('confidence', 0))
        
        if scores:
            # Weighted average by confidence
            if sum(confidences) > 0:
                weighted_score = sum(s * c for s, c in zip(scores, confidences)) / sum(confidences)
                avg_confidence = sum(confidences) / len(confidences)
            else:
                weighted_score = sum(scores) / len(scores)
                avg_confidence = 0.5
            
            return {
                'score': weighted_score,
                'label': self._score_to_label(weighted_score),
                'confidence': avg_confidence
            }
        
        return {'score': 0.0, 'label': 'neutral', 'confidence': 0}
    
    def _get_top_news_highlights(self, stock_sentiments: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get top news highlights across portfolio"""
        highlights = []
        
        for symbol, sentiment in stock_sentiments.items():
            recent_news = sentiment.get('recent_news', [])
            for news in recent_news:
                if news.get('sentiment') in ['positive', 'negative']:  # Skip neutral
                    highlights.append({
                        'symbol': symbol,
                        'title': news['title'],
                        'sentiment': news['sentiment'],
                        'source': news['source']
                    })
        
        # Sort by sentiment strength (positive first, then negative)
        highlights.sort(key=lambda x: (x['sentiment'] == 'negative', x['sentiment'] == 'neutral'))
        return highlights[:5]  # Top 5 highlights
    
    def _create_sentiment_summary(self, overall_sentiment: Dict[str, Any], stock_sentiments: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of sentiment analysis"""
        positive_stocks = []
        negative_stocks = []
        neutral_stocks = []
        
        for symbol, sentiment in stock_sentiments.items():
            label = sentiment.get('sentiment_label', 'neutral')
            if label == 'positive':
                positive_stocks.append(symbol)
            elif label == 'negative':
                negative_stocks.append(symbol)
            else:
                neutral_stocks.append(symbol)
        
        return {
            'overall_mood': overall_sentiment.get('label', 'neutral'),
            'positive_stocks': positive_stocks,
            'negative_stocks': negative_stocks,
            'neutral_stocks': neutral_stocks,
            'sentiment_distribution': {
                'positive': len(positive_stocks),
                'negative': len(negative_stocks),
                'neutral': len(neutral_stocks)
            }
        }
    
    def _score_to_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def _score_to_mood(self, score: float) -> str:
        """Convert sentiment score to market mood"""
        if score > 0.3:
            return 'bullish'
        elif score > 0.1:
            return 'optimistic'
        elif score < -0.3:
            return 'bearish'
        elif score < -0.1:
            return 'pessimistic'
        else:
            return 'neutral'
    
    def get_sentiment_for_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get detailed sentiment analysis for a single symbol"""
        return self._get_stock_sentiment(symbol)