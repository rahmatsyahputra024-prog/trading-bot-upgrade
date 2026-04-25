"""
SIGNAL SCORER - A+/A/B/C Grading
=================================

Score: 0-20 points
A+ = 18-20 (TRADE!)
A = 14-17 (TRADE!)
B = 10-13 (SKIP!)
C = <10 (SKIP!)
"""

import logging

logger = logging.getLogger('SCORER')

class SignalScorer:
    """Score signals 0-20"""
    
    def __init__(self):
        print("[SCORER] Initialized!")
    
    def score_signal(self, indicators):
        """Score signal 0-20"""
        score = 0
        
        # Trend (0-5)
        ema_9 = indicators.get('ema_9', 0)
        ema_21 = indicators.get('ema_21', 0)
        ema_50 = indicators.get('ema_50', 0)
        ema_200 = indicators.get('ema_200', 0)
        
        if ema_9 > ema_21 > ema_50 > ema_200:
            score += 5
        elif ema_9 > ema_21 > ema_50:
            score += 4
        elif ema_9 > ema_21:
            score += 2
        
        # Momentum (0-5)
        rsi = indicators.get('rsi', 50)
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        
        if rsi > 70 and macd > macd_signal:
            score += 5
        elif rsi > 60 and macd > macd_signal:
            score += 4
        elif rsi > 50:
            score += 2
        
        # Volume (0-5)
        volume_ratio = indicators.get('volume_ratio', 0)
        
        if volume_ratio > 1.5:
            score += 5
        elif volume_ratio > 1.2:
            score += 3
        elif volume_ratio > 1.0:
            score += 1
        
        # Support/Resistance (0-5)
        at_support = indicators.get('at_support', False)
        bounce = indicators.get('bounce', False)
        
        if at_support and bounce:
            score += 5
        elif at_support:
            score += 3
        
        return score
    
    def get_grade(self, score):
        """Convert score to grade"""
        if score >= 18:
            return "A+"
        elif score >= 14:
            return "A"
        elif score >= 10:
            return "B"
        else:
            return "C"
    
    def should_trade(self, score):
        """Only trade A+ or A"""
        grade = self.get_grade(score)
        return grade in ["A+", "A"]
    
    def analyze(self, indicators):
        """Full analysis"""
        score = self.score_signal(indicators)
        grade = self.get_grade(score)
        trade = self.should_trade(score)
        
        return {
            'score': score,
            'grade': grade,
            'trade': trade
        }

# Test
if __name__ == "__main__":
    scorer = SignalScorer()
    
    # Test A+ signal
    strong = {
        'ema_9': 65100,
        'ema_21': 65000,
        'ema_50': 64900,
        'ema_200': 64700,
        'rsi': 72,
        'macd': 50,
        'macd_signal': 40,
        'volume_ratio': 1.8,
        'at_support': True,
        'bounce': True,
    }
    
    result = scorer.analyze(strong)
    print(f"\nTest A+ Signal:")
    print(f"Score: {result['score']}/20")
    print(f"Grade: {result['grade']}")
    print(f"Trade: {'✅ YES' if result['trade'] else '❌ NO'}")
    
    # Test B signal (skip!)
    weak = {
        'ema_9': 65100,
        'ema_21': 65050,
        'ema_50': 65100,
        'ema_200': 64700,
        'rsi': 55,
        'macd': 30,
        'macd_signal': 40,
        'volume_ratio': 0.9,
        'at_support': False,
        'bounce': False,
    }
    
    result = scorer.analyze(weak)
    print(f"\nTest B Signal (SKIP!):")
    print(f"Score: {result['score']}/20")
    print(f"Grade: {result['grade']}")
    print(f"Trade: {'✅ YES' if result['trade'] else '❌ NO'}")
    