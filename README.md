# Personal Portfolio Tracker & AI Investment Bot

A comprehensive Python-based portfolio tracker that monitors your stock holdings, provides AI-powered investment recommendations, and sends daily updates via Telegram bot.

## 🚀 Features

### 📊 **Portfolio Management**
- Real-time portfolio tracking with live market data
- Interactive CLI for managing holdings
- Automatic price updates and performance calculations
- Cash balance management

## 📚 Understanding Stock Analysis Terms

New to investing? Here's what the AI recommendations mean:

### **Technical Indicators**
- **RSI (Relative Strength Index)**: Measures if a stock is overbought (>70, maybe sell) or oversold (<30, maybe buy)
- **MACD (Moving Average Convergence Divergence)**: Shows momentum changes - crossovers indicate potential buy/sell signals
- **SMA (Simple Moving Average)**: Average price over X days - when short-term crosses above long-term, it's bullish

### **Portfolio Terms**
- **P&L (Profit & Loss)**: How much money you've made (+) or lost (-)
- **Benchmark**: What you compare performance against (like S&P 500)
- **Volatility**: How much prices swing up and down (higher = more risky)

### **Market Sentiment**
- **Bullish** 🐂: Optimistic, expecting prices to rise
- **Bearish** 🐻: Pessimistic, expecting prices to fall
- **Position**: Your ownership in a specific stock

### **AI Recommendation Examples**
- *"NVDA oversold (RSI: 25) - potential buy opportunity"*
- *"TSLA showing bullish MACD crossover - upward momentum"*
- *"Portfolio up 12% vs S&P 500 +8% - outperforming market"*

## 🔧 Advanced Features

### **AI Recommendation Logic**
- **Technical Signals**: RSI oversold/overbought, MACD crossovers, SMA trends
- **Sentiment Signals**: News analysis, earnings reactions, analyst upgrades
- **Risk Management**: Profit-taking at +20%, stop-loss at -10%
- **Portfolio Context**: Position sizing, concentration limits, cash management

### 📱 **Telegram Integration**
- Daily portfolio reports sent to your phone
- Price movement alerts (5%+ changes)
- AI recommendations delivered automatically
- Error notifications and system health updates

### 🔄 **Daily Automation**
- Automated daily analysis via cron jobs
- Raspberry Pi optimized for 24/7 operation
- Comprehensive error handling and logging
- System health monitoring

## 📁 Project Structure

```
stock-portfolio-tracker/
├── portfolio_manager.py           # 🎯 Interactive CLI (main interface)
├── daily_tracker.py              # 🤖 Automated daily analysis
├── test_phase4.py                 # 🧪 Complete system testing
├── requirements.txt               # 📦 Python dependencies
├── src/
│   ├── api_clients/              # 📡 Market data APIs
│   │   ├── alpha_vantage.py      # Stock prices & technical indicators
│   │   ├── finnhub.py           # Company news & financials
│   │   └── marketaux.py         # News sentiment analysis
│   ├── analyzers/               # 🧠 AI analysis engines
│   │   ├── portfolio_analyzer.py # Performance & alerts
│   │   ├── technical_analyzer.py # RSI, MACD, SMA analysis
│   │   ├── sentiment_analyzer.py # News sentiment scoring
│   │   └── recommendation_engine.py # AI buy/sell decisions
│   ├── notifications/           # 📱 Telegram integration
│   │   ├── telegram_bot.py      # Message sending
│   │   └── message_formatter.py # Mobile-friendly formatting
│   └── utils/                   # 🔧 Core utilities
│       ├── config_loader.py     # Configuration management
│       ├── cache_manager.py     # API response caching
│       └── logger.py           # Logging system
├── install/
│   ├── setup_pi.sh             # 🍓 Raspberry Pi setup
│   └── crontab.example         # ⏰ Automation schedule
└── data/                       # 📊 Auto-created data directory
    ├── cache/                  # API response cache
    └── logs/                   # Application logs
```

## 🚀 Quick Start

### 1. **Clone & Setup**
```bash
git clone <your-repo-url>
cd stock-portfolio-tracker
pip install -r requirements.txt
```

### 2. **Configuration**
```bash
# Copy configuration templates
cp .env.example .env
cp portfolio.json.example portfolio.json
cp settings.json.example settings.json

# Edit with your data
nano .env              # Add API keys & Telegram bot token
nano portfolio.json    # Add your stock holdings
```

### 3. **Get API Keys (Free)**
- **Alpha Vantage**: [Get key](https://www.alphavantage.co/support/#api-key) (25 calls/day)
- **Finnhub**: [Get key](https://finnhub.io/register) (60 calls/minute)  
- **MarketAux**: [Get key](https://www.marketaux.com/pricing) (100 calls/month)
- **Telegram Bot**: Message [@BotFather](https://t.me/botfather) on Telegram

### 4. **Test System**
```bash
# Test all components
python test_phase4.py

# Test individual features
python portfolio_manager.py     # Interactive portfolio management
python daily_tracker.py --test  # Test automation system
```

### 5. **Setup Daily Automation**
```bash
# Add to crontab for daily 4:30 PM reports
crontab -e
# Add: 30 16 * * 1-5 cd /path/to/project && python3 daily_tracker.py
```

## 📱 Telegram Bot Setup

1. **Create Bot**: Message [@BotFather](https://t.me/botfather) → `/newbot`
2. **Get Token**: Copy the bot token to `.env`
3. **Get Chat ID**: 
   - Start your bot
   - Send a message to it
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Copy your chat ID to `.env`

## 🎯 Usage

### **Interactive Portfolio Manager**
```bash
python portfolio_manager.py
```
- **Option 1**: 📋 Show Portfolio (real-time prices)
- **Option 2**: 🔍 Live Analysis (detailed performance)
- **Option 3**: 🤖 AI Recommendations (buy/sell advice)
- **Option 4**: 📰 Sentiment Check (news analysis)
- **Option 5**: 🚨 Price Alerts (5%+ movements)

### **Daily Automation**
```bash
python daily_tracker.py           # Run daily analysis
python daily_tracker.py --test    # Test system health
```

## 💡 Example Portfolio Configuration

**portfolio.json**:
```json
{
  "stocks": {
    "AAPL": {
      "shares": 10.5,
      "avg_price": 150.00,
      "total_invested": 1575.00,
      "notes": "Tech holding"
    },
    "NVDA": {
      "shares": 5.0,
      "avg_price": 220.00,
      "total_invested": 1100.00,
      "notes": "AI/GPU play"
    }
  },
  "cash": {
    "available": 500.00,
    "currency": "USD"
  },
  "settings": {
    "benchmark": "VOO",
    "currency": "USD"
  }
}
```

## 📊 Daily Telegram Reports

You'll receive automated messages like:

```
📊 Daily Portfolio Summary
📅 July 8, 2025

💰 Value: $3,276.69
🟢 P&L: +$339.15 (+11.5%)

🤖 AI Recommendation:
🟢 BUY: NVDA (85%)

📈 Market Sentiment: Positive
```

## 🍓 Raspberry Pi Deployment

```bash
# Run setup script
chmod +x install/setup_pi.sh
./install/setup_pi.sh

# Follow the prompts for complete Pi setup
```

The setup script configures:
- Python environment
- System dependencies  
- Automated daily execution
- Log rotation
- Health monitoring

## 🔧 Advanced Features

### **AI Recommendation Logic**
- **Technical Signals**: RSI oversold/overbought, MACD crossovers, SMA trends
- **Sentiment Signals**: News analysis, earnings reactions, analyst upgrades
- **Risk Management**: Profit-taking at +20%, stop-loss at -10%
- **Portfolio Context**: Position sizing, concentration limits, cash management

### **Price Alert System**
- Automatic 5%+ movement detection
- Severity classification (high/medium)
- Position impact calculation
- Instant Telegram notifications

### **Error Handling**
- Graceful API failure handling
- Automatic fallback systems
- Error notifications via Telegram
- Comprehensive logging

## 🛠️ Troubleshooting

### **Common Issues**
```bash
# API connection issues
python test_apis.py

# Telegram bot issues  
python test_phase4.py

# Portfolio loading issues
python portfolio_manager.py

# Check logs
tail -f data/logs/*.log
```

### **System Health Check**
```bash
# Run health check (if on Pi)
./health_check.sh

# Test daily tracker
python daily_tracker.py --test
```

## 📈 Performance

- **API Calls**: Optimized with caching (5-min price cache, 1-hour indicator cache)
- **Rate Limiting**: Built-in delays to respect API limits
- **Memory Usage**: ~50MB typical operation
- **Execution Time**: 30-60 seconds for full analysis

## 🔒 Security

- All API keys stored in `.env` (git-ignored)
- Portfolio data in local JSON files
- No sensitive data transmitted
- Telegram bot uses secure HTTPS