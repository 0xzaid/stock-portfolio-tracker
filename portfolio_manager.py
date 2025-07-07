#!/usr/bin/env python3
"""
Interactive Portfolio Manager CLI
Manage your stock holdings with add/remove/show commands
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.config_loader import ConfigLoader

class PortfolioManager:
    def __init__(self):
        self.config = ConfigLoader()
        self.portfolio = self.config.load_portfolio()
    
    def show_portfolio(self):
        """Display current portfolio with gains/losses"""
        stocks = self.portfolio.get('stocks', {})
        cash = self.portfolio.get('cash', {})
        
        if not stocks:
            print("\n📊 Portfolio is empty")
            print("Use 'Add Stock' to get started!")
            return
        
        print(f"\n📊 Portfolio Summary")
        print("=" * 80)
        
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
        print("1. 📋 Show Portfolio")
        print("2. ➕ Add Stock")
        print("3. ➖ Remove Stock") 
        print("4. ✏️ Update Stock")
        print("5. 💵 Update Cash")
        print("6. 🚪 Exit")
        print("-" * 30)
    
    def run(self):
        """Main CLI loop"""
        print("🚀 Welcome to Portfolio Manager!")
        
        while True:
            self.show_menu()
            choice = input("Enter your choice (1-6): ").strip()
            
            if choice == '1':
                self.show_portfolio()
            elif choice == '2':
                self.add_stock()
            elif choice == '3':
                self.remove_stock()
            elif choice == '4':
                self.update_stock()
            elif choice == '5':
                self.update_cash()
            elif choice == '6':
                print("👋 Goodbye!")
                break
            else:
                print("❌ Invalid choice. Please enter 1-6")
            
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    manager = PortfolioManager()
    manager.run()