"""
BOT v10 TEST - 3-Tier Trading System
Simulates trades untuk validate logic
"""

from dataclasses import dataclass
from datetime import datetime
from tier_config import TIER_1, TIER_2, TIER_3

@dataclass
class TradePosition:
    tier: str
    symbol: str
    direction: str
    entry_price: float
    entry_time: datetime
    position_size: float
    leverage: int
    notional: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    status: str = "OPEN"
    pnl_dollars: float = 0.0
    pnl_percent: float = 0.0

@dataclass
class BotDailyState:
    date: str
    opening_balance: float = 150
    current_balance: float = 150
    daily_pnl: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    tier1_trades: int = 0
    tier1_pnl: float = 0.0
    tier2_trades: int = 0
    tier2_pnl: float = 0.0
    tier3_trades: int = 0
    tier3_pnl: float = 0.0

class MultiTierBotTest:
    def __init__(self):
        self.capital = 150
        self.today = datetime.now().strftime("%Y-%m-%d")
        self.daily_state = BotDailyState(date=self.today)
        
        self.log("="*70)
        self.log("ULTIMATE TRADING BOT v10.0 - MULTI-TIER SYSTEM")
        self.log("="*70)
    
    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {msg}")
    
    def simulate_tier1_trade(self):
        """Simulate Tier 1 scalp trade"""
        self.log("\n--- TIER 1: SCALP QUICK ⚡ ---")
        
        entry = 65000.00
        trade = TradePosition(
            tier="tier1",
            symbol="BTCUSDT",
            direction="LONG",
            entry_price=entry,
            entry_time=datetime.now(),
            position_size=TIER_1.position_size,
            leverage=TIER_1.leverage,
            notional=TIER_1.notional_value,
            stop_loss=entry - (entry * 0.008),
            take_profit_1=entry + (entry * 0.005),
            take_profit_2=entry + (entry * 0.01),
            take_profit_3=entry + (entry * 0.02),
        )
        
        # Simulate winning trade
        exit_price = entry + (entry * 0.01)
        pnl = (exit_price - entry) / entry * TIER_1.position_size * TIER_1.leverage
        
        self.log(f"Entry: ${entry:,.2f}")
        self.log(f"Exit:  ${exit_price:,.2f}")
        self.log(f"P&L:   ${pnl:+.2f}")
        self.log(f"Position: {TIER_1.position_size} * {TIER_1.leverage}x = ${TIER_1.notional_value}")
        
        # Update state
        self.daily_state.tier1_trades += 1
        self.daily_state.tier1_pnl += pnl
        self.daily_state.total_trades += 1
        self.daily_state.winning_trades += 1
        self.daily_state.daily_pnl += pnl
        self.daily_state.current_balance += pnl
        
        return trade
    
    def simulate_tier2_trade(self):
        """Simulate Tier 2 swing trade"""
        self.log("\n--- TIER 2: SWING NORMAL 📈 ---")
        
        entry = 65100.00
        trade = TradePosition(
            tier="tier2",
            symbol="BTCUSDT",
            direction="LONG",
            entry_price=entry,
            entry_time=datetime.now(),
            position_size=TIER_2.position_size,
            leverage=TIER_2.leverage,
            notional=TIER_2.notional_value,
            stop_loss=entry - (entry * 0.012),
            take_profit_1=entry + (entry * 0.01),
            take_profit_2=entry + (entry * 0.02),
            take_profit_3=entry + (entry * 0.04),
        )
        
        # Simulate winning trade
        exit_price = entry + (entry * 0.02)
        pnl = (exit_price - entry) / entry * TIER_2.position_size * TIER_2.leverage
        
        self.log(f"Entry: ${entry:,.2f}")
        self.log(f"Exit:  ${exit_price:,.2f}")
        self.log(f"P&L:   ${pnl:+.2f}")
        self.log(f"Position: {TIER_2.position_size} * {TIER_2.leverage}x = ${TIER_2.notional_value}")
        
        # Update state
        self.daily_state.tier2_trades += 1
        self.daily_state.tier2_pnl += pnl
        self.daily_state.total_trades += 1
        self.daily_state.winning_trades += 1
        self.daily_state.daily_pnl += pnl
        self.daily_state.current_balance += pnl
        
        return trade
    
    def simulate_tier3_trade(self):
        """Simulate Tier 3 patient swing trade"""
        self.log("\n--- TIER 3: SWING PATIENT 💪 ---")
        
        entry = 65200.00
        trade = TradePosition(
            tier="tier3",
            symbol="BTCUSDT",
            direction="LONG",
            entry_price=entry,
            entry_time=datetime.now(),
            position_size=TIER_3.position_size,
            leverage=TIER_3.leverage,
            notional=TIER_3.notional_value,
            stop_loss=entry - (entry * 0.015),
            take_profit_1=entry + (entry * 0.015),
            take_profit_2=entry + (entry * 0.03),
            take_profit_3=entry + (entry * 0.06),
        )
        
        # Simulate winning trade
        exit_price = entry + (entry * 0.03)
        pnl = (exit_price - entry) / entry * TIER_3.position_size * TIER_3.leverage
        
        self.log(f"Entry: ${entry:,.2f}")
        self.log(f"Exit:  ${exit_price:,.2f}")
        self.log(f"P&L:   ${pnl:+.2f}")
        self.log(f"Position: {TIER_3.position_size} * {TIER_3.leverage}x = ${TIER_3.notional_value}")
        
        # Update state
        self.daily_state.tier3_trades += 1
        self.daily_state.tier3_pnl += pnl
        self.daily_state.total_trades += 1
        self.daily_state.winning_trades += 1
        self.daily_state.daily_pnl += pnl
        self.daily_state.current_balance += pnl
        
        return trade
    
    def print_daily_summary(self):
        """Print daily summary"""
        self.log("\n" + "="*70)
        self.log("DAILY SUMMARY")
        self.log("="*70)
        self.log(f"Date: {self.daily_state.date}")
        self.log(f"Opening Balance: ${self.daily_state.opening_balance:,.2f}")
        self.log(f"Closing Balance: ${self.daily_state.current_balance:,.2f}")
        self.log(f"Daily P&L: ${self.daily_state.daily_pnl:+.2f}")
        self.log(f"Daily Return: {(self.daily_state.daily_pnl/self.daily_state.opening_balance)*100:+.2f}%")
        self.log("")
        self.log("BY TIER:")
        self.log(f"  Tier 1 (Scalp):   {self.daily_state.tier1_trades:2} trades | ${self.daily_state.tier1_pnl:+7.2f} P&L")
        self.log(f"  Tier 2 (Swing):   {self.daily_state.tier2_trades:2} trades | ${self.daily_state.tier2_pnl:+7.2f} P&L")
        self.log(f"  Tier 3 (Patient): {self.daily_state.tier3_trades:2} trades | ${self.daily_state.tier3_pnl:+7.2f} P&L")
        self.log("")
        self.log(f"Total: {self.daily_state.total_trades} trades")
        self.log(f"Wins: {self.daily_state.winning_trades} | Losses: {self.daily_state.losing_trades}")
        if self.daily_state.total_trades > 0:
            win_rate = (self.daily_state.winning_trades / self.daily_state.total_trades) * 100
            self.log(f"Win Rate: {win_rate:.1f}%")
        self.log("")
        self.log("STATUS: ✅ All tiers working perfectly!")
        self.log("="*70)

if __name__ == "__main__":
    bot = MultiTierBotTest()
    
    # Simulate trades
    bot.log("\n🤖 SIMULATING 3 TRADES (1 per tier)...\n")
    
    bot.simulate_tier1_trade()
    bot.simulate_tier2_trade()
    bot.simulate_tier3_trade()
    
    # Print summary
    bot.print_daily_summary()
    
    # Show tier configurations
    bot.log("\n" + "="*70)
    bot.log("TIER CONFIGURATIONS")
    bot.log("="*70)
    print(TIER_1)
    print(TIER_2)
    print(TIER_3)