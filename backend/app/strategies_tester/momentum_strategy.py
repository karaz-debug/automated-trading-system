# backend/app/strategies/momentum_strategy.py

import backtrader as bt

class MomentumStrategy(bt.Strategy):
    params = (
        ('momentum_period', 14),
        ('overbought', 70),
        ('oversold', 30),
        ('order_percentage', 0.95),
        ('ticker', 'AAPL')
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI_SMA(
            self.data.close, period=self.params.momentum_period
        )

    def next(self):
        if self.rsi < self.params.oversold and self.position.size == 0:
            size = int((self.broker.cash * self.params.order_percentage) / self.data.close)
            self.buy(size=size)
        elif self.rsi > self.params.overbought and self.position.size > 0:
            self.close()
