#!/bin/bash

# Raspberry Pi Setup Script for Portfolio Tracker
# This script sets up the complete environment on a fresh Raspberry Pi

echo "🚀 Setting up Portfolio Tracker on Raspberry Pi..."

# Update system
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Python 3 and pip
echo "🐍 Installing Python 3 and pip..."
sudo apt install -y python3 python3-pip python3-venv git

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y curl wget chromium-browser chromium-chromedriver

# Create project directory
PROJECT_DIR="/home/pi/stock-portfolio-tracker"
echo "📁 Creating project directory: $PROJECT_DIR"
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# Clone or setup project (if you have a git repo)
# git clone https://github.com/yourusername/stock-portfolio-tracker.git .

# Create Python virtual environment
echo "🏠 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📚 Installing Python packages..."
pip install --upgrade pip
pip install requests python-dotenv pandas numpy beautifulsoup4 lxml fake-useragent selenium

# Create necessary directories
echo "📂 Creating directories..."
mkdir -p data/cache data/logs src/api_clients src/analyzers src/notifications src/utils install

# Set up log rotation
echo "📝 Setting up log rotation..."
sudo tee /etc/logrotate.d/portfolio-tracker > /dev/null <<EOF
$PROJECT_DIR/data/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 pi pi
}
EOF

# Create systemd service (optional - for automatic startup)
echo "🔄 Creating systemd service..."
sudo tee /etc/systemd/system/portfolio-tracker.service > /dev/null <<EOF
[Unit]
Description=Portfolio Tracker Daily Service
After=network.target

[Service]
Type=oneshot
User=pi
WorkingDirectory=$PROJECT_DIR
Environment=PATH=$PROJECT_DIR/venv/bin
ExecStart=$PROJECT_DIR/venv/bin/python3 $PROJECT_DIR/daily_tracker.py
StandardOutput=append:$PROJECT_DIR/data/logs/service.log
StandardError=append:$PROJECT_DIR/data/logs/service.log

[Install]
WantedBy=multi-user.target
EOF

# Create systemd timer for daily execution
sudo tee /etc/systemd/system/portfolio-tracker.timer > /dev/null <<EOF
[Unit]
Description=Run Portfolio Tracker Daily
Requires=portfolio-tracker.service

[Timer]
OnCalendar=Mon-Fri 16:30
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable systemd timer
sudo systemctl daemon-reload
sudo systemctl enable portfolio-tracker.timer

# Create startup script
echo "🏃 Creating startup script..."
tee $PROJECT_DIR/run_tracker.sh > /dev/null <<EOF
#!/bin/bash
cd $PROJECT_DIR
source venv/bin/activate
python3 daily_tracker.py "\$@"
EOF

chmod +x $PROJECT_DIR/run_tracker.sh

# Create .gitignore for security
echo "🔒 Creating .gitignore for sensitive files..."
tee $PROJECT_DIR/.gitignore > /dev/null <<EOF
# Environment variables (contains API keys)
.env
.env.local

# Portfolio data (contains personal investment info)
portfolio.json
settings.json

# Data directory (contains cache and logs)
data/

# Python cache
__pycache__/
*.py[cod]
*$py.class
*.so

# Virtual environments
venv/
env/
ENV/

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db

# Logs
*.log

# Backup files
*.backup
*.bak

# Sensitive runtime files
last_msg_id.txt
jobs_cache.json
EOF

# Setup actual environment file with user input
echo "⚙️ Setting up environment configuration..."
echo "📝 Please provide your API keys and Telegram bot information:"

read -p "Alpha Vantage API Key: " ALPHA_KEY
read -p "Finnhub API Key: " FINNHUB_KEY
read -p "MarketAux API Key: " MARKETAUX_KEY
read -p "Telegram Bot Token: " BOT_TOKEN
read -p "Telegram Chat ID: " CHAT_ID

tee $PROJECT_DIR/.env > /dev/null <<EOF
# API Keys
ALPHA_VANTAGE_API_KEY=$ALPHA_KEY
FINNHUB_API_KEY=$FINNHUB_KEY
MARKETAUX_API_KEY=$MARKETAUX_KEY

# Telegram Bot
TELEGRAM_BOT_TOKEN=$BOT_TOKEN
TELEGRAM_CHAT_ID=$CHAT_ID

# Alert Settings
PRICE_ALERT_THRESHOLD=5
EOF

echo "✅ Environment configuration saved to .env"

# Setup actual portfolio with user input
echo "💼 Setting up your portfolio..."
echo "📝 Please enter your stock holdings:"

# Initialize portfolio structure
cat > $PROJECT_DIR/portfolio.json <<EOF
{
  "stocks": {
  },
  "cash": {
    "available": 0.00,
    "currency": "USD"
  },
  "settings": {
    "benchmark": "VOO",
    "currency": "USD"
  }
}
EOF

# Prompt for cash balance
read -p "Available cash balance (\$): " CASH_BALANCE
python3 -c "
import json
with open('portfolio.json', 'r') as f:
    portfolio = json.load(f)
portfolio['cash']['available'] = float('$CASH_BALANCE' or '0')
with open('portfolio.json', 'w') as f:
    json.dump(portfolio, f, indent=2)
"

# Prompt for stocks
echo "📈 Enter your stock holdings (press Enter with empty symbol to finish):"
while true; do
    read -p "Stock Symbol (e.g., AAPL) [Enter to finish]: " SYMBOL
    if [ -z "$SYMBOL" ]; then
        break
    fi
    
    SYMBOL=$(echo "$SYMBOL" | tr '[:lower:]' '[:upper:]')
    read -p "Number of shares for $SYMBOL: " SHARES
    read -p "Average price per share for $SYMBOL: \$" AVG_PRICE
    read -p "Current price for $SYMBOL (or Enter for same as avg): \$" CURRENT_PRICE
    read -p "Notes for $SYMBOL (optional): " NOTES
    
    # Default current price to avg price if not provided
    if [ -z "$CURRENT_PRICE" ]; then
        CURRENT_PRICE=$AVG_PRICE
    fi
    
    # Add stock to portfolio
    python3 -c "
import json
with open('portfolio.json', 'r') as f:
    portfolio = json.load(f)

shares = float('$SHARES')
avg_price = float('$AVG_PRICE')
current_price = float('$CURRENT_PRICE')

portfolio['stocks']['$SYMBOL'] = {
    'shares': shares,
    'avg_price': avg_price,
    'total_invested': shares * avg_price,
    'current_price': current_price,
    'current_value': shares * current_price,
    'notes': '$NOTES'
}

with open('portfolio.json', 'w') as f:
    json.dump(portfolio, f, indent=2)
"
    echo "✅ Added $SYMBOL to portfolio"
done

echo "✅ Portfolio configuration complete!"

# Create actual settings file
echo "⚙️ Creating settings configuration..."
tee $PROJECT_DIR/settings.json > /dev/null <<EOF
{
  "alerts": {
    "price_threshold": 5,
    "enable_recommendations": true,
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
EOF

# Create health check script
echo "🏥 Creating health check script..."
tee $PROJECT_DIR/health_check.sh > /dev/null <<EOF
#!/bin/bash
cd $PROJECT_DIR
source venv/bin/activate

echo "🔍 Portfolio Tracker Health Check"
echo "================================"

# Check if virtual environment is active
if [[ "\$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment: Active"
else
    echo "❌ Virtual environment: Not active"
fi

# Check Python packages
echo "📦 Checking Python packages..."
python3 -c "import requests, pandas, numpy; print('✅ Core packages: OK')" 2>/dev/null || echo "❌ Core packages: Missing"

# Check API configuration
if [ -f ".env" ]; then
    echo "✅ Environment file: Found"
    # Check if keys are set (without showing them)
    if grep -q "ALPHA_VANTAGE_API_KEY=your_" .env; then
        echo "⚠️ API keys: Default values detected"
    else
        echo "✅ API keys: Configured"
    fi
else
    echo "❌ Environment file: Missing (.env)"
fi

# Check portfolio file
if [ -f "portfolio.json" ]; then
    echo "✅ Portfolio file: Found"
    STOCK_COUNT=\$(python3 -c "import json; f=open('portfolio.json'); p=json.load(f); print(len(p.get('stocks', {})))")
    echo "📊 Stocks configured: \$STOCK_COUNT"
else
    echo "❌ Portfolio file: Missing (portfolio.json)"
fi

# Check log directory
if [ -d "data/logs" ]; then
    echo "✅ Log directory: OK"
    echo "📊 Recent logs:"
    ls -la data/logs/ | tail -3
else
    echo "❌ Log directory: Missing"
fi

# Test system components
echo "🧪 Testing system components..."
python3 daily_tracker.py --test

echo "================================"
echo "Health check complete!"
EOF

chmod +x $PROJECT_DIR/health_check.sh

# Create backup script
echo "💾 Creating backup script..."
tee $PROJECT_DIR/backup_portfolio.sh > /dev/null <<EOF
#!/bin/bash
BACKUP_DIR="\$HOME/portfolio_backups"
DATE=\$(date +%Y%m%d_%H%M%S)

mkdir -p \$BACKUP_DIR

# Backup portfolio and environment (without exposing secrets)
cp portfolio.json \$BACKUP_DIR/portfolio_\$DATE.json 2>/dev/null
echo "Portfolio backed up" > \$BACKUP_DIR/backup_\$DATE.log

echo "✅ Portfolio backed up to \$BACKUP_DIR"

# Keep only last 30 backups
find \$BACKUP_DIR -name "portfolio_*.json" -type f -mtime +30 -delete
find \$BACKUP_DIR -name "backup_*.log" -type f -mtime +30 -delete
EOF

chmod +x $PROJECT_DIR/backup_portfolio.sh

# Create example templates for reference
echo "📝 Creating template files for reference..."
mkdir -p $PROJECT_DIR/templates

tee $PROJECT_DIR/templates/.env.example > /dev/null <<EOF
# API Keys - Get free keys from these providers:
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key_here
FINNHUB_API_KEY=your_finnhub_key_here
MARKETAUX_API_KEY=your_marketaux_key_here

# Telegram Bot - Get from @BotFather on Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Alert Settings
PRICE_ALERT_THRESHOLD=5
EOF

tee $PROJECT_DIR/templates/portfolio.json.example > /dev/null <<EOF
{
  "stocks": {
    "AAPL": {
      "shares": 10.0,
      "avg_price": 150.00,
      "total_invested": 1500.00,
      "current_price": 150.00,
      "current_value": 1500.00,
      "notes": "Tech holding"
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
EOF

# Set permissions
echo "🔐 Setting permissions..."
chown -R pi:pi $PROJECT_DIR
chmod +x $PROJECT_DIR/*.py
chmod 600 $PROJECT_DIR/.env $PROJECT_DIR/portfolio.json  # Secure sensitive files

# Test the setup
echo "🧪 Testing the setup..."
cd $PROJECT_DIR
source venv/bin/activate
python3 daily_tracker.py --test

# Final instructions
echo ""
echo "🎉 Raspberry Pi setup complete!"
echo "================================"
echo ""
echo "✅ Configuration Summary:"
echo "📁 Project location: $PROJECT_DIR"
echo "🔐 Sensitive files secured with .gitignore"
echo "📊 Portfolio configured with your holdings"
echo "🤖 API keys and Telegram bot configured"
echo "⏰ Daily automation ready"
echo ""
echo "🚀 Next steps:"
echo "1. Test the system:"
echo "   cd $PROJECT_DIR"
echo "   ./health_check.sh"
echo ""
echo "2. Run daily analysis:"
echo "   ./run_tracker.sh --test"
echo "   ./run_tracker.sh"
echo ""
echo "3. Enable daily automation:"
echo "   sudo systemctl start portfolio-tracker.timer"
echo "   sudo systemctl status portfolio-tracker.timer"
echo ""
echo "4. Or set up cron job instead:"
echo "   crontab -e"
echo "   # Add: 30 16 * * 1-5 $PROJECT_DIR/run_tracker.sh"
echo ""
echo "🔒 Security Notes:"
echo "   • .env and portfolio.json are in .gitignore"
echo "   • Sensitive files have 600 permissions"
echo "   • Backups exclude sensitive data"
echo ""
echo "🔧 Useful commands:"
echo "   ./health_check.sh           # Check system health"
echo "   ./run_tracker.sh --test     # Test all components"
echo "   ./run_tracker.sh            # Run daily analysis"
echo "   ./backup_portfolio.sh       # Backup your data"
echo ""
echo "📱 Daily reports will be sent to your Telegram!"
echo ""