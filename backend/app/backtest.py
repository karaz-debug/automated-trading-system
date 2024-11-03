# backend/app/backtest.py

import backtrader as bt
import datetime
import sys
import yfinance as yf
import pandas as pd  # Import pandas for DataFrame manipulation

# Import strategies from the strategies package
from strategies_tester.moving_average_crossover import MovingAverageCrossover
from strategies_tester.momentum_strategy import MomentumStrategy
from strategies_tester.breakout_strategy import BreakoutStrategy
from strategies_tester.bollinger_bands_strategy import BollingerBandsStrategy
from strategies_tester.ict_strategy import ICTStrategy  # Import the new ICT Strategy

def run_backtest(strategy, data_feeds, initial_cash=100000, commission=0.001):
    """
    Runs the backtest for the given strategy and data feeds.
    """
    cerebro = bt.Cerebro()
    cerebro.addstrategy(strategy)
    
    for data in data_feeds:
        cerebro.adddata(data)
    
    cerebro.broker.set_cash(initial_cash)
    cerebro.broker.setcommission(commission=commission)
    
    # Add analyzers for detailed reporting
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe_ratio')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analyzer')
    
    print(f"\nStarting Portfolio Value: {cerebro.broker.getvalue():.2f}")
    results = cerebro.run()
    strat = results[0]
    print(f"Ending Portfolio Value: {cerebro.broker.getvalue():.2f}")
    
    # Retrieve and print analyzer results safely
    print("\n--- Backtest Report ---")
    
    # Sharpe Ratio
    sharpe = strat.analyzers.sharpe_ratio.get_analysis().get('sharperatio', 'N/A')
    print(f"Sharpe Ratio: {sharpe}")
    
    # Drawdown
    drawdown = strat.analyzers.drawdown.get_analysis().get('max', {}).get('drawdown', 'N/A')
    print(f"Max Drawdown: {drawdown}%")
    
    # Trade Analyzer
    trade_analyzer = strat.analyzers.trade_analyzer.get_analysis()
    
    # Total Trades
    total_trades = trade_analyzer.get('total', {}).get('total', 'N/A')
    print(f"Total Trades: {total_trades}")
    
    # Wins
    wins = trade_analyzer.get('won', {}).get('total', 'N/A')
    print(f"Wins: {wins}")
    
    # Losses
    losses = trade_analyzer.get('lost', {}).get('total', 'N/A')
    print(f"Losses: {losses}")
    
    # Win Rate
    win_rate = trade_analyzer.get('won', {}).get('perc', {}).get('total', 'N/A')
    print(f"Win Rate: {win_rate}%")
    
    # Optional: Total PnL
    pnl = trade_analyzer.get('pnl', {}).get('net', {}).get('total', 'N/A')
    print(f"Total PnL: {pnl}")
    
    # Plot the results without volume to prevent axis limit errors
    cerebro.plot(volume=False)

def get_user_choice():
    """
    Presents a menu to the user to select a trading strategy.
    Returns:
    - choice: The user's selected strategy as a string.
    """
    print("\nSelect a Trading Strategy to Backtest:")
    print("1. Moving Average Crossover")
    print("2. Momentum Strategy")
    print("3. Breakout Strategy")
    print("4. Bollinger Bands Strategy")
    print("5. ICT Strategy")  # Added ICT Strategy
    choice = input("Enter the number corresponding to your choice (1-5): ")
    return choice

def main():
    """
    Main function to execute the backtest based on user-selected strategy.
    """
    choice = get_user_choice()

    strategy_map = {
        '1': MovingAverageCrossover,
        '2': MomentumStrategy,
        '3': BreakoutStrategy,
        '4': BollingerBandsStrategy,
        '5': ICTStrategy,  # Added ICT Strategy
    }

    # Retrieve the selected strategy
    strategy = strategy_map.get(choice)

    if not strategy:
        print("Invalid choice. Exiting.")
        sys.exit(1)

    # Define symbols and their Yahoo Finance tickers
    symbols = {
        'EURUSD': 'EURUSD=X',
        'GBPUSD': 'GBPUSD=X',
        'USDX': 'DX-Y.NYB'
    }

    # Download data using yfinance
    # Set start_date to 30 days before today
    start_date = datetime.datetime.now() - datetime.timedelta(days=7)
    end_date = datetime.datetime.now()
    # df = yf.download(ticker, start=start_date, end=end_date, interval='1m')


    print(f"\nDownloading data for EUR/USD, GBP/USD, and USDX from {start_date.date()} to {end_date.date()}...")

    data_feeds = []
    for name, ticker in symbols.items():
        print(f"\nDownloading {name} data...")
        df = yf.download(ticker, start=start_date, end=end_date, interval='1m')
        
        if df.empty:
            print(f"No data found for {ticker}. Exiting.")
            sys.exit(1)
        
        # Debug: Print the first few rows and columns
        print(f"\nDownloaded DataFrame for {name}:")
        print(df.head())
        print("\nDataFrame Columns:")
        print(df.columns.values)
        
        # Ensure df.columns are single-level and strings
        if isinstance(df.columns, pd.MultiIndex):
            # Flatten the MultiIndex by joining the tuples into single strings
            df.columns = ['_'.join(col).strip() for col in df.columns.values]
        else:
            # Convert all column names to strings (if they aren't already)
            df.columns = [str(col) for col in df.columns]
        
        # Debug: Print the processed columns
        print("\nProcessed DataFrame Columns:")
        print(df.columns.values)
        
        # Rename columns to match Backtrader's expectations
        # Mapping original columns to Backtrader's expected columns
        rename_map = {
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        }
        
        # Rename the columns
        df = df.rename(columns=rename_map)
        
        # Debug: Print the renamed columns
        print("\nRenamed DataFrame Columns:")
        print(df.columns.values)
        
        # Re-order columns to match Backtrader's expectations
        required_order = ['open', 'high', 'low', 'close', 'volume']
        try:
            df = df[required_order]
        except KeyError as e:
            print(f"Missing required column: {e}. Exiting.")
            sys.exit(1)
        
        # Debug: Print the final DataFrame head
        print("\nFinal DataFrame Head:")
        print(df.head())
        
        # Check for any NaN values in critical columns
        if df[required_order].isnull().values.any():
            print(f"Data for {name} contains NaN values. Please check the data source.")
            sys.exit(1)
        
        # Create a data feed from the pandas DataFrame
        data = bt.feeds.PandasData(dataname=df, name=name)
        data_feeds.append(data)
    
    # Run backtest with the selected strategy and data feeds
    run_backtest(strategy, data_feeds)

if __name__ == "__main__":
    main()
