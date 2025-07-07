import requests
import time
from typing import Dict, Optional, Any, List
import os
from datetime import datetime, timedelta

class MarketAuxClient:
    """
    MarketAux API client for news and sentiment analysis
    Free tier: 100 requests per month
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('MARKETAUX_API_KEY')
        self.base_url = "https://api.marketaux.com/v1"
        self.last_request_time = 0
        self.min_request_interval = 2  # Conservative rate limiting for free tier
        
        if not self.api_key:
            raise ValueError("MarketAux API key not found. Set MARKETAUX_API_KEY in .env")
    
    def _make_request(self, endpoint: str, params: Dict[str, str] = None) -> Optional[Dict[str, Any]]:
        """Make rate-limited API request"""
        # Rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        if params is None:
            params = {}
        params['api_token'] = self.api_key
        
        try:
            url = f"{self.base_url}/{endpoint}"
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            self.last_request_time = time.time()
            
            data = response.json()
            
            # Check for API errors
            if 'error' in data:
                print(f"❌ MarketAux Error: {data['error']}")
                return None
                
            return data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ MarketAux request failed: {e}")
            return None
        except ValueError as e:
            print(f"❌ MarketAux JSON decode error: {e}")
            return None
    
    def get_news_by_symbols(self, symbols: List[str], limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """
        Get news articles for specific stock symbols
        """
        symbols_str = ','.join(symbols) if isinstance(symbols, list) else str(symbols)
        
        params = {
            'symbols': symbols_str,
            'filter_entities': 'true',
            'language': 'en',
            'limit': str(limit)
        }
        
        data = self._make_request('news/all', params)
        if data and 'data' in data:
            formatted_news = []
            for article in data['data']:
                formatted_news.append({
                    'title': article.get('title'),
                    'description': article.get('description'),
                    'url': article.get('url'),
                    'source': article.get('source'),
                    'published_at': article.get('published_at'),
                    'sentiment': self._extract_sentiment(article),
                    'entities': article.get('entities', []),
                    'symbols': [entity['symbol'] for entity in article.get('entities', []) if entity.get('symbol')]
                })
            return formatted_news
        return None
    
    def get_general_market_news(self, limit: int = 20) -> Optional[List[Dict[str, Any]]]:
        """Get general market news"""
        params = {
            'language': 'en',
            'limit': str(limit),
            'filter_entities': 'true'
        }
        
        data = self._make_request('news/all', params)
        if data and 'data' in data:
            return data['data']
        return None
    
    def get_news_by_keywords(self, keywords: List[str], limit: int = 10) -> Optional[List[Dict[str, Any]]]:
        """Search news by keywords"""
        keywords_str = ' OR '.join(keywords) if isinstance(keywords, list) else str(keywords)
        
        params = {
            'search': keywords_str,
            'language': 'en',
            'limit': str(limit),
            'filter_entities': 'true'
        }
        
        data = self._make_request('news/all', params)
        if data and 'data' in data:
            return data['data']
        return None
    
    def get_trending_news(self, limit: int = 15) -> Optional[List[Dict[str, Any]]]:
        """Get trending market news"""
        params = {
            'language': 'en',
            'limit': str(limit),
            'sort': 'entity_match_score',
            'filter_entities': 'true'
        }
        
        data = self._make_request('news/all', params)
        if data and 'data' in data:
            return data['data']
        return None
    
    def _extract_sentiment(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract sentiment information from article
        MarketAux provides sentiment in entities
        """
        entities = article.get('entities', [])
        
        sentiment_scores = []
        for entity in entities:
            if 'sentiment_score' in entity:
                sentiment_scores.append(entity['sentiment_score'])
        
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            return {
                'score': avg_sentiment,
                'label': self._sentiment_label(avg_sentiment),
                'confidence': len(sentiment_scores)  # More entities = higher confidence
            }
        
        return {
            'score': 0.0,
            'label': 'neutral',
            'confidence': 0
        }
    
    def _sentiment_label(self, score: float) -> str:
        """Convert sentiment score to label"""
        if score > 0.1:
            return 'positive'
        elif score < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def analyze_portfolio_sentiment(self, symbols: List[str]) -> Optional[Dict[str, Any]]:
        """
        Analyze overall sentiment for a portfolio of symbols
        """
        news = self.get_news_by_symbols(symbols, limit=50)
        if not news:
            return None
        
        # Aggregate sentiment by symbol
        symbol_sentiments = {}
        overall_scores = []
        
        for article in news:
            article_sentiment = article.get('sentiment', {})
            score = article_sentiment.get('score', 0)
            
            if score != 0:  # Only count articles with sentiment
                overall_scores.append(score)
                
                # Track sentiment by symbol
                for symbol in article.get('symbols', []):
                    if symbol in symbols:
                        if symbol not in symbol_sentiments:
                            symbol_sentiments[symbol] = []
                        symbol_sentiments[symbol].append(score)
        
        # Calculate overall portfolio sentiment
        overall_sentiment = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        
        # Calculate per-symbol sentiment
        for symbol in symbol_sentiments:
            scores = symbol_sentiments[symbol]
            symbol_sentiments[symbol] = {
                'avg_score': sum(scores) / len(scores),
                'article_count': len(scores),
                'label': self._sentiment_label(sum(scores) / len(scores))
            }
        
        return {
            'overall_sentiment': {
                'score': overall_sentiment,
                'label': self._sentiment_label(overall_sentiment),
                'article_count': len(overall_scores)
            },
            'symbol_sentiments': symbol_sentiments,
            'analysis_date': datetime.now().isoformat()
        }
    
    def test_connection(self) -> bool:
        """Test API connection with a simple news request"""
        print("🧪 Testing MarketAux connection...")
        
        result = self.get_general_market_news(limit=1)
        if result and len(result) > 0:
            print(f"✅ MarketAux connected - Found {len(result)} news articles")
            return True
        else:
            print("❌ MarketAux connection failed")
            return False