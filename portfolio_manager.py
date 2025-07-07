#!/usr/bin/env python3
"""
Interactive Portfolio Manager CLI with Real-Time Analytics
Manage your stock holdings with live market data and performance analysis
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from utils.config_loader import ConfigLoader
from api_clients.alpha_vantage import AlphaVantageClient
from api_clients.finnhub import FinnhubClient
from analyzers.portfolio_analyzer import PortfolioAnalyzer

class PortfolioManager:
    def __init__(self):
        self.config = ConfigLoader()
        self.portfolio = self.config.load_portfolio()
        
        # Initialize API clients and analyzer
        try:
            self.av_client = AlphaVantageClient()
            self.fh_client = FinnhubClient()
            self.analyzer = PortfolioAnalyzer(self.av_client, self.fh_client)
            self.live_data_available = True
            print("✅ Connected to market data APIs")
        except Exception as e:
            print(f"⚠️ Live data unavailable: {e}")
            print("📊 Using static portfolio data only")
            self.analyzer = None
            self.live_data_available = False
    
    def show_portfolio(self):
        """Display current portfolio with real-time market data"""
        stocks = self.portfolio.get('stocks', {})
        cash = self.portfolio.get('cash', {})
        
        if not stocks:
            print("\n📊 Portfolio is empty")
            print("Use 'Add Stock' to get started!")
            return
        
        print(f"\n📊 Portfolio Summary")
        print("=" * 80)
        
        if self.live_data_available and self.analyzer:
            # Use real-time analytics
            try:
                print("🔄 Fetching live market data...")
                analysis = self.analyzer.get_current_portfolio_value(self.portfolio)
                self._display_live_portfolio(analysis)
            except Exception as e:
                print(f"⚠️ Live data failed: {e}")
                print("📊 Showing static portfolio data:")
                self._display_static_portfolio(stocks, cash)
        else:
            # Use static data from JSON
            self._display_static_portfolio(stocks, cash)
    
    def _display_live_portfolio(self, analysis):
        """Display portfolio with live market data"""
        # Individual stocks with real-time data
        for symbol, stock in analysis['stocks'].items():
            shares = stock['shares']
            avg_price = stock['avg_price']
            current_price = stock['current_price']
            current_value = stock['current_value']
            gain_loss = stock['gain_loss']
            gain_loss_pct = stock['gain_loss_pct']
            
            # Price change today
            price_change = stock.get('price_change', 0)
            price_change_pct = stock.get('price_change_pct', 0)
            
            # Color coding for gains/losses
            gain_indicator = "🟢" if gain_loss >= 0 else "🔴"
            price_indicator = "📈" if price_change >= 0 else "📉"
            gain_sign = "+" if gain_loss >= 0 else ""
            price_sign = "+" if price_change >= 0 else ""
            
            print(f"{gain_indicator} {symbol} - {shares} shares")
            print(f"   Current Price: ${current_price:.2f} {price_indicator} {price_sign}${price_change:.2f} ({price_sign}{price_change_pct:.1f}%)")
            print(f"   Avg Cost: ${avg_price:.2f} → Value: ${current_value:.2f}")
            print(f"   Position P&L: {gain_sign}${gain_loss:.2f} ({gain_sign}{gain_loss_pct:.1f}%)")
            
            # Volume and day range if available
            if stock.get('volume'):
                volume_k = stock['volume'] / 1000 if stock['volume'] > 1000 else stock['volume']
                unit = "K" if stock['volume'] > 1000 else ""
                print(f"   Volume: {volume_k:.0f}{unit}")
            
            if stock.get('high') and stock.get('low'):
                print(f"   Day Range: ${stock['low']:.2f} - ${stock['high']:.2f}")
            
            print()
        
        # Cash balance
        available_cash = analysis['cash']
        if available_cash > 0:
            print(f"💵 Available Cash: ${available_cash:.2f}")
            print()
        
        # Portfolio totals with live data
        total_invested = analysis['total_invested']
        total_current_value = analysis['current_value']
        total_portfolio_value = analysis['current_value'] + analysis['cash']
        total_gain_loss = analysis['total_gain_loss']
        total_gain_loss_pct = analysis['total_gain_loss_pct']
        
        print("=" * 80)
        print(f"💰 PORTFOLIO PERFORMANCE")
        print("=" * 80)
        print(f"💵 Total Invested: ${total_invested:.2f}")
        print(f"📈 Current Value: ${total_current_value:.2f}")
        print(f"💸 Available Cash: ${available_cash:.2f}")
        print(f"🏆 Total Portfolio: ${total_portfolio_value:.2f}")
        
        gain_indicator = "🟢" if total_gain_loss >= 0 else "🔴"
        gain_sign = "+" if total_gain_loss >= 0 else ""
        print(f"{gain_indicator} Total P&L: {gain_sign}${total_gain_loss:.2f} ({gain_sign}{total_gain_loss_pct:.1f}%)")
        
        # Price alerts
        if analysis.get('alerts'):
            print(f"\n🚨 PRICE ALERTS ({len(analysis['alerts'])})")
            print("-" * 40)
            for alert in analysis['alerts']:
                alert_icon = "📈" if alert['type'] == 'gain' else "📉"
                print(f"{alert_icon} {alert['symbol']}: {alert['change_pct']:+.1f}% movement detected!")
        
        benchmark = self.portfolio.get('settings', {}).get('benchmark', 'VOO')
        print(f"\n📊 Benchmark: {benchmark}")
        print(f"🕐 Last Updated: {analysis['last_updated'][:16]}")
        print("=" * 80)
    
    def _display_static_portfolio(self, stocks, cash):
        """Display portfolio with static JSON data (fallback)"""
        total_invested = 0
        total_current_value = 0
        
        for symbol, data in stocks.items():
            shares = data['shares']
            avg_price = data['avg_price']
            invested = data['total_invested']
            current_price = data.get('current_price', avg_price)
            current_value = data.get('current_value', invested)
            notes = data.get('notes', '')
            
            gain_loss = current_value - invested
            gain_loss_pct = (gain_loss / invested * 100) if invested > 0 else 0
            
            total_invested += invested
            total_current_value += current_value
            
            # Color coding for gains/losses
            gain_indicator = "🟢" if gain_loss >= 0 else "🔴"
            sign = "+" if gain_loss >= 0 else ""
            
            print(f"{gain_indicator} {symbol}")
            print(f"   Shares: {shares}")
            print(f"   Avg Price: ${avg_price:.2f} → Current: ${current_price:.2f}")
            print(f"   Invested: ${invested:.2f} → Value: ${current_value:.2f}")
            print(f"   Gain/Loss: {sign}${gain_loss:.2f} ({sign}{gain_loss_pct:.1f}%)")
            if notes:
                print(f"   Notes: {notes}")
            print()
        
        # Cash balance
        available_cash = cash.get('available', 0)
        if available_cash > 0:
            print(f"💵 Available Cash: ${available_cash:.2f}")
            print()
        
        # Portfolio totals
        total_portfolio_value = total_current_value + available_cash
        total_gain_loss = total_current_value - total_invested
        total_gain_loss_pct = (total_gain_loss / total_invested * 100) if total_invested > 0 else 0
        
        print("=" * 80)
        print(f"💰 Total Invested: ${total_invested:.2f}")
        print(f"📈 Current Value: ${total_current_value:.2f}")
        print(f"💵 Available Cash: ${available_cash:.2f}")
        print(f"🏆 Total Portfolio: ${total_portfolio_value:.2f}")
        
        gain_indicator = "🟢" if total_gain_loss >= 0 else "🔴"
        sign = "+" if total_gain_loss >= 0 else ""
        print(f"{gain_indicator} Total Gain/Loss: {sign}${total_gain_loss:.2f} ({sign}{total_gain_loss_pct:.1f}%)")
        
        benchmark = self.portfolio.get('settings', {}).get('benchmark', 'VOO')
        print(f"📊 Benchmark: {benchmark}")
        print("⚠️ Showing cached prices - use 'Live Analysis' for real-time data")
        print("=" * 80)
    
    def add_stock(self):
        """Add a new stock to portfolio"""
        print("\n➕ Add New Stock")
        print("-" * 20)
        
        symbol = input("Stock Symbol (e.g., AAPL): ").upper().strip()
        if not symbol:
            print("❌ Invalid symbol")
            return
        
        # Check if stock already exists
        if symbol in self.portfolio['stocks']:
            print(f"⚠️ {symbol} already exists in portfolio")
            choice = input("Update existing position? (y/n): ").lower()
            if choice != 'y':
                return
            self.update_stock(symbol)
            return
        
        try:
            shares = float(input("Number of shares: "))
            avg_price = float(input("Average price per share: $"))
            
            # Get current price if live data is available
            if self.live_data_available and self.analyzer:
                try:
                    current_price = self.analyzer._get_current_price(symbol)
                    if current_price:
                        print(f"💡 Current market price: ${current_price:.2f}")
                        use_current = input("Use current price for initial value? (y/n): ").lower()
                        if use_current == 'y':
                            current_price = current_price
                        else:
                            current_price_input = input(f"Enter current price (${current_price:.2f}): ").strip()
                            current_price = float(current_price_input) if current_price_input else current_price
                    else:
                        current_price_input = input(f"Current price (${avg_price:.2f}): ").strip()
                        current_price = float(current_price_input) if current_price_input else avg_price
                except:
                    current_price_input = input(f"Current price (${avg_price:.2f}): ").strip()
                    current_price = float(current_price_input) if current_price_input else avg_price
            else:
                current_price_input = input(f"Current price (${avg_price:.2f}): ").strip()
                current_price = float(current_price_input) if current_price_input else avg_price
            
            notes = input("Notes (optional): ").strip()
            
            total_invested = shares * avg_price
            current_value = shares * current_price
            
            self.portfolio['stocks'][symbol] = {
                'shares': shares,
                'avg_price': avg_price,
                'total_invested': total_invested,
                'current_price': current_price,
                'current_value': current_value,
                'notes': notes
            }
            
            if self.config.save_portfolio(self.portfolio):
                gain_loss = current_value - total_invested
                print(f"✅ Added {shares} shares of {symbol} at ${avg_price:.2f}")
                print(f"💰 Total investment: ${total_invested:.2f}")
                if current_price != avg_price:
                    sign = "+" if gain_loss >= 0 else ""
                    print(f"📈 Current value: ${current_value:.2f} ({sign}${gain_loss:.2f})")
            else:
                print("❌ Failed to save portfolio")
                
        except ValueError:
            print("❌ Invalid number format")
    
    def remove_stock(self):
        """Remove a stock from portfolio"""
        if not self.portfolio['stocks']:
            print("\n❌ Portfolio is empty")
            return
        
        print("\n➖ Remove Stock")
        print("-" * 15)
        
        # Show available stocks
        stocks = list(self.portfolio['stocks'].keys())
        for i, symbol in enumerate(stocks, 1):
            print(f"{i}. {symbol}")
        
        try:
            choice = input("\nEnter stock number or symbol: ").strip()
            
            # Handle numeric choice
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(stocks):
                    symbol = stocks[idx]
                else:
                    print("❌ Invalid choice")
                    return
            else:
                symbol = choice.upper()
            
            if symbol not in self.portfolio['stocks']:
                print(f"❌ {symbol} not found in portfolio")
                return
            
            # Confirm removal
            stock_data = self.portfolio['stocks'][symbol]
            print(f"\n🗑️ Remove {symbol}:")
            print(f"   Shares: {stock_data['shares']}")
            print(f"   Invested: ${stock_data['total_invested']:.2f}")
            
            confirm = input("Are you sure? (y/n): ").lower()
            if confirm == 'y':
                del self.portfolio['stocks'][symbol]
                if self.config.save_portfolio(self.portfolio):
                    print(f"✅ Removed {symbol} from portfolio")
                else:
                    print("❌ Failed to save portfolio")
            
        except ValueError:
            print("❌ Invalid input")
    
    def update_stock(self, symbol=None):
        """Update existing stock position"""
        if not self.portfolio['stocks']:
            print("\n❌ Portfolio is empty")
            return
        
        if not symbol:
            print("\n✏️ Update Stock")
            print("-" * 15)
            
            stocks = list(self.portfolio['stocks'].keys())
            for i, sym in enumerate(stocks, 1):
                print(f"{i}. {sym}")
            
            choice = input("\nEnter stock number or symbol: ").strip()
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(stocks):
                    symbol = stocks[idx]
                else:
                    print("❌ Invalid choice")
                    return
            else:
                symbol = choice.upper()
        
        if symbol not in self.portfolio['stocks']:
            print(f"❌ {symbol} not found in portfolio")
            return
        
        current = self.portfolio['stocks'][symbol]
        print(f"\n📝 Current {symbol} position:")
        print(f"   Shares: {current['shares']}")
        print(f"   Avg Price: ${current['avg_price']:.2f}")
        print(f"   Current Price: ${current.get('current_price', current['avg_price']):.2f}")
        print(f"   Invested: ${current['total_invested']:.2f}")
        print(f"   Current Value: ${current.get('current_value', current['total_invested']):.2f}")
        
        try:
            new_shares = input(f"New shares ({current['shares']}): ").strip()
            new_price = input(f"New avg price (${current['avg_price']:.2f}): ").strip()
            new_current_price = input(f"New current price (${current.get('current_price', current['avg_price']):.2f}): ").strip()
            new_notes = input(f"Notes ({current.get('notes', '')}): ").strip()
            
            # Use current values if no input
            shares = float(new_shares) if new_shares else current['shares']
            avg_price = float(new_price) if new_price else current['avg_price']
            current_price = float(new_current_price) if new_current_price else current.get('current_price', avg_price)
            notes = new_notes if new_notes else current.get('notes', '')
            
            self.portfolio['stocks'][symbol] = {
                'shares': shares,
                'avg_price': avg_price,
                'total_invested': shares * avg_price,
                'current_price': current_price,
                'current_value': shares * current_price,
                'notes': notes
            }
            
            if self.config.save_portfolio(self.portfolio):
                print(f"✅ Updated {symbol}")
            else:
                print("❌ Failed to save portfolio")
                
        except ValueError:
            print("❌ Invalid number format")
    
    def show_live_analysis(self):
        """Show detailed live portfolio analysis with alerts and benchmark comparison"""
        if not self.live_data_available:
            print("\n❌ Live analysis unavailable - API connections failed")
            print("💡 Check your .env.local file and API keys")
            return
        
        print("\n🔍 Detailed Portfolio Analysis")
        print("=" * 50)
        
        try:
            print("🔄 Analyzing portfolio performance...")
            summary = self.analyzer.get_portfolio_summary(self.portfolio)
            
            # Portfolio value analysis
            analysis = summary['portfolio_value']
            alerts = summary['price_alerts']
            benchmark = summary['benchmark_comparison']
            
            # Quick summary
            total_gain = analysis['total_gain_loss']
            total_pct = analysis['total_gain_loss_pct']
            gain_indicator = "🟢" if total_gain >= 0 else "🔴"
            gain_sign = "+" if total_gain >= 0 else ""
            
            print(f"\n📊 PORTFOLIO OVERVIEW")
            print("-" * 30)
            print(f"Total Value: ${analysis['current_value'] + analysis['cash']:.2f}")
            print(f"Performance: {gain_indicator} {gain_sign}${total_gain:.2f} ({gain_sign}{total_pct:.1f}%)")
            
            # Price alerts
            if alerts:
                print(f"\n🚨 ACTIVE PRICE ALERTS ({len(alerts)})")
                print("-" * 35)
                for alert in alerts:
                    severity_icon = "🔥" if alert['severity'] == 'high' else "⚠️"
                    change_sign = "+" if alert['change_pct'] > 0 else ""
                    print(f"{severity_icon} {alert['symbol']}: {change_sign}{alert['change_pct']:.1f}% "
                          f"(${alert['current_price']:.2f})")
                    print(f"   Position Impact: ${alert['position_value']:.2f}")
            else:
                print(f"\n✅ No significant price movements (>5% threshold)")
            
            # Benchmark comparison
            print(f"\n📈 BENCHMARK COMPARISON")
            print("-" * 30)
            portfolio_return = benchmark['portfolio_return_pct']
            benchmark_return = benchmark['benchmark_change_pct']
            benchmark_symbol = benchmark['benchmark_symbol']
            outperforming = benchmark['outperforming']
            
            print(f"Portfolio: {portfolio_return:+.1f}%")
            print(f"{benchmark_symbol}: {benchmark_return:+.1f}%")
            
            if outperforming:
                diff = benchmark['performance_difference']
                print(f"🎉 Outperforming by {diff:+.1f}%!")
            else:
                diff = abs(benchmark['performance_difference'])
                print(f"📉 Underperforming by {diff:.1f}%")
            
            # Top performers
            summary_data = summary['summary']
            if summary_data.get('biggest_gainer'):
                gainer = summary_data['biggest_gainer']
                print(f"\n🏆 Best Performer: {gainer['symbol']} ({gainer['gain_loss_pct']:+.1f}%)")
            
            if summary_data.get('biggest_loser'):
                loser = summary_data['biggest_loser']
                print(f"📉 Worst Performer: {loser['symbol']} ({loser['gain_loss_pct']:+.1f}%)")
            
            print(f"\n🕐 Analysis Time: {summary_data['analysis_timestamp'][:16]}")
            
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            print("💡 Try again in a few moments (API rate limits)")
    
    def check_price_alerts(self):
        """Check for price alerts only"""
        if not self.live_data_available:
            print("\n❌ Price alerts unavailable - API connections failed")
            return
        
        print("\n🚨 Price Alert Check")
        print("=" * 25)
        
        try:
            print("🔄 Checking for significant price movements...")
            alerts = self.analyzer.detect_price_alerts(self.portfolio)
            
            if alerts:
                print(f"🚨 Found {len(alerts)} price alerts:")
                for alert in alerts:
                    severity_icon = "🔥" if alert['severity'] == 'high' else "⚠️"
                    change_sign = "+" if alert['change_pct'] > 0 else ""
                    alert_type = "GAIN" if alert['change_pct'] > 0 else "LOSS"
                    
                    print(f"\n{severity_icon} {alert['symbol']} - {alert_type}")
                    print(f"   Change: {change_sign}{alert['change_pct']:.1f}%")
                    print(f"   Price: ${alert['current_price']:.2f}")
                    print(f"   Position Value: ${alert['position_value']:.2f}")
                    print(f"   Severity: {alert['severity'].upper()}")
            else:
                print("✅ No significant price movements detected")
                print("📊 All positions within normal ranges (<5% change)")
            
        except Exception as e:
            print(f"❌ Price alert check failed: {e}")
    
    def refresh_portfolio_data(self):
        """Update portfolio JSON with current market prices"""
        if not self.live_data_available:
            print("\n❌ Cannot refresh - API connections failed")
            return
        
        print("\n🔄 Refreshing Portfolio Data")
        print("=" * 35)
        
        try:
            print("📡 Fetching current market prices...")
            analysis = self.analyzer.get_current_portfolio_value(self.portfolio)
            
            # Update portfolio with current prices
            updated_count = 0
            for symbol, stock_data in analysis['stocks'].items():
                if symbol in self.portfolio['stocks']:
                    self.portfolio['stocks'][symbol]['current_price'] = stock_data['current_price']
                    self.portfolio['stocks'][symbol]['current_value'] = stock_data['current_value']
                    updated_count += 1
            
            # Save updated portfolio
            if self.config.save_portfolio(self.portfolio):
                print(f"✅ Updated {updated_count} stocks with current prices")
                print("💾 Portfolio data saved to portfolio.json")
            else:
                print("❌ Failed to save updated portfolio")
            
        except Exception as e:
            print(f"❌ Portfolio refresh failed: {e}")
    
    def update_cash(self):
        """Update available cash balance"""
        current_cash = self.portfolio.get('cash', {}).get('available', 0)
        print(f"\n💵 Update Cash Balance")
        print("-" * 25)
        print(f"Current cash: ${current_cash:.2f}")
        
        try:
            new_cash_input = input(f"New cash balance (${current_cash:.2f}): ").strip()
            new_cash = float(new_cash_input) if new_cash_input else current_cash
            
            if 'cash' not in self.portfolio:
                self.portfolio['cash'] = {}
            
            self.portfolio['cash']['available'] = new_cash
            self.portfolio['cash']['currency'] = 'USD'
            
            if self.config.save_portfolio(self.portfolio):
                print(f"✅ Updated cash balance to ${new_cash:.2f}")
            else:
                print("❌ Failed to save portfolio")
                
        except ValueError:
            print("❌ Invalid number format")
    
    def show_menu(self):
        """Display main menu"""
        print("\n" + "="*50)
        print("📊 Personal Portfolio Manager")
        print("="*50)
        
        if self.live_data_available:
            print("1. 📋 Show Portfolio")
            print("2. 🔍 Live Analysis")
            print("3. 🚨 Price Alerts")
            print("4. 🔄 Refresh Data")
            print("5. ➕ Add Stock")
            print("6. ➖ Remove Stock")
            print("7. ✏️ Update Stock")
            print("8. 💵 Update Cash")
            print("9. 🚪 Exit")
        else:
            print("1. 📋 Show Portfolio")
            print("2. ➕ Add Stock")
            print("3. ➖ Remove Stock") 
            print("4. ✏️ Update Stock")
            print("5. 💵 Update Cash")
            print("6. 🚪 Exit")
        print("-" * 50)
    
    def run(self):
        """Main CLI loop"""
        print("🚀 Welcome to Portfolio Manager with Live Analytics!")
        
        while True:
            self.show_menu()
            
            if self.live_data_available:
                choice = input("Enter your choice (1-9): ").strip()
                max_choice = 9
            else:
                choice = input("Enter your choice (1-6): ").strip()
                max_choice = 6
            
            if choice == '1':
                self.show_portfolio()
            elif choice == '2':
                if self.live_data_available:
                    self.show_live_analysis()
                else:
                    self.add_stock()
            elif choice == '3':
                if self.live_data_available:
                    self.check_price_alerts()
                else:
                    self.remove_stock()
            elif choice == '4':
                if self.live_data_available:
                    self.refresh_portfolio_data()
                else:
                    self.update_stock()
            elif choice == '5':
                if self.live_data_available:
                    self.add_stock()
                else:
                    self.update_cash()
            elif choice == '6':
                if self.live_data_available:
                    self.remove_stock()
                else:
                    print("👋 Goodbye!")
                    break
            elif choice == '7' and self.live_data_available:
                self.update_stock()
            elif choice == '8' and self.live_data_available:
                self.update_cash()
            elif choice == '9' and self.live_data_available:
                print("👋 Goodbye!")
                break
            else:
                print(f"❌ Invalid choice. Please enter 1-{max_choice}")
            
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    manager = PortfolioManager()
    manager.run()