# backend/app/strategies/bollinger_bands_strategy.py

import backtrader as bt

class BollingerBandsStrategy(bt.Strategy):
    params = (
        ('period', 20),
        ('devfactor', 2),
        ('order_percentage', 0.95),
        ('ticker', 'AAPL')
    )

    def __init__(self):
        self.boll = bt.indicators.BollingerBands(
            self.data.close,
            period=self.params.period,
            devfactor=self.params.devfactor
        )

    def next(self):
        if self.data.close[0] < self.boll.lines.bot and self.position.size == 0:
            size = int((self.broker.cash * self.params.order_percentage) / self.data.close)
            self.buy(size=size)
        elif self.data.close[0] > self.boll.lines.top and self.position.size > 0:
            self.close()
