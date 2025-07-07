import json
import os
from typing import Dict, Any
from dotenv import load_dotenv

class ConfigLoader:
    def __init__(self):
        load_dotenv()
        self.portfolio_file = "portfolio.json"
        self.settings_file = "settings.json"
    
    def load_portfolio(self) -> Dict[str, Any]:
        """Load portfolio data from JSON file"""
        if not os.path.exists(self.portfolio_file):
            return self._create_default_portfolio()
        
        try:
            with open(self.portfolio_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"Error loading {self.portfolio_file}, creating default...")
            return self._create_default_portfolio()
    
    def save_portfolio(self, portfolio_data: Dict[str, Any]) -> bool:
        """Save portfolio data to JSON file"""
        try:
            with open(self.portfolio_file, 'w') as f:
                json.dump(portfolio_data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving portfolio: {e}")
            return False
    
    def load_settings(self) -> Dict[str, Any]:
        """Load settings from JSON file"""
        if not os.path.exists(self.settings_file):
            return self._create_default_settings()
        
        try:
            with open(self.settings_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            print(f"Error loading {self.settings_file}, using defaults...")
            return self._create_default_settings()
    
    def get_env(self, key: str, default: str = None) -> str:
        """Get environment variable"""
        return os.getenv(key, default)
    
    def _create_default_portfolio(self) -> Dict[str, Any]:
        """Create default portfolio structure"""
        default_portfolio = {
            "stocks": {},
            "settings": {
                "benchmark": "VOO",
                "currency": "USD"
            }
        }
        self.save_portfolio(default_portfolio)
        return default_portfolio
    
    def _create_default_settings(self) -> Dict[str, Any]:
        """Create default settings"""
        return {
            "alerts": {
                "price_threshold": 5,
                "enable_recommendations": True,
                "recommendation_strength": "moderate"
            },
            "technical_analysis": {
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "sma_short": 20,
                "sma_long": 50
            },
            "news": {
                "sentiment_threshold": 0.1,
                "sources": ["alpha_vantage", "finnhub", "marketaux"]
            }
        }