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
pip install requests python-dotenv pandas numpy beautifulsoup4 lxml

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

# Setup environment template
echo "⚙️ Creating environment template..."
tee $PROJECT_DIR/.env.example > /dev/null <<EOF
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

# Create portfolio template
echo "💼 Creating portfolio template..."
tee $PROJECT_DIR/portfolio.json.example > /dev/null <<EOF
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
else
    echo "❌ Environment file: Missing (.env)"
fi

# Check portfolio file
if [ -f "portfolio.json" ]; then
    echo "✅ Portfolio file: Found"
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

# Backup portfolio and environment
cp portfolio.json \$BACKUP_DIR/portfolio_\$DATE.json 2>/dev/null
cp .env \$BACKUP_DIR/env_\$DATE.backup 2>/dev/null

echo "✅ Portfolio backed up to \$BACKUP_DIR"

# Keep only last 30 backups
find \$BACKUP_DIR -name "portfolio_*.json" -type f -mtime +30 -delete
find \$BACKUP_DIR -name "env_*.backup" -type f -mtime +30 -delete
EOF

chmod +x $PROJECT_DIR/backup_portfolio.sh

# Set permissions
echo "🔐 Setting permissions..."
chown -R pi:pi $PROJECT_DIR
chmod +x $PROJECT_DIR/*.py

# Final instructions
echo ""
echo "🎉 Raspberry Pi setup complete!"
echo "================================"
echo ""
echo "📋 Next steps:"
echo "1. Copy your API keys:"
echo "   cp .env.example .env"
echo "   nano .env  # Add your actual API keys"
echo ""
echo "2. Set up your portfolio:"
echo "   cp portfolio.json.example portfolio.json"
echo "   nano portfolio.json  # Add your actual stocks"
echo ""
echo "3. Test the system:"
echo "   ./health_check.sh"
echo "   ./run_tracker.sh --test"
echo ""
echo "4. Enable daily automation:"
echo "   sudo systemctl start portfolio-tracker.timer"
echo "   sudo systemctl status portfolio-tracker.timer"
echo ""
echo "5. Or set up cron job instead:"
echo "   crontab -e"
echo "   # Add: 30 16 * * 1-5 $PROJECT_DIR/run_tracker.sh"
echo ""
echo "📍 Project location: $PROJECT_DIR"
echo "📱 Daily reports will be sent to your Telegram!"
echo ""
echo "🔧 Useful commands:"
echo "   ./health_check.sh           # Check system health"
echo "   ./run_tracker.sh --test     # Test all components"
echo "   ./run_tracker.sh            # Run daily analysis"
echo "   ./backup_portfolio.sh       # Backup your data"
echo ""