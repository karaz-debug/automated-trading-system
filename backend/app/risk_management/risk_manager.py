# risk_management/risk_manager.py

from utils.logger import get_logger

def calculate_position_size(account_balance, risk_per_trade, stop_loss_pips, pip_value=10):
    """
    Calculate position size based on risk parameters.

    :param account_balance: Total account balance
    :param risk_per_trade: Percentage of account to risk per trade (e.g., 1 for 1%)
    :param stop_loss_pips: Number of pips for stop loss
    :param pip_value: Value per pip (default 10 for standard lot)
    :return: Position size (quantity)
    """
    risk_amount = (risk_per_trade / 100) * account_balance
    position_size = risk_amount / (stop_loss_pips * pip_value)
    return int(position_size)

def enforce_daily_limits(trades_today, max_loss, max_trades):
    """
    Enforce daily trading limits.

    :param trades_today: List of trade results for the day
    :param max_loss: Maximum allowable loss for the day
    :param max_trades: Maximum number of trades for the day
    :return: Boolean indicating if trading should continue
    """
    total_loss = sum([trade['loss'] for trade in trades_today])
    total_trades = len(trades_today)

    if total_loss >= max_loss:
        return False  # Stop trading
    if total_trades >= max_trades:
        return False  # Stop trading

    return True

def risk_management(trade_signal, account_balance, config):
    """
    Manage risk by calculating position size and enforcing limits.

    :param trade_signal: Dictionary containing trade details
    :param account_balance: Current account balance
    :param config: Risk management configuration
    :return: Modified trade_signal with position size
    """
    stop_loss = trade_signal.get('stop_loss')
    # Assuming price is in pips, adjust as needed
    stop_loss_pips = abs(trade_signal['price'] - stop_loss) * 10000  # Example for Forex

    position_size = calculate_position_size(
        account_balance,
        config.get('risk_per_trade', 1),  # Default 1%
        stop_loss_pips,
        pip_value=config.get('pip_value', 10)
    )

    trade_signal['quantity'] = position_size

    logger = get_logger('RiskManager')
    logger.info(f"Calculated position size: {position_size} units for trade: {trade_signal}")

    return trade_signal
