# backend/app/strategies/breakout_strategy.py

import backtrader as bt

class BreakoutStrategy(bt.Strategy):
    params = (
        ('lookback', 20),
        ('order_percentage', 0.95),
        ('ticker', 'AAPL')
    )

    def __init__(self):
        self.highest = bt.indicators.Highest(self.data.close, period=self.params.lookback)
        self.lowest = bt.indicators.Lowest(self.data.close, period=self.params.lookback)

    def next(self):
        if self.data.close[0] > self.highest[-1] and self.position.size == 0:
            size = int((self.broker.cash * self.params.order_percentage) / self.data.close)
            self.buy(size=size)
        elif self.data.close[0] < self.lowest[-1] and self.position.size > 0:
            self.close()
