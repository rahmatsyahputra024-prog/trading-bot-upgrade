"""
BOT V10 LIVE - Automated Trading Bot
=====================================

3-Tier system dengan:
- Tier 1: 5M scalp (A+ signals only)
- Tier 2: 1H swing (A+ or A signals)
- Tier 3: 4H patient (A+ or A signals)

Binance API + Signal Scorer
24/7 Cloud deployment (Railway)

FINAL CONFIG:
├─ Leverage: 5x
├─ Daily loss limit: -$20
├─ Monthly target: +$240
├─ Timeline: 4 months to $1,000!
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass

import requests
from binance.client import Client
from binance.enums import *

from tier_config import TIER_1, TIER_2, TIER_3, TOTAL_CAPITAL, DAILY_LOSS_LIMIT
from signal_scorer import SignalScorer

# ================================================
# LOGGING
# ================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot_v10.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('BOT_V10')

# ================================================
# CONFIG
# ================================================

BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', '')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY', '')
NTFY_CHANNEL = os.getenv('NTFY_CHANNEL', 'Mamat-trading')
USE_TESTNET = os.getenv('USE_TESTNET', 'True').lower() == 'true'

SYMBOL = 'BTCUSDT'

# ================================================
# DATA MODELS
# ================================================

@dataclass
class Position:
    """Open position"""
    tier: str
    entry_price: float
    entry_qty: float
    entry_time: str
    tp_price: float
    sl_price: float
    position_id: str
    status: str = "OPEN"

@dataclass
class DailyStats:
    """Daily statistics"""
    date: str
    opening_balance: float = TOTAL_CAPITAL
    current_balance: float = TOTAL_CAPITAL
    daily_pnl: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

# ================================================
# BOT MAIN ENGINE
# ================================================

class BotV10Live:
    """Main trading bot"""
    
    def __init__(self):
        self.symbol = SYMBOL
        self.client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY, testnet=USE_TESTNET)
        self.scorer = SignalScorer()
        
        self.open_positions: List[Position] = []
        self.daily_stats = DailyStats(date=datetime.now().strftime("%Y-%m-%d"))
        
        self.log("="*70)
        self.log("BOT V10 LIVE - Automated Trading System")
        self.log("="*70)
        self.log(f"Symbol: {self.symbol}")
        self.log(f"Mode: {'TESTNET (Paper)' if USE_TESTNET else 'LIVE'}")
        self.log(f"Capital: ${TOTAL_CAPITAL}")
        self.log(f"Daily loss limit: ${DAILY_LOSS_LIMIT}")
        self.log("")
    
    def log(self, msg):
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
        """Get current BTC price"""
        try:
            ticker = self.client.get_symbol_ticker(symbol=self.symbol)
            return float(ticker['price'])
        except Exception as e:
            self.log(f"❌ Error getting price: {e}")
            return 0.0
    
    def get_klines(self, interval: str, limit: int = 50) -> List:
        """Get historical klines"""
        try:
            klines = self.client.get_klines(
                symbol=self.symbol,
                interval=interval,
                limit=limit
            )
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
        
        # EMA simple
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
        
        # MACD simple
        ema_12 = sum(closes[-12:]) / 12
        ema_26 = sum(closes[-26:]) / 26 if len(closes) >= 26 else ema_12
        macd = ema_12 - ema_26
        signal = macd * 0.666  # Simplified
        
        # Volume
        avg_volume = sum(volumes[-20:]) / 20
        current_volume = volumes[-1]
        
        return {
            'close': closes[-1],
            'ema_9': ema_9,
            'ema_21': ema_21,
            'ema_50': ema_50,
            'ema_200': ema_200,
            'rsi': rsi,
            'macd': macd,
            'macd_signal': signal,
            'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1.0,
            'at_support': False,  # Simplified
            'bounce': False,  # Simplified
        }
    
    def check_tier1_signal(self) -> Optional[Dict]:
        """Check Tier 1 (5M) signal"""
        klines = self.get_klines(KLINE_INTERVAL_5MINUTE, 50)
        if not klines:
            return None
        
        indicators = self.calculate_indicators(klines)
        result = self.scorer.analyze(indicators)
        
        # Only A+ for Tier 1!
        if result['grade'] == 'A+':
            return {
                'tier': 'tier1',
                'score': result['score'],
                'grade': result['grade'],
                'indicators': indicators
            }
        return None
    
    def check_tier2_signal(self) -> Optional[Dict]:
        """Check Tier 2 (1H) signal"""
        klines = self.get_klines(KLINE_INTERVAL_1HOUR, 50)
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
        """Check Tier 3 (4H) signal"""
        klines = self.get_klines(KLINE_INTERVAL_4HOUR, 50)
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
        """Execute Tier 1 scalp trade"""
        signal = self.check_tier1_signal()
        if not signal:
            return
        
        current_price = self.get_price()
        if current_price == 0:
            return
        
        self.log(f"\n🚀 TIER 1 SIGNAL (A+)! Score: {signal['score']}/20")
        self.log(f"Price: ${current_price:,.2f}")
        
        position_size = TIER_1.position_size
        leverage = TIER_1.leverage
        notional = position_size * leverage
        
        tp_price = current_price * (1 + TIER_1.tp_percent)
        sl_price = current_price * (1 + TIER_1.sl_percent)
        
        self.log(f"Position: ${position_size} × {leverage}x = ${notional}")
        self.log(f"TP: ${tp_price:,.2f} (+{TIER_1.tp_percent*100:.1f}%)")
        self.log(f"SL: ${sl_price:,.2f} ({TIER_1.sl_percent*100:.1f}%)")
        
        # Create position object
        position = Position(
            tier='tier1',
            entry_price=current_price,
            entry_qty=notional / current_price,
            entry_time=datetime.now().isoformat(),
            tp_price=tp_price,
            sl_price=sl_price,
            position_id=f"tier1_{int(time.time())}"
        )
        self.open_positions.append(position)
        
        msg = f"Tier 1 Scalp Entry\nPrice: ${current_price:,.2f}\nTP: ${tp_price:,.2f}\nSL: ${sl_price:,.2f}"
        self.send_ntfy("🚀 TIER 1 ENTRY (A+)", msg)
    
    def execute_tier2_trade(self):
        """Execute Tier 2 swing trade"""
        signal = self.check_tier2_signal()
        if not signal:
            return
        
        current_price = self.get_price()
        if current_price == 0:
            return
        
        self.log(f"\n📈 TIER 2 SIGNAL ({signal['grade']})! Score: {signal['score']}/20")
        self.log(f"Price: ${current_price:,.2f}")
        
        position_size = TIER_2.position_size
        leverage = TIER_2.leverage
        notional = position_size * leverage
        
        tp_price = current_price * (1 + TIER_2.tp_percent)
        sl_price = current_price * (1 + TIER_2.sl_percent)
        
        self.log(f"Position: ${position_size} × {leverage}x = ${notional}")
        self.log(f"TP: ${tp_price:,.2f} (+{TIER_2.tp_percent*100:.1f}%)")
        self.log(f"SL: ${sl_price:,.2f} ({TIER_2.sl_percent*100:.1f}%)")
        
        position = Position(
            tier='tier2',
            entry_price=current_price,
            entry_qty=notional / current_price,
            entry_time=datetime.now().isoformat(),
            tp_price=tp_price,
            sl_price=sl_price,
            position_id=f"tier2_{int(time.time())}"
        )
        self.open_positions.append(position)
        
        msg = f"Tier 2 Swing Entry\nPrice: ${current_price:,.2f}\nTP: ${tp_price:,.2f}\nSL: ${sl_price:,.2f}"
        self.send_ntfy(f"📈 TIER 2 ENTRY ({signal['grade']})", msg)
    
    def execute_tier3_trade(self):
        """Execute Tier 3 patient trade"""
        signal = self.check_tier3_signal()
        if not signal:
            return
        
        current_price = self.get_price()
        if current_price == 0:
            return
        
        self.log(f"\n💪 TIER 3 SIGNAL ({signal['grade']})! Score: {signal['score']}/20")
        self.log(f"Price: ${current_price:,.2f}")
        
        position_size = TIER_3.position_size
        leverage = TIER_3.leverage
        notional = position_size * leverage
        
        tp_price = current_price * (1 + TIER_3.tp_percent)
        sl_price = current_price * (1 + TIER_3.sl_percent)
        
        self.log(f"Position: ${position_size} × {leverage}x = ${notional}")
        self.log(f"TP: ${tp_price:,.2f} (+{TIER_3.tp_percent*100:.1f}%)")
        self.log(f"SL: ${sl_price:,.2f} ({TIER_3.sl_percent*100:.1f}%)")
        
        position = Position(
            tier='tier3',
            entry_price=current_price,
            entry_qty=notional / current_price,
            entry_time=datetime.now().isoformat(),
            tp_price=tp_price,
            sl_price=sl_price,
            position_id=f"tier3_{int(time.time())}"
        )
        self.open_positions.append(position)
        
        msg = f"Tier 3 Patient Entry\nPrice: ${current_price:,.2f}\nTP: ${tp_price:,.2f}\nSL: ${sl_price:,.2f}"
        self.send_ntfy(f"💪 TIER 3 ENTRY ({signal['grade']})", msg)
    
    def monitor_positions(self):
        """Monitor open positions for TP/SL"""
        current_price = self.get_price()
        if current_price == 0:
            return
        
        for position in self.open_positions[:]:
            # Check TP
            if current_price >= position.tp_price:
                pnl = (position.tp_price - position.entry_price) * position.entry_qty
                self.log(f"✅ {position.tier.upper()} TP HIT! P&L: +${pnl:.2f}")
                self.daily_stats.daily_pnl += pnl
                self.daily_stats.winning_trades += 1
                self.open_positions.remove(position)
                self.send_ntfy(f"✅ {position.tier.upper()} TP HIT", f"P&L: +${pnl:.2f}")
            
            # Check SL
            elif current_price <= position.sl_price:
                pnl = (position.sl_price - position.entry_price) * position.entry_qty
                self.log(f"❌ {position.tier.upper()} SL HIT! P&L: ${pnl:.2f}")
                self.daily_stats.daily_pnl += pnl
                self.daily_stats.losing_trades += 1
                self.open_positions.remove(position)
                self.send_ntfy(f"❌ {position.tier.upper()} SL HIT", f"P&L: ${pnl:.2f}")
    
    def check_daily_loss_limit(self) -> bool:
        """Check if daily loss limit hit"""
        if self.daily_stats.daily_pnl <= DAILY_LOSS_LIMIT:
            self.log(f"\n⚠️  DAILY LOSS LIMIT HIT! P&L: ${self.daily_stats.daily_pnl:.2f}")
            self.send_ntfy("⚠️  DAILY LOSS LIMIT", f"P&L: ${self.daily_stats.daily_pnl:.2f}\nSTOP ALL TRADES!")
            return False
        return True
    
    def print_status(self):
        """Print current status"""
        self.log(f"\nOpen positions: {len(self.open_positions)}")
        self.log(f"Daily P&L: ${self.daily_stats.daily_pnl:+.2f}")
        self.log(f"Trades: {self.daily_stats.total_trades} ({self.daily_stats.winning_trades}W/{self.daily_stats.losing_trades}L)")
    
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
                    self.log("Waiting 1 hour before resuming...")
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
        bot = BotV10Live()
        bot.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")