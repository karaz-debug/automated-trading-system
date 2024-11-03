# strategies_implementor/sma_crossover_strategy.py

from typing import Dict, List, Any
from datetime import datetime, time
import pandas as pd
from utils.logger import get_logger

# Initialize logger for the strategy
logger = get_logger('SMACrossoverStrategy')


def prepare_historical_data(historical_data: Dict[str, pd.DataFrame], strategy_config: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
    """
    Calculate short-term and long-term SMAs for each symbol.

    :param historical_data: Dictionary mapping symbols to their historical DataFrames
    :param strategy_config: Dictionary containing strategy-specific configurations
    :return: Dictionary mapping symbols to DataFrames with SMA columns
    """
    short_window = strategy_config['params']['short_ma']
    long_window = strategy_config['params']['long_ma']

    sma_data = {}

    for symbol in strategy_config['symbols']:
        sym = symbol['symbol']
        df = historical_data.get(sym)

        if df is None or df.empty:
            logger.warning(f"No historical data for {sym} to prepare SMA.")
            continue

        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Calculate SMAs
        df['short_sma'] = df['close'].rolling(window=short_window).mean()
        df['long_sma'] = df['close'].rolling(window=long_window).mean()

        sma_data[sym] = df

        logger.info(f"{sym} SMA calculated: short_window={short_window}, long_window={long_window}")

    return sma_data


def evaluate_trade_conditions(
    bar_data: Dict[str, Any],
    sma_data: Dict[str, pd.DataFrame],
    previous_sma: Dict[str, Dict[str, float]],
    strategy_config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Evaluate whether trade conditions are met based on the current bar data.

    :param bar_data: Dictionary containing current bar data
    :param sma_data: Dictionary mapping symbols to DataFrames with SMA columns
    :param previous_sma: Dictionary storing previous SMA values for trend detection
    :param strategy_config: Dictionary containing strategy-specific configurations
    :return: List of trading signals
    """
    signals = []
    trade_time_start = time(0, 0)
    trade_time_end = time(23, 59)

    current_time = bar_data['timestamp'].time()

    # Ensure trading is within operational hours
    if not (trade_time_start <= current_time <= trade_time_end):
        return signals  # Outside trading hours

    symbol = bar_data['symbol']
    price = bar_data['close']
    sec_type = bar_data['sec_type']

    # Retrieve SMA data
    symbol_sma = sma_data.get(symbol)

    if symbol_sma is None or symbol_sma.empty:
        logger.warning(f"No SMA data available for {symbol}.")
        return signals

    # Get the latest two SMA values
    latest = symbol_sma.iloc[-1]
    previous = symbol_sma.iloc[-2] if len(symbol_sma) >= 2 else None

    if previous is None or pd.isna(previous['short_sma']) or pd.isna(previous['long_sma']):
        logger.debug(f"Insufficient SMA data for {symbol}.")
        return signals  # Not enough data to evaluate

    # Store previous SMA for trend detection
    prev_short_sma = previous_sma.get(symbol, {}).get('short_sma')
    prev_long_sma = previous_sma.get(symbol, {}).get('long_sma')

    current_short_sma = latest['short_sma']
    current_long_sma = latest['long_sma']

    # Update previous SMA
    previous_sma[symbol] = {
        'short_sma': current_short_sma,
        'long_sma': current_long_sma
    }

    # Determine if a crossover occurred
    # Bullish Crossover
    if prev_short_sma and prev_long_sma:
        if (prev_short_sma <= prev_long_sma) and (current_short_sma > current_long_sma):
            # Generate BUY signal
            signal = generate_signal(
                symbol=symbol,
                action='BUY',
                price=price,
                strategy_params=strategy_config['params'],
                sec_type=sec_type
            )
            if signal:
                signals.append(signal)

        # Bearish Crossover
        elif (prev_short_sma >= prev_long_sma) and (current_short_sma < current_long_sma):
            # Generate SELL signal
            signal = generate_signal(
                symbol=symbol,
                action='SELL',
                price=price,
                strategy_params=strategy_config['params'],
                sec_type=sec_type
            )
            if signal:
                signals.append(signal)

    return signals


def generate_signal(
    symbol: str,
    action: str,
    price: float,
    strategy_params: Dict[str, Any],
    sec_type: str
) -> Dict[str, Any]:
    """
    Generate a trading signal based on the action and price.

    :param symbol: Symbol to trade
    :param action: 'BUY' or 'SELL'
    :param price: Entry price
    :param strategy_params: Dictionary containing strategy-specific parameters
    :param sec_type: Security type
    :return: Dictionary containing signal details
    """
    signal = {}
    tp_percent = strategy_params.get('tp_percent', 14)
    sl_percent = strategy_params.get('sl_percent', 7)

    if action.upper() == 'BUY':
        sl = price * (1 - sl_percent / 100)
        tp = price * (1 + tp_percent / 100)
    elif action.upper() == 'SELL':
        sl = price * (1 + sl_percent / 100)
        tp = price * (1 - tp_percent / 100)
    else:
        logger.error(f"Invalid action: {action}")
        return None

    signal = {
        'broker': 'IBKR',  # Specify the broker to use
        'symbol': symbol,
        'action': action.upper(),
        'price': price,
        'stop_loss': sl,
        'take_profit': tp,
        'quantity': strategy_params.get('quantity', 100000),  # Adjust based on risk management
        'timestamp': datetime.utcnow(),
        'sec_type': sec_type,
        'currency': strategy_params.get('currency', 'USD'),       # Default currency; adjust as needed
        'exchange': strategy_params.get('exchange', 'IDEALPRO')   # Default exchange; adjust as needed
    }

    logger.info(f"Generated {action.upper()} signal for {symbol} at {price} with SL={sl} and TP={tp}")
    return signal
