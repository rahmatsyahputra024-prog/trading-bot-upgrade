"""
BOT V10 FUTURES - Automated Trading Bot
========================================

FINAL STRATEGY:
- Modal: $5,799.74 USDT (Binance Futures Testnet)
- Leverage: 5x per tier (tier-specific SL!)
- Margin: 25% ($1,449.94)
- Buffer: 75% ($4,349.81)

3-Tier System:
├─ Tier 1: Scalp 5M (A+ only, SL $50)
├─ Tier 2: Swing 1H (A+/A, SL $100)
└─ Tier 3: Patient 4H (A+/A, SL $150)

Daily Max Loss: -$300 (hard stop!)
Signal Grade: A+ = 18-20, A = 14-17 (only trade these!)

FUTURES-SPECIFIC:
- 5x leverage per tier
- Liquidation monitoring
- Margin ratio tracking
- Emergency close-all logic
- Position sizing formula
"""

import os
import time
import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, asdict

import requests
from binance.um_futures import UMFutures
from binance.lib.utils import config_logging

from tier_config import TIER_1, TIER_2, TIER_3, TOTAL_CAPITAL, DAILY_LOSS_LIMIT
from signal_scorer import SignalScorer

# ================================================
# LOGGING SETUP
# ================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_v10_futures.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BOT_V10_FUTURES')

# ================================================
# CONFIGURATION
# ================================================

BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '')
NTFY_CHANNEL = os.getenv('NTFY_CHANNEL', 'Mamat-trading')
USE_TESTNET = os.getenv('USE_TESTNET', 'True').lower() == 'true'

SYMBOL = 'BTCUSDT'
TRADING_MODE = 'TESTNET' if USE_TESTNET else 'LIVE'

# ================================================
# DATA MODELS
# ================================================

@dataclass
class Position:
    """Open futures position"""
    tier: str
    entry_price: float
    entry_qty: float
    entry_time: str
    tp_price: float
    sl_price: float
    position_id: str
    max_loss: float
    leverage: float
    status: str = "OPEN"

@dataclass
class DailyStats:
    """Daily trading statistics"""
    date: str
    opening_balance: float
    current_balance: float
    daily_pnl: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    margin_used: float = 0.0
    margin_available: float = 0.0

# ================================================
# BOT ENGINE
# ================================================

class BotV10Futures:
    """Main futures trading bot with tier-specific SL"""
    
    def __init__(self):
        self.symbol = SYMBOL
        self.client = UMFutures(
            key=BINANCE_API_KEY,
            secret=BINANCE_SECRET_KEY,
            base_url='https://testnet.binancefuture.com' if USE_TESTNET else 'https://fapi.binance.com'
        )
        self.scorer = SignalScorer()
        
        self.open_positions: List[Position] = []
        self.daily_stats = DailyStats(date=datetime.now().strftime("%Y-%m-%d"), opening_balance=TOTAL_CAPITAL)
        self.session_start = datetime.now()
        
        self.log("="*80)
        self.log("BOT V10 FUTURES - Automated Trading System")
        self.log("="*80)
        self.log(f"Symbol: {self.symbol}")
        self.log(f"Mode: {TRADING_MODE}")
        self.log(f"Capital: ${TOTAL_CAPITAL:,.2f}")
        self.log(f"Margin (25%): ${TOTAL_CAPITAL * 0.25:,.2f}")
        self.log(f"Buffer (75%): ${TOTAL_CAPITAL * 0.75:,.2f}")
        self.log(f"Daily Loss Limit: -$300")
        self.log(f"Leverage: 5x per tier")
        self.log("")
    
    def log(self, msg: str):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {msg}")
        logger.info(msg)
    
    def send_ntfy(self, title: str, message: str):
        """Send Ntfy notification"""
        try:
            url = f"https://ntfy.sh/{NTFY_CHANNEL}"
            requests.post(
                url,
                data=message,
                headers={"Title": title},
                timeout=5
            )
        except Exception as e:
            self.log(f"❌ Ntfy error: {e}")
    
    def get_price(self) -> float:
        """Get current price"""
        try:
            ticker = self.client.mark_price(self.symbol)
            return float(ticker['markPrice'])
        except Exception as e:
            self.log(f"❌ Error getting price: {e}")
            return 0.0
    
    def get_klines(self, interval: str, limit: int = 100) -> List:
        """Get historical klines for signal analysis"""
        try:
            klines = self.client.klines(self.symbol, interval, limit=limit)
            return klines
        except Exception as e:
            self.log(f"❌ Error getting klines: {e}")
            return []
    
    def calculate_indicators(self, klines: List) -> Dict:
        """Calculate indicators from klines"""
        if not klines or len(klines) < 50:
            return {}
        
        closes = [float(k[4]) for k in klines]
        volumes = [float(k[7]) for k in klines]
        
        # EMA
        ema_9 = sum(closes[-9:]) / 9
        ema_21 = sum(closes[-21:]) / 21
        ema_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else 0
        ema_200 = sum(closes[-50:]) / 50  # Simplified
        
        # RSI
        deltas = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gains = sum([d for d in deltas if d > 0]) / 14
        losses = sum([abs(d) for d in deltas if d < 0]) / 14
        rs = gains / losses if losses > 0 else 0
        rsi = 100 - (100 / (1 + rs)) if rs >= 0 else 50
        
        # MACD
        ema_12 = sum(closes[-12:]) / 12
        ema_26 = sum(closes[-26:]) / 26 if len(closes) >= 26 else ema_12
        macd = ema_12 - ema_26
        signal = macd * 0.666
        
        # Volume
        avg_volume = sum(volumes[-20:]) / 20
        current_volume = volumes[-1]
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        return {
            'close': closes[-1],
            'ema_9': ema_9,
            'ema_21': ema_21,
            'ema_50': ema_50,
            'ema_200': ema_200,
            'rsi': rsi,
            'macd': macd,
            'macd_signal': signal,
            'volume_ratio': volume_ratio,
            'at_support': False,
            'bounce': False,
        }
    
    def check_tier1_signal(self) -> Optional[Dict]:
        """Check Tier 1 (5M) signal - A+ ONLY!"""
        klines = self.get_klines('5m', 100)
        if not klines:
            return None
        
        indicators = self.calculate_indicators(klines)
        result = self.scorer.analyze(indicators)
        
        # ONLY A+ for Tier 1!
        if result['grade'] == 'A+':
            return {
                'tier': 'tier1',
                'score': result['score'],
                'grade': result['grade'],
                'indicators': indicators
            }
        return None
    
    def check_tier2_signal(self) -> Optional[Dict]:
        """Check Tier 2 (1H) signal - A+ or A"""
        klines = self.get_klines('1h', 100)
        if not klines:
            return None
        
        indicators = self.calculate_indicators(klines)
        result = self.scorer.analyze(indicators)
        
        # A+ or A for Tier 2
        if result['grade'] in ['A+', 'A']:
            return {
                'tier': 'tier2',
                'score': result['score'],
                'grade': result['grade'],
                'indicators': indicators
            }
        return None
    
    def check_tier3_signal(self) -> Optional[Dict]:
        """Check Tier 3 (4H) signal - A+ or A"""
        klines = self.get_klines('4h', 100)
        if not klines:
            return None
        
        indicators = self.calculate_indicators(klines)
        result = self.scorer.analyze(indicators)
        
        # A+ or A for Tier 3
        if result['grade'] in ['A+', 'A']:
            return {
                'tier': 'tier3',
                'score': result['score'],
                'grade': result['grade'],
                'indicators': indicators
            }
        return None
    
    def execute_tier1_trade(self):
        """Execute Tier 1 trade (A+ only, SL $50)"""
        signal = self.check_tier1_signal()
        if not signal or len([p for p in self.open_positions if p.tier == 'tier1']) > 0:
            return
        
        current_price = self.get_price()
        if current_price == 0:
            return
        
        self.log(f"\n🚀 TIER 1 SIGNAL (A+)! Score: {signal['score']}/20")
        self.log(f"Price: ${current_price:,.2f}")
        
        position_size = TIER_1['position_size']
        leverage = TIER_1['leverage']
        notional = position_size * leverage
        max_loss = 50  # $50 max loss
        sl_percent = max_loss / notional
        
        tp_price = current_price * (1 + TIER_1['tp_percent'])
        sl_price = current_price * (1 - sl_percent)
        
        self.log(f"Position: ${position_size} × {leverage}x = ${notional}")
        self.log(f"Max Loss: -${max_loss} ({-sl_percent*100:.2f}%)")
        self.log(f"TP: ${tp_price:,.2f} (+{TIER_1['tp_percent']*100:.1f}%)")
        self.log(f"SL: ${sl_price:,.2f} (-{sl_percent*100:.2f}%)")
        
        position = Position(
            tier='tier1',
            entry_price=current_price,
            entry_qty=notional / current_price,
            entry_time=datetime.now().isoformat(),
            tp_price=tp_price,
            sl_price=sl_price,
            position_id=f"tier1_{int(time.time())}",
            max_loss=max_loss,
            leverage=leverage
        )
        self.open_positions.append(position)
        
        msg = f"Tier 1 Scalp (5M) - A+ Signal\nPrice: ${current_price:,.2f}\nTP: ${tp_price:,.2f}\nSL: ${sl_price:,.2f}\nMax Loss: -${max_loss}"
        self.send_ntfy("🚀 TIER 1 ENTRY (A+)", msg)
    
    def execute_tier2_trade(self):
        """Execute Tier 2 trade (A+/A, SL $100)"""
        signal = self.check_tier2_signal()
        if not signal or len([p for p in self.open_positions if p.tier == 'tier2']) > 0:
            return
        
        current_price = self.get_price()
        if current_price == 0:
            return
        
        self.log(f"\n📈 TIER 2 SIGNAL ({signal['grade']})! Score: {signal['score']}/20")
        self.log(f"Price: ${current_price:,.2f}")
        
        position_size = TIER_2['position_size']
        leverage = TIER_2['leverage']
        notional = position_size * leverage
        max_loss = 100  # $100 max loss
        sl_percent = max_loss / notional
        
        tp_price = current_price * (1 + TIER_2['tp_percent'])
        sl_price = current_price * (1 - sl_percent)
        
        self.log(f"Position: ${position_size} × {leverage}x = ${notional}")
        self.log(f"Max Loss: -${max_loss} ({-sl_percent*100:.2f}%)")
        self.log(f"TP: ${tp_price:,.2f} (+{TIER_2['tp_percent']*100:.1f}%)")
        self.log(f"SL: ${sl_price:,.2f} (-{sl_percent*100:.2f}%)")
        
        position = Position(
            tier='tier2',
            entry_price=current_price,
            entry_qty=notional / current_price,
            entry_time=datetime.now().isoformat(),
            tp_price=tp_price,
            sl_price=sl_price,
            position_id=f"tier2_{int(time.time())}",
            max_loss=max_loss,
            leverage=leverage
        )
        self.open_positions.append(position)
        
        msg = f"Tier 2 Swing (1H) - {signal['grade']} Signal\nPrice: ${current_price:,.2f}\nTP: ${tp_price:,.2f}\nSL: ${sl_price:,.2f}\nMax Loss: -${max_loss}"
        self.send_ntfy(f"📈 TIER 2 ENTRY ({signal['grade']})", msg)
    
    def execute_tier3_trade(self):
        """Execute Tier 3 trade (A+/A, SL $150)"""
        signal = self.check_tier3_signal()
        if not signal or len([p for p in self.open_positions if p.tier == 'tier3']) > 0:
            return
        
        current_price = self.get_price()
        if current_price == 0:
            return
        
        self.log(f"\n💪 TIER 3 SIGNAL ({signal['grade']})! Score: {signal['score']}/20")
        self.log(f"Price: ${current_price:,.2f}")
        
        position_size = TIER_3['position_size']
        leverage = TIER_3['leverage']
        notional = position_size * leverage
        max_loss = 150  # $150 max loss
        sl_percent = max_loss / notional
        
        tp_price = current_price * (1 + TIER_3['tp_percent'])
        sl_price = current_price * (1 - sl_percent)
        
        self.log(f"Position: ${position_size} × {leverage}x = ${notional}")
        self.log(f"Max Loss: -${max_loss} ({-sl_percent*100:.2f}%)")
        self.log(f"TP: ${tp_price:,.2f} (+{TIER_3['tp_percent']*100:.1f}%)")
        self.log(f"SL: ${sl_price:,.2f} (-{sl_percent*100:.2f}%)")
        
        position = Position(
            tier='tier3',
            entry_price=current_price,
            entry_qty=notional / current_price,
            entry_time=datetime.now().isoformat(),
            tp_price=tp_price,
            sl_price=sl_price,
            position_id=f"tier3_{int(time.time())}",
            max_loss=max_loss,
            leverage=leverage
        )
        self.open_positions.append(position)
        
        msg = f"Tier 3 Patient (4H) - {signal['grade']} Signal\nPrice: ${current_price:,.2f}\nTP: ${tp_price:,.2f}\nSL: ${sl_price:,.2f}\nMax Loss: -${max_loss}"
        self.send_ntfy(f"💪 TIER 3 ENTRY ({signal['grade']})", msg)
    
    def monitor_positions(self):
        """Monitor open positions for TP/SL"""
        current_price = self.get_price()
        if current_price == 0:
            return
        
        for position in self.open_positions[:]:
            # Check TP
            if current_price >= position.tp_price:
                pnl = position.tp_price - position.entry_price
                profit = pnl * position.entry_qty
                self.log(f"✅ {position.tier.upper()} TP HIT! Profit: +${profit:.2f}")
                self.daily_stats.daily_pnl += profit
                self.daily_stats.winning_trades += 1
                self.open_positions.remove(position)
                self.send_ntfy(f"✅ {position.tier.upper()} TP HIT", f"Profit: +${profit:.2f}")
            
            # Check SL
            elif current_price <= position.sl_price:
                pnl = position.sl_price - position.entry_price
                loss = pnl * position.entry_qty
                self.log(f"❌ {position.tier.upper()} SL HIT! Loss: ${loss:.2f}")
                self.daily_stats.daily_pnl += loss
                self.daily_stats.losing_trades += 1
                self.open_positions.remove(position)
                self.send_ntfy(f"❌ {position.tier.upper()} SL HIT", f"Loss: ${loss:.2f}")
    
    def check_daily_loss_limit(self) -> bool:
        """Check if daily loss limit exceeded"""
        if self.daily_stats.daily_pnl <= -300:  # Daily max loss: $300
            self.log(f"\n⚠️  DAILY LOSS LIMIT HIT! P&L: ${self.daily_stats.daily_pnl:.2f}")
            self.send_ntfy("⚠️  DAILY LOSS LIMIT", f"P&L: ${self.daily_stats.daily_pnl:.2f}\nSTOP ALL TRADES!")
            return False
        return True
    
    def check_margin_ratio(self) -> bool:
        """Check margin ratio and liquidation risk"""
        try:
            account = self.client.account()
            total_wallet_balance = float(account['totalWalletBalance'])
            total_margin_balance = float(account['totalMarginBalance'])
            
            # Calculate margin ratio
            if total_wallet_balance > 0:
                margin_ratio = (total_margin_balance / total_wallet_balance) * 100
                self.log(f"Margin Ratio: {margin_ratio:.2f}%")
                
                if margin_ratio < 100:
                    self.log("⚠️  WARNING: Margin ratio < 100%! Risk of liquidation!")
                    self.send_ntfy("⚠️  MARGIN WARNING", f"Margin ratio: {margin_ratio:.2f}%\nClose positions!")
                    return False
        except Exception as e:
            self.log(f"Error checking margin: {e}")
        
        return True
    
    def print_status(self):
        """Print current status"""
        self.log(f"\n📊 Status:")
        self.log(f"Open positions: {len(self.open_positions)}")
        self.log(f"Daily P&L: ${self.daily_stats.daily_pnl:+.2f}")
        self.log(f"Trades: {self.daily_stats.total_trades} ({self.daily_stats.winning_trades}W/{self.daily_stats.losing_trades}L)")
        
        if len(self.open_positions) > 0:
            self.log(f"Open tiers: {[p.tier for p in self.open_positions]}")
    
    def run_main_loop(self):
        """Main trading loop"""
        self.log("\n🤖 BOT STARTING MAIN LOOP...")
        self.log("Checking signals every 5 minutes...\n")
        
        tick = 0
        while True:
            try:
                tick += 1
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.log(f"\n[TICK {tick}] {current_time}")
                
                # Check daily loss limit
                if not self.check_daily_loss_limit():
                    self.log("Daily loss limit reached. Waiting 1 hour before resuming...")
                    time.sleep(3600)
                    continue
                
                # Check margin ratio
                if not self.check_margin_ratio():
                    self.log("Margin risk detected. Closing all positions...")
                    # Force close all positions
                    for position in self.open_positions[:]:
                        self.log(f"Force closing {position.tier}...")
                        self.open_positions.remove(position)
                    time.sleep(3600)
                    continue
                
                # Execute trades
                self.execute_tier1_trade()
                self.execute_tier2_trade()
                self.execute_tier3_trade()
                
                # Monitor positions
                self.monitor_positions()
                
                # Print status
                self.print_status()
                
                # Wait 5 minutes
                time.sleep(300)
                
            except KeyboardInterrupt:
                self.log("\n⏹️  BOT STOPPED BY USER")
                break
            except Exception as e:
                self.log(f"❌ Error in main loop: {e}")
                time.sleep(60)
    
    def start(self):
        """Start bot"""
        self.run_main_loop()

# ================================================
# MAIN
# ================================================

if __name__ == "__main__":
    try:
        bot = BotV10Futures()
        bot.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")