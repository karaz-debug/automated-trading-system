# # strategies/custom_strategy.py

# import pandas as pd
# from datetime import datetime, time, timedelta
# from utils.logger import get_logger

# def prepare_levels(historical_data, symbols):
#     """
#     Identify Asian session and previous day levels for each symbol.

#     :param historical_data: Dictionary of pandas DataFrames for each symbol
#     :param symbols: List of symbols
#     :return: Dictionaries containing Asian highs/lows and previous day highs/lows
#     """
#     asian_high = {}
#     asian_low = {}
#     prev_day_high = {}
#     prev_day_low = {}
#     logger = get_logger('PrepareLevels')

#     for symbol in symbols:
#         df = historical_data.get(symbol)
#         if df is None or df.empty:
#             logger.warning(f"No historical data for {symbol} to prepare levels.")
#             continue

#         # Ensure datetime index
#         if not isinstance(df.index, pd.DatetimeIndex):
#             df.index = pd.to_datetime(df.index)

#         # Asian session: 8:00 PM to 12:00 AM NY time
#         asian_session = df.between_time('20:00', '00:00')
#         if not asian_session.empty:
#             asian_high[symbol] = asian_session['high'].max()
#             asian_low[symbol] = asian_session['low'].min()
#             logger.info(f"{symbol} Asian High: {asian_high[symbol]}, Asian Low: {asian_low[symbol]}")
#         else:
#             logger.warning(f"No Asian session data for {symbol}.")

#         # Previous day levels
#         last_day = (df.index[-1].date() - timedelta(days=1))
#         prev_day_data = df[df.index.date == last_day]
#         if not prev_day_data.empty:
#             prev_day_high[symbol] = prev_day_data['high'].max()
#             prev_day_low[symbol] = prev_day_data['low'].min()
#             logger.info(f"{symbol} Previous Day High: {prev_day_high[symbol]}, Previous Day Low: {prev_day_low[symbol]}")
#         else:
#             logger.warning(f"No previous day data for {symbol}.")

#     return asian_high, asian_low, prev_day_high, prev_day_low

# def evaluate_trade_conditions(data, levels, symbols, current_time: time, logger):
#     """
#     Evaluate whether trade conditions are met based on current bar data.

#     :param data: Current bar data as a dictionary
#     :param levels: Dictionaries containing Asian and previous day levels
#     :param symbols: List of symbols
#     :param current_time: Current time as datetime.time object
#     :param logger: Logger instance
#     :return: List of trading signals
#     """
#     signals = []
#     trade_start_time = time(3, 0)
#     trade_end_time = time(4, 0)
#     risk_reward_ratio = 2  # 1:2

#     if not (trade_start_time <= current_time <= trade_end_time):
#         return signals  # Not within trading window

#     symbol = data['symbol']
#     sec_type = data['sec_type']
#     price = data['close']  # Using close price of the bar
#     bar_size = data['bar_size']

#     # Check if any level is cleared
#     cleared_level = None
#     if symbol in levels['asian_high'] and price > levels['asian_high'][symbol]:
#         cleared_level = 'asian_high'
#         logger.info(f"{symbol} cleared Asian High at {price}")
#     elif symbol in levels['asian_low'] and price < levels['asian_low'][symbol]:
#         cleared_level = 'asian_low'
#         logger.info(f"{symbol} cleared Asian Low at {price}")
#     elif symbol in levels['prev_day_high'] and price > levels['prev_day_high'][symbol]:
#         cleared_level = 'prev_day_high'
#         logger.info(f"{symbol} cleared Previous Day High at {price}")
#     elif symbol in levels['prev_day_low'] and price < levels['prev_day_low'][symbol]:
#         cleared_level = 'prev_day_low'
#         logger.info(f"{symbol} cleared Previous Day Low at {price}")

#     if cleared_level:
#         # Check for divergence and MSS (placeholder logic)
#         divergence = check_divergence(symbol)
#         if divergence:
#             mss = confirm_mss(symbol)
#             if mss:
#                 # Generate trading signal
#                 signal = generate_signal(symbol, cleared_level, price, risk_reward_ratio)
#                 if signal:
#                     signals.append(signal)

#     return signals

# def check_divergence(symbol: str) -> bool:
#     """
#     Placeholder function to check for divergence between correlated pairs.

#     :param symbol: Current symbol
#     :return: Boolean indicating if divergence is detected
#     """
#     # Implement actual divergence logic based on correlated pairs
#     # For demonstration, assume divergence is always detected
#     return True

# def confirm_mss(symbol: str) -> bool:
#     """
#     Placeholder function to confirm Market Structure Shift (MSS).

#     :param symbol: Current symbol
#     :return: Boolean indicating if MSS is confirmed
#     """
#     # Implement actual MSS confirmation logic
#     # For demonstration, assume MSS is always confirmed
#     return True

# def generate_signal(symbol: str, cleared_level: str, price: float, risk_reward_ratio: float):
#     """
#     Generate a trading signal based on the cleared level.

#     :param symbol: Currency pair symbol
#     :param cleared_level: The level that was cleared
#     :param price: Current price
#     :param risk_reward_ratio: Desired risk-reward ratio
#     :return: Dictionary containing signal details
#     """
#     signal = {}
#     if cleared_level in ['asian_high', 'prev_day_high']:
#         # Bearish setup
#         action = 'SELL'
#         sl = price + (price * 0.01)  # 1% SL above
#         tp = price - (price * 0.02)  # 2% TP below (1:2 RR)
#         signal = {
#             'symbol': symbol,
#             'action': action,
#             'price': price,
#             'stop_loss': sl,
#             'take_profit': tp,
#             'quantity': 100000,  # Example quantity
#             'timestamp': datetime.utcnow(),
#             'sec_type': 'CASH'  # Assuming Forex; adjust as needed
#         }
#     elif cleared_level in ['asian_low', 'prev_day_low']:
#         # Bullish setup
#         action = 'BUY'
#         sl = price - (price * 0.01)  # 1% SL below
#         tp = price + (price * 0.02)  # 2% TP above (1:2 RR)
#         signal = {
#             'symbol': symbol,
#             'action': action,
#             'price': price,
#             'stop_loss': sl,
#             'take_profit': tp,
#             'quantity': 100000,  # Example quantity
#             'timestamp': datetime.utcnow(),
#             'sec_type': 'CASH'  # Assuming Forex; adjust as needed
#         }
#     else:
#         return None

#     return signal
