# TIER CONFIGURATION - Multi-Tier Trading Bot
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class TierConfig:
    """Configuration for each trading tier"""
    name: str
    timeframe: str
    position_size: float
    allocation_percent: float
    leverage: int
    notional_value: float
    
    entry_min_signals: int
    entry_signals: List[str]
    
    tp_percent: float
    sl_percent: float
    tp_target_dollars: float
    sl_target_dollars: float
    
    min_hold_minutes: int
    max_hold_minutes: int
    expected_signals_per_day: float
    
    win_rate_target: float
    rr_ratio: float
    
    daily_expected_profit: float
    
    def __str__(self):
        return f"""
╔════════════════════════════════════════╗
║ TIER: {self.name:^34} ║
╠════════════════════════════════════════╣
║ Timeframe:        {self.timeframe:^21} ║
║ Position Size:    ${self.position_size:^19.0f} ║
║ Allocation:       {self.allocation_percent:^20.0f}% ║
║ Leverage:         {self.leverage:^21}x ║
║ Notional:         ${self.notional_value:^19.0f} ║
║                                        ║
║ TP Target:        +{self.tp_percent*100:^19.1f}% ║
║ SL Target:        {self.sl_percent*100:^19.1f}% ║
║ Hold:             {self.min_hold_minutes:^7}-{self.max_hold_minutes:^12} mins ║
║ Signals/Day:      {self.expected_signals_per_day:^20.1f}x ║
║ Daily Expected:   ${self.daily_expected_profit:^18.2f} ║
║ Win Rate Target:  {self.win_rate_target:^20.0f}% ║
║ R/R Ratio:        1:{self.rr_ratio:^18.1f} ║
╚════════════════════════════════════════╝
"""

# TIER 1: SCALP QUICK ⚡
TIER_1 = TierConfig(
    name="SCALP QUICK ⚡",
    timeframe="5m",
    position_size=30,
    allocation_percent=20,
    leverage=5,
    notional_value=150,
    
    entry_min_signals=3,
    entry_signals=["EMA 9 > 21", "RSI > 50", "Volume > SMA"],
    
    tp_percent=0.01,
    sl_percent=-0.008,
    tp_target_dollars=1.50,
    sl_target_dollars=-1.20,
    
    min_hold_minutes=5,
    max_hold_minutes=30,
    expected_signals_per_day=2.0,
    
    win_rate_target=67,
    rr_ratio=1.25,
    
    daily_expected_profit=1.50,
)

# TIER 2: SWING NORMAL 📈
TIER_2 = TierConfig(
    name="SWING NORMAL 📈",
    timeframe="1h",
    position_size=60,
    allocation_percent=40,
    leverage=5,
    notional_value=300,
    
    entry_min_signals=2,
    entry_signals=["1H EMA 50 > 200", "4H Support bounce", "Volume > SMA"],
    
    tp_percent=0.02,
    sl_percent=-0.012,
    tp_target_dollars=6.00,
    sl_target_dollars=-3.60,
    
    min_hold_minutes=60,
    max_hold_minutes=720,
    expected_signals_per_day=1.5,
    
    win_rate_target=67,
    rr_ratio=1.67,
    
    daily_expected_profit=3.60,
)

# TIER 3: SWING PATIENT 💪
TIER_3 = TierConfig(
    name="SWING PATIENT 💪",
    timeframe="4h",
    position_size=60,
    allocation_percent=40,
    leverage=5,
    notional_value=300,
    
    entry_min_signals=2,
    entry_signals=["Daily EMA 50 > 200", "4H break", "Volume spike"],
    
    tp_percent=0.03,
    sl_percent=-0.015,
    tp_target_dollars=9.00,
    sl_target_dollars=-4.50,
    
    min_hold_minutes=240,
    max_hold_minutes=1440,
    expected_signals_per_day=0.75,
    
    win_rate_target=67,
    rr_ratio=2.00,
    
    daily_expected_profit=3.15,
)

TOTAL_CAPITAL = 150
DAILY_LOSS_LIMIT = 30

if __name__ == "__main__":
    print("\n3-TIER BOT CONFIGURATION\n")
    print(TIER_1)
    print(TIER_2)
    print(TIER_3)
    print(f"\nDaily Expected: ${TIER_1.daily_expected_profit + TIER_2.daily_expected_profit + TIER_3.daily_expected_profit:.2f}")
    