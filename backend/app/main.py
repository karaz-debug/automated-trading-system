# main.py

import asyncio
from typing import Dict, Any, List
import pandas as pd  # Ensure pandas is imported for DataFrame handling

from data_feeds import IBKRDataFeed  # Ensure this matches your actual package name
from strategies_implementor.sma_crossover_strategy import (
    prepare_historical_data,
    evaluate_trade_conditions
)
from execution_engine.engine import ExecutionEngine
from risk_management.risk_manager import risk_management, enforce_daily_limits
from utils.logger import get_logger
from utils.config import load_config
from datetime import datetime, time

# Global variables for risk management
account_balance = 100000  # Example account balance; replace with actual account balance retrieval
trades_today = []
max_daily_loss = 500  # Maximum loss per day
max_daily_trades = 10  # Maximum number of trades per day


async def signal_handler(
    signal: Dict[str, Any],
    execution_engine: ExecutionEngine,
    risk_config: Dict[str, Any],
    logger: Any
):
    """
    Handle trading signals by applying risk management and sending orders to the Execution Engine.
    """
    global trades_today, account_balance

    # Apply risk management
    adjusted_signal = risk_management(signal, account_balance, risk_config)

    # Enforce daily limits
    if not enforce_daily_limits(trades_today, max_daily_loss, max_daily_trades):
        logger.warning("Daily trading limits reached. No further trades will be executed today.")
        return

    # Send order to Execution Engine
    await execution_engine.send_order(adjusted_signal)  # Assuming send_order is async

    # Log the trade
    trades_today.append({
        'symbol': adjusted_signal['symbol'],
        'action': adjusted_signal['action'],
        'price': adjusted_signal['price'],
        'loss': 0  # Update 'loss' as needed based on actual trade outcomes
    })


async def on_bar_aggregated(
    data: Dict[str, Any],
    sma_data: Dict[str, pd.DataFrame],
    previous_sma: Dict[str, Dict[str, float]],
    strategy_config: Dict[str, Any],
    execution_engine: ExecutionEngine,
    risk_config: Dict[str, Any],
    logger: Any
):
    """
    Callback function to handle incoming aggregated bar data.
    """
    # Evaluate trade conditions
    signals = evaluate_trade_conditions(
        bar_data=data,
        sma_data=sma_data,
        previous_sma=previous_sma,
        strategy_config=strategy_config
    )

    for signal in signals:
        # Handle the signal
        await signal_handler(signal, execution_engine, risk_config, logger)

        # Here, you can update `account_balance` based on trade outcomes if desired


async def main():
    # Load configuration
    config = load_config('config/config.yaml')

    # Initialize Logger
    logger = get_logger('Main')

    # Initialize Execution Engine
    broker_configs = config.get('brokers', {})
    execution_engine = ExecutionEngine(broker_configs)
    await execution_engine.start()  # Assuming start is async

    # Risk management configuration
    risk_config = config.get('risk_management', {})

    # Initialize strategies
    strategies = config.get('strategies', [])

    # Prepare SMA data for all strategies
    sma_data_all = {}
    previous_sma_all = {}

    # Fetch and prepare historical data
    for strategy in strategies:
        strategy_name = strategy.get('name')
        symbols = strategy.get('symbols', [])
        historical_config = strategy.get('historical', {})
        duration = historical_config.get('duration', '1 D')
        bar_size = historical_config.get('bar_size', '1m')

        # Fetch historical data for the strategy
        historical_data = {}
        ibkr_data_feed_history = IBKRDataFeed(strategy, callback=None)  # No callback needed for historical data
        await ibkr_data_feed_history.connect()

        for symbol_info in symbols:
            symbol = symbol_info.get('symbol')
            sec_type = symbol_info.get('sec_type', 'CASH')
            df = await ibkr_data_feed_history.fetch_historical_data(
                symbol=symbol,
                sec_type=sec_type,
                duration=duration,
                bar_size=bar_size
            )
            historical_data[symbol] = df

        await ibkr_data_feed_history.disconnect()

        # Prepare SMA data
        strategy_sma_data = prepare_historical_data(historical_data, strategy)
        for sym, sma_df in strategy_sma_data.items():
            sma_data_all[sym] = sma_df

            # Initialize previous SMA
            if len(sma_df) >= 1:
                previous_sma_all[sym] = {
                    'short_sma': sma_df['short_sma'].iloc[-1],
                    'long_sma': sma_df['long_sma'].iloc[-1]
                }

    # Define the asynchronous callback for data feeds
    async def bar_callback(data: Dict[str, Any]):
        logger.debug(f"Received new bar data: {data}")
        symbol = data.get('symbol')
        if symbol not in sma_data_all:
            return  # No SMA data available for this symbol

        # Update SMA data
        sma_df = sma_data_all[symbol]
        new_row = pd.DataFrame([data])
        sma_df = pd.concat([sma_df, new_row], ignore_index=True)
        sma_df['short_sma'] = sma_df['close'].rolling(window=strategy.get('params', {}).get('short_ma', 5)).mean()
        sma_df['long_sma'] = sma_df['close'].rolling(window=strategy.get('params', {}).get('long_ma', 20)).mean()
        sma_data_all[symbol] = sma_df

        # Get the latest SMA values
        if len(sma_df) >= 2:
            previous_sma = {
                'short_sma': sma_df['short_sma'].iloc[-2],
                'long_sma': sma_df['long_sma'].iloc[-2]
            }
            current_sma = {
                'short_sma': sma_df['short_sma'].iloc[-1],
                'long_sma': sma_df['long_sma'].iloc[-1]
            }

            # Prepare data for strategy evaluation
            evaluation_data = {
                'symbol': symbol,
                'close': data.get('close'),
                'timestamp': data.get('timestamp')  # Ensure timestamp is present
            }

            # Find the strategy associated with this symbol
            for strategy in strategies:
                if any(s['symbol'] == symbol for s in strategy.get('symbols', [])):
                    await on_bar_aggregated(
                        data=evaluation_data,
                        sma_data=sma_data_all,
                        previous_sma=previous_sma_all,
                        strategy_config=strategy,
                        execution_engine=execution_engine,
                        risk_config=risk_config,
                        logger=logger
                    )

    # Initialize Data Feeds for all strategies
    data_feed_tasks = []
    for strategy in strategies:
        symbols = strategy.get('symbols', [])
        data_feed = IBKRDataFeed(strategy, callback=bar_callback)
        task = asyncio.create_task(data_feed.start())  # Assuming start is async and runs indefinitely
        data_feed_tasks.append(task)

    logger.info("Trading system started. Press Ctrl+C to exit.")

    try:
        await asyncio.gather(*data_feed_tasks)
    except asyncio.CancelledError:
        logger.info("Trading system is shutting down...")
    finally:
        # Stop all data feeds
        for task in data_feed_tasks:
            task.cancel()
        await asyncio.gather(*data_feed_tasks, return_exceptions=True)
        # Stop Execution Engine
        await execution_engine.stop()  # Assuming stop is async
        logger.info("Trading system stopped.")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Trading system terminated by user.")
