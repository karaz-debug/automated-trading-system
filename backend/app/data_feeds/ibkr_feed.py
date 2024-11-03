# data_feed/ibkr_feed.py

import asyncio
from typing import Dict, Any, Callable
from ib_insync import IB, Forex, Stock, Future, Option, util
from utils.logger import get_logger
import pandas as pd

class IBKRDataFeed:
    def __init__(self, config: Dict[str, Any], callback: Callable[[Dict[str, Any]], Any] = None):
        """
        Initialize the IBKR Data Feed.

        :param config: Dictionary containing broker-specific configurations.
        :param callback: Async function to call with aggregated bar data.
        """
        self.config = config
        self.callback = callback
        self.ib = IB()
        self.logger = get_logger('IBKRDataFeed')
        self.running = False

    async def connect(self):
        """
        Asynchronously connect to IBKR.
        """
        try:
            await self.ib.connectAsync(
                self.config.get('host', '127.0.0.1'),
                self.config.get('port', 7497),
                clientId=self.config.get('clientId', 1)
            )
            if self.ib.isConnected():
                self.logger.info("Connected to IBKR")
            else:
                self.logger.error("Failed to connect to IBKR")
        except asyncio.CancelledError:
            self.logger.info("Connection attempt cancelled.")
        except Exception as e:
            self.logger.error(f"API connection failed: {e}")

    async def disconnect(self):
        """
        Asynchronously disconnect from IBKR.
        """
        if self.ib.isConnected():
            self.ib.disconnect()
            self.logger.info("Disconnected from IBKR")

    def get_contract(self, symbol: str, sec_type: str) -> Any:
        """
        Define the contract for a given symbol and security type.

        :param symbol: Symbol to trade
        :param sec_type: Security type (e.g., 'CASH', 'STK')
        :return: IB Insync Contract object
        """
        if sec_type == 'CASH':
            return Forex(symbol)
        elif sec_type == 'STK':
            return Stock(symbol, exchange='SMART', currency='USD')
        elif sec_type == 'FUT':
            return Future(symbol, exchange='GLOBEX', currency='USD', lastTradeDateOrContractMonth='202412')
        elif sec_type == 'OPT':
            return Option(
                symbol, exchange='SMART', currency='USD',
                lastTradeDateOrContractMonth='202412', right='CALL', strike=100
            )
        else:
            raise ValueError(f"Unsupported security type: {sec_type}")

    async def fetch_historical_data(self, symbol: str, sec_type: str, duration: str, bar_size: str) -> pd.DataFrame:
        """
        Asynchronously fetch historical data for a given symbol.

        :param symbol: Symbol to fetch data for.
        :param sec_type: Security type.
        :param duration: Duration of historical data.
        :param bar_size: Size of each bar.
        :return: DataFrame containing historical data.
        """
        contract = self.get_contract(symbol, sec_type)
        try:
            bars = await self.ib.reqHistoricalDataAsync(
                contract,
                endDateTime='',
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow='MIDPOINT',
                useRTH=True,
                formatDate=1
            )
            df = util.df(bars)
            return df
        except Exception as e:
            self.logger.error(f"Failed to fetch historical data for {symbol}: {e}")
            return pd.DataFrame()

    async def start(self):
        """
        Start the data feed.
        """
        await self.connect()
        self.running = True
        self.logger.info("Data feed started.")
        await self.run()

    async def run(self):
        """
        Main loop to fetch and process data.
        """
        symbols = self.config.get('symbols', [])
        duration = self.config.get('historical', {}).get('duration', '1 D')
        bar_size = self.config.get('historical', {}).get('bar_size', '1m')

        while self.running:
            try:
                for symbol_info in symbols:
                    symbol = symbol_info.get('symbol')
                    sec_type = symbol_info.get('sec_type', 'CASH')
                    df = await self.fetch_historical_data(
                        symbol=symbol,
                        sec_type=sec_type,
                        duration=duration,
                        bar_size=bar_size
                    )
                    # Process data as needed (e.g., calculate indicators)
                    if not df.empty and self.callback:
                        latest_bar = df.iloc[-1].to_dict()
                        await self.callback(latest_bar)
                await asyncio.sleep(60)  # Fetch data every minute
            except asyncio.CancelledError:
                self.logger.info("Data feed run cancelled.")
                break
            except Exception as e:
                self.logger.error(f"Error in data feed run: {e}")
                await asyncio.sleep(60)  # Retry after delay

    async def stop(self):
        """
        Stop the data feed.
        """
        self.running = False
        await self.disconnect()
        self.logger.info("Data feed stopped.")
