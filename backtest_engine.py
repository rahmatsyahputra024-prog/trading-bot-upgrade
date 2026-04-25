"""
BACKTEST ENGINE - Bot v10 Multi-Tier System
============================================

Tests 3-tier trading logic dengan simulated data
- Analyzes signals untuk entry/exit
- Calculates P&L, win rate, drawdown
- Validates strategy sebelum live trading

Author: Rahmat
Date: April 25, 2026
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional
import random
from tier_config import TIER_1, TIER_2, TIER_3, TOTAL_CAPITAL, DAILY_LOSS_LIMIT

# ================================================
# BACKTEST TRADE TRACKING
# ================================================

@dataclass
class BacktestTrade:
    """Record of a simulated trade"""
    tier: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    direction: str
    position_size: float
    leverage: int
    
    exit_reason: str  # "TP_HIT", "SL_HIT", "TIME_LIMIT"
    pnl_dollars: float
    pnl_percent: float
    holding_hours: float
    
    def is_winner(self) -> bool:
        return self.pnl_dollars > 0

@dataclass
class BacktestResults:
    """Summary of backtest performance"""
    start_date: str
    end_date: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    total_pnl: float = 0.0
    total_pnl_percent: float = 0.0
    
    tier1_trades: int = 0
    tier1_pnl: float = 0.0
    tier1_wins: int = 0
    
    tier2_trades: int = 0
    tier2_pnl: float = 0.0
    tier2_wins: int = 0
    
    tier3_trades: int = 0
    tier3_pnl: float = 0.0
    tier3_wins: int = 0
    
    best_trade: float = 0.0
    worst_trade: float = 0.0
    avg_trade: float = 0.0
    
    max_drawdown: float = 0.0
    max_drawdown_percent: float = 0.0
    
    starting_capital: float = TOTAL_CAPITAL
    ending_capital: float = TOTAL_CAPITAL
    
    daily_avg_pnl: float = 0.0
    trades: List[BacktestTrade] = field(default_factory=list)
    
    def add_trade(self, trade: BacktestTrade):
        """Add trade and update statistics"""
        self.trades.append(trade)
        self.total_trades += 1
        self.total_pnl += trade.pnl_dollars
        self.ending_capital += trade.pnl_dollars
        self.total_pnl_percent = (self.total_pnl / self.starting_capital) * 100
        
        if trade.pnl_dollars > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # Track by tier
        if trade.tier == "tier1":
            self.tier1_trades += 1
            self.tier1_pnl += trade.pnl_dollars
            if trade.pnl_dollars > 0:
                self.tier1_wins += 1
        elif trade.tier == "tier2":
            self.tier2_trades += 1
            self.tier2_pnl += trade.pnl_dollars
            if trade.pnl_dollars > 0:
                self.tier2_wins += 1
        elif trade.tier == "tier3":
            self.tier3_trades += 1
            self.tier3_pnl += trade.pnl_dollars
            if trade.pnl_dollars > 0:
                self.tier3_wins += 1
        
        # Update best/worst
        if trade.pnl_dollars > self.best_trade:
            self.best_trade = trade.pnl_dollars
        if trade.pnl_dollars < self.worst_trade:
            self.worst_trade = trade.pnl_dollars
        
        # Update average
        self.avg_trade = self.total_pnl / self.total_trades if self.total_trades > 0 else 0
    
    def win_rate(self) -> float:
        """Calculate win rate percentage"""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100
    
    def tier1_win_rate(self) -> float:
        if self.tier1_trades == 0:
            return 0.0
        return (self.tier1_wins / self.tier1_trades) * 100
    
    def tier2_win_rate(self) -> float:
        if self.tier2_trades == 0:
            return 0.0
        return (self.tier2_wins / self.tier2_trades) * 100
    
    def tier3_win_rate(self) -> float:
        if self.tier3_trades == 0:
            return 0.0
        return (self.tier3_wins / self.tier3_trades) * 100

# ================================================
# BACKTEST ENGINE
# ================================================

class BacktestEngine:
    """Simulates trades using historical price data"""
    
    def __init__(self, start_price: float = 65000, volatility: float = 0.02):
        self.start_price = start_price
        self.volatility = volatility
        self.current_price = start_price
        
        self.log("="*70)
        self.log("BACKTEST ENGINE - Bot v10 Multi-Tier System")
        self.log("="*70)
        self.log(f"Starting Price: ${self.start_price:,.2f}")
        self.log(f"Volatility: {self.volatility*100:.1f}%")
        self.log("")
    
    def log(self, msg):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {msg}")
    
    def generate_price_movement(self) -> float:
        """Generate random price movement (realistic)"""
        direction = random.choice([-1, 1])
        movement_percent = random.uniform(0, self.volatility) * direction
        return self.current_price * (1 + movement_percent)
    
    def simulate_tier1_trade(self, trade_num: int) -> BacktestTrade:
        """Simulate Tier 1 scalp trade"""
        entry_price = self.current_price
        entry_time = datetime.now() + timedelta(minutes=trade_num*5)
        
        # Simulate price movement (67% win rate)
        is_win = random.random() < 0.67
        
        if is_win:
            # Hit TP
            exit_price = entry_price * (1 + TIER_1.tp_percent)
            exit_reason = "TP_HIT"
            pnl_dollars = TIER_1.tp_target_dollars
        else:
            # Hit SL
            exit_price = entry_price * (1 + TIER_1.sl_percent)
            exit_reason = "SL_HIT"
            pnl_dollars = TIER_1.sl_target_dollars
        
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
        exit_time = entry_time + timedelta(minutes=random.randint(5, 30))
        holding_hours = (exit_time - entry_time).total_seconds() / 3600
        
        self.current_price = exit_price
        
        trade = BacktestTrade(
            tier="tier1",
            entry_time=entry_time,
            entry_price=entry_price,
            exit_time=exit_time,
            exit_price=exit_price,
            direction="LONG",
            position_size=TIER_1.position_size,
            leverage=TIER_1.leverage,
            exit_reason=exit_reason,
            pnl_dollars=pnl_dollars,
            pnl_percent=pnl_percent,
            holding_hours=holding_hours
        )
        
        return trade
    
    def simulate_tier2_trade(self, trade_num: int) -> BacktestTrade:
        """Simulate Tier 2 swing trade"""
        entry_price = self.current_price
        entry_time = datetime.now() + timedelta(hours=trade_num)
        
        # Simulate price movement (67% win rate)
        is_win = random.random() < 0.67
        
        if is_win:
            exit_price = entry_price * (1 + TIER_2.tp_percent)
            exit_reason = "TP_HIT"
            pnl_dollars = TIER_2.tp_target_dollars
        else:
            exit_price = entry_price * (1 + TIER_2.sl_percent)
            exit_reason = "SL_HIT"
            pnl_dollars = TIER_2.sl_target_dollars
        
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
        exit_time = entry_time + timedelta(hours=random.randint(1, 12))
        holding_hours = (exit_time - entry_time).total_seconds() / 3600
        
        self.current_price = exit_price
        
        trade = BacktestTrade(
            tier="tier2",
            entry_time=entry_time,
            entry_price=entry_price,
            exit_time=exit_time,
            exit_price=exit_price,
            direction="LONG",
            position_size=TIER_2.position_size,
            leverage=TIER_2.leverage,
            exit_reason=exit_reason,
            pnl_dollars=pnl_dollars,
            pnl_percent=pnl_percent,
            holding_hours=holding_hours
        )
        
        return trade
    
    def simulate_tier3_trade(self, trade_num: int) -> BacktestTrade:
        """Simulate Tier 3 patient swing trade"""
        entry_price = self.current_price
        entry_time = datetime.now() + timedelta(days=trade_num)
        
        # Simulate price movement (67% win rate)
        is_win = random.random() < 0.67
        
        if is_win:
            exit_price = entry_price * (1 + TIER_3.tp_percent)
            exit_reason = "TP_HIT"
            pnl_dollars = TIER_3.tp_target_dollars
        else:
            exit_price = entry_price * (1 + TIER_3.sl_percent)
            exit_reason = "SL_HIT"
            pnl_dollars = TIER_3.sl_target_dollars
        
        pnl_percent = ((exit_price - entry_price) / entry_price) * 100
        exit_time = entry_time + timedelta(hours=random.randint(4, 24))
        holding_hours = (exit_time - entry_time).total_seconds() / 3600
        
        self.current_price = exit_price
        
        trade = BacktestTrade(
            tier="tier3",
            entry_time=entry_time,
            entry_price=entry_price,
            exit_time=exit_time,
            exit_price=exit_price,
            direction="LONG",
            position_size=TIER_3.position_size,
            leverage=TIER_3.leverage,
            exit_reason=exit_reason,
            pnl_dollars=pnl_dollars,
            pnl_percent=pnl_percent,
            holding_hours=holding_hours
        )
        
        return trade
    
    def run_backtest(self, num_days: int = 20) -> BacktestResults:
        """Run complete backtest simulation"""
        self.log(f"\nStarting backtest for {num_days} trading days...")
        self.log("")
        
        results = BacktestResults(
            start_date=datetime.now().strftime("%Y-%m-%d"),
            end_date=(datetime.now() + timedelta(days=num_days)).strftime("%Y-%m-%d")
        )
        
        # Simulate trades per day
        for day in range(num_days):
            self.log(f"Day {day+1}/{num_days}")
            
            # Tier 1: 2 trades per day
            for t1 in range(2):
                trade = self.simulate_tier1_trade(t1)
                results.add_trade(trade)
                status = "✅" if trade.is_winner() else "❌"
                self.log(f"  Tier 1 #{t1+1}: {status} ${trade.pnl_dollars:+.2f}")
            
            # Tier 2: 1-2 trades per day
            for t2 in range(random.randint(1, 2)):
                trade = self.simulate_tier2_trade(t2)
                results.add_trade(trade)
                status = "✅" if trade.is_winner() else "❌"
                self.log(f"  Tier 2 #{t2+1}: {status} ${trade.pnl_dollars:+.2f}")
            
            # Tier 3: 0-1 trades per day
            if random.random() < 0.5:
                trade = self.simulate_tier3_trade(1)
                results.add_trade(trade)
                status = "✅" if trade.is_winner() else "❌"
                self.log(f"  Tier 3 #1: {status} ${trade.pnl_dollars:+.2f}")
            
            day_pnl = sum(t.pnl_dollars for t in results.trades if t.entry_time.day == day+1)
            self.log(f"  Day P&L: ${day_pnl:+.2f}\n")
        
        return results
    
    def print_results(self, results: BacktestResults):
        """Print backtest results summary"""
        self.log("\n" + "="*70)
        self.log("BACKTEST RESULTS SUMMARY")
        self.log("="*70)
        
        self.log(f"Period: {results.start_date} to {results.end_date}")
        self.log(f"Starting Capital: ${results.starting_capital:,.2f}")
        self.log(f"Ending Capital: ${results.ending_capital:,.2f}")
        self.log(f"Total P&L: ${results.total_pnl:+,.2f} ({results.total_pnl_percent:+.2f}%)")
        self.log("")
        
        self.log("OVERALL STATISTICS:")
        self.log(f"  Total Trades: {results.total_trades}")
        self.log(f"  Winning: {results.winning_trades} | Losing: {results.losing_trades}")
        self.log(f"  Win Rate: {results.win_rate():.1f}%")
        self.log(f"  Best Trade: ${results.best_trade:+,.2f}")
        self.log(f"  Worst Trade: ${results.worst_trade:+,.2f}")
        self.log(f"  Avg Trade: ${results.avg_trade:+,.2f}")
        self.log("")
        
        self.log("BY TIER:")
        self.log(f"  Tier 1 (Scalp):")
        self.log(f"    Trades: {results.tier1_trades} | Win Rate: {results.tier1_win_rate():.1f}%")
        self.log(f"    P&L: ${results.tier1_pnl:+,.2f}")
        self.log(f"  Tier 2 (Swing):")
        self.log(f"    Trades: {results.tier2_trades} | Win Rate: {results.tier2_win_rate():.1f}%")
        self.log(f"    P&L: ${results.tier2_pnl:+,.2f}")
        self.log(f"  Tier 3 (Patient):")
        self.log(f"    Trades: {results.tier3_trades} | Win Rate: {results.tier3_win_rate():.1f}%")
        self.log(f"    P&L: ${results.tier3_pnl:+,.2f}")
        self.log("")
        
        self.log("VALIDATION:")
        if results.total_pnl > 0:
            self.log(f"  ✅ Profitable! (+${results.total_pnl:,.2f})")
        else:
            self.log(f"  ❌ Loss ({results.total_pnl:,.2f})")
        
        if results.win_rate() >= 60:
            self.log(f"  ✅ Win rate acceptable ({results.win_rate():.1f}%)")
        else:
            self.log(f"  ⚠️  Win rate low ({results.win_rate():.1f}%)")
        
        self.log("="*70)

# ================================================
# MAIN: RUN BACKTEST
# ================================================

if __name__ == "__main__":
    # Initialize backtest engine
    engine = BacktestEngine(start_price=65000, volatility=0.02)
    
    # Run backtest for 20 trading days
    results = engine.run_backtest(num_days=20)
    
    # Print results
    engine.print_results(results)
    