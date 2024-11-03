# backend/app/strategies/ict_strategy.py

import backtrader as bt
from datetime import time

class ICTStrategy(bt.Strategy):
    params = (
        ('pairs', ['EURUSD=X', 'GBPUSD=X']),
        ('usdx', 'DX-Y.NYB'),
        ('trading_start', time(3, 0)),
        ('trading_end', time(4, 0)),
        ('asian_start', time(20, 0)),
        ('asian_end', time(0, 0)),
        ('rr_ratio', 2.0),
        ('risk_per_trade', 0.01),  # Risk 1% per trade
    )

    def __init__(self):
        # Initialize dictionaries to store session highs/lows and previous day highs/lows
        self.asian_high = {pair: None for pair in self.params.pairs}
        self.asian_low = {pair: None for pair in self.params.pairs}
        self.prev_day_high = {pair: None for pair in self.params.pairs}
        self.prev_day_low = {pair: None for pair in self.params.pairs}
        
        # Store references to USDX data
        self.usdx = self.getdatabyname(self.params.usdx)
        
        # Initialize flags for level clearance
        self.level_cleared = {pair: False for pair in self.params.pairs}
        
        # Initialize indicators for Market Structure Shift (e.g., Moving Averages)
        self.ma = {}
        for pair in self.params.pairs:
            data = self.getdatabyname(pair)
            self.ma[pair] = bt.indicators.SimpleMovingAverage(data.close, period=20)

    def next(self):
        current_time = self.datas[0].datetime.time()

        # Mark Asian session high and low between 8:00 PM and 12:00 AM NY time
        if self.params.asian_start <= current_time or current_time < self.params.asian_end:
            for pair in self.params.pairs:
                data = self.getdatabyname(pair)
                if self.asian_high[pair] is None or data.high[0] > self.asian_high[pair]:
                    self.asian_high[pair] = data.high[0]
                if self.asian_low[pair] is None or data.low[0] < self.asian_low[pair]:
                    self.asian_low[pair] = data.low[0]

        # Mark previous day's high and low at 12:00 AM NY time
        if current_time == self.params.asian_end:
            for pair in self.params.pairs:
                data = self.getdatabyname(pair)
                self.prev_day_high[pair] = data.high[-1]
                self.prev_day_low[pair] = data.low[-1]

        # Trading time between 3:00 AM and 4:00 AM NY time
        if self.params.trading_start <= current_time < self.params.trading_end:
            for pair in self.params.pairs:
                data = self.getdatabyname(pair)

                # Check if price breaches Asian or previous day levels
                breach = False
                breach_type = None
                if self.asian_high[pair] and data.close[0] > self.asian_high[pair]:
                    breach = True
                    breach_type = 'bullish'
                elif self.asian_low[pair] and data.close[0] < self.asian_low[pair]:
                    breach = True
                    breach_type = 'bearish'
                elif self.prev_day_high[pair] and data.close[0] > self.prev_day_high[pair]:
                    breach = True
                    breach_type = 'bullish'
                elif self.prev_day_low[pair] and data.close[0] < self.prev_day_low[pair]:
                    breach = True
                    breach_type = 'bearish'

                if breach and not self.level_cleared[pair]:
                    # Check for divergence
                    divergence = self.check_divergence(pair, breach_type)
                    if divergence:
                        # Confirm Market Structure Shift (MSS)
                        mss = self.confirm_mss(pair, breach_type)
                        if mss:
                            # Enter on retest
                            self.enter_trade(pair, breach_type)
                            self.level_cleared[pair] = True

    def check_divergence(self, pair, breach_type):
        # Simple divergence logic between USDX and currency pair
        usdx_prev = self.usdx.close[-1]
        usdx_current = self.usdx.close[0]
        pair_prev = self.getdatabyname(pair).close[-1]
        pair_current = self.getdatabyname(pair).close[0]

        if breach_type == 'bullish':
            # USDX declining, pair rising
            if usdx_current < usdx_prev and pair_current > pair_prev:
                return True
        elif breach_type == 'bearish':
            # USDX rising, pair declining
            if usdx_current > usdx_prev and pair_current < pair_prev:
                return True
        return False

    def confirm_mss(self, pair, breach_type):
        # Confirm Market Structure Shift using SMA crossover
        data = self.getdatabyname(pair)
        if breach_type == 'bullish':
            if data.close[0] > self.ma[pair][0]:
                return True
        elif breach_type == 'bearish':
            if data.close[0] < self.ma[pair][0]:
                return True
        return False

    def enter_trade(self, pair, breach_type):
        data = self.getdatabyname(pair)
        risk = self.params.risk_per_trade

        if breach_type == 'bullish' and not self.getposition(data).size:
            # Calculate stop loss
            stop_loss = self.prev_day_low[pair] if self.prev_day_low[pair] else data.close[0] - (self.ma[pair][0] - data.close[0])
            risk_amount = self.broker.getcash() * risk
            risk_per_unit = data.close[0] - stop_loss
            if risk_per_unit <= 0:
                print(f"Invalid risk per unit for {pair}. Skipping trade.")
                return
            size = risk_amount / risk_per_unit
            self.buy(data=data, size=size)
            print(f"BUY order placed for {pair} at {data.close[0]} with size {size}")

        elif breach_type == 'bearish' and not self.getposition(data).size:
            # Calculate stop loss
            stop_loss = self.prev_day_high[pair] if self.prev_day_high[pair] else data.close[0] + (data.close[0] - self.ma[pair][0])
            risk_amount = self.broker.getcash() * risk
            risk_per_unit = stop_loss - data.close[0]
            if risk_per_unit <= 0:
                print(f"Invalid risk per unit for {pair}. Skipping trade.")
                return
            size = risk_amount / risk_per_unit
            self.sell(data=data, size=size)
            print(f"SELL order placed for {pair} at {data.close[0]} with size {size}")

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f"BUY EXECUTED, Price: {order.executed.price}")
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            elif order.issell():
                print(f"SELL EXECUTED, Price: {order.executed.price}")
                self.sellprice = order.executed.price
                self.sellcomm = order.executed.comm
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print("Order Canceled/Margin/Rejected")

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        print(f"OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}")
