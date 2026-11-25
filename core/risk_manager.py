from datetime import date

class RiskManager:
    def __init__(self, min_confidence=0.65, stake_per_trade=10.0, max_daily_loss=30.0, max_consecutive_losses=3, max_open_trades=2, risk_reward_ratio=2.0):
        self.min_confidence = float(min_confidence)
        self.stake_per_trade = float(stake_per_trade)
        self.max_daily_loss = float(max_daily_loss)
        self.max_consecutive_losses = int(max_consecutive_losses)
        self.max_open_trades = int(max_open_trades)
        self.risk_reward_ratio = float(risk_reward_ratio)
        self.current_day = date.today()
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.open_trades_count = 0

    def _reset_if_new_day(self):
        today = date.today()
        if today != self.current_day:
            self.current_day = today
            self.daily_pnl = 0.0
            self.consecutive_losses = 0

    def record_trade_result(self, profit_loss: float):
        self._reset_if_new_day()
        self.daily_pnl += float(profit_loss)
        self.consecutive_losses = self.consecutive_losses + 1 if profit_loss < 0 else 0

    def evaluate_trade(self, signal: str, confidence: float, balance: float) -> dict:
        self._reset_if_new_day()
        if signal not in ("BUY", "SELL"):
            return {"approved": False, "reason": "Signal is NEUTRAL."}
        if confidence < self.min_confidence:
            return {"approved": False, "reason": f"Confidence {confidence:.1%} < {self.min_confidence:.1%}."}
        if self.daily_pnl <= -abs(self.max_daily_loss):
            return {"approved": False, "reason": "Max daily loss reached."}
        if self.consecutive_losses >= self.max_consecutive_losses:
            return {"approved": False, "reason": "Max consecutive losses reached."}
        if balance < self.stake_per_trade or self.stake_per_trade < 1.0:
            return {"approved": False, "reason": "Insufficient balance for stake."}
        sl = max(1.0, round(self.stake_per_trade * 0.5, 2))
        tp = max(2.0, round(sl * self.risk_reward_ratio, 2))
        return {"approved": True, "reason": "Approved.", "stake": round(self.stake_per_trade, 2), "stop_loss": sl, "take_profit": tp}
      
