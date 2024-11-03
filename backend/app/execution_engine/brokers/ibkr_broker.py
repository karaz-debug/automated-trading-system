# execution_engine/brokers/ibkr_broker.py

from ib_insync import IB, Forex, Stock, Future, Option, MarketOrder, LimitOrder, StopOrder, Contract
import asyncio
from typing import Dict, Any
from utils.logger import get_logger

class IBKRBroker:
    def __init__(self, config: Dict[str, Any]):
        self.host = config.get('host', '127.0.0.1')
        self.port = config.get('port', 7497)
        self.clientId = config.get('clientId', 1)
        self.ib = IB()
        self.logger = get_logger('IBKRBroker')

    async def connect(self):
        """
        Asynchronously connect to IBKR.
        """
        try:
            await self.ib.connectAsync(self.host, self.port, clientId=self.clientId)
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

    async def send_order(self, signal: Dict[str, Any]):
        """
        Asynchronously send an order based on the trading signal.

        :param signal: Dictionary containing order details.
        """
        symbol = signal.get('symbol')
        action = signal.get('action')
        price = signal.get('price')
        quantity = signal.get('quantity')
        sec_type = signal.get('sec_type', 'CASH')
        currency = signal.get('currency', 'USD')
        exchange = signal.get('exchange', 'IDEALPRO')

        contract = self.get_contract(symbol, sec_type, currency, exchange)

        if action == 'BUY':
            order = MarketOrder('BUY', quantity)
        elif action == 'SELL':
            order = MarketOrder('SELL', quantity)
        else:
            self.logger.error(f"Invalid action: {action}")
            return

        try:
            trade = await self.ib.placeOrderAsync(contract, order)
            self.logger.info(f"Order placed: {trade}")
        except Exception as e:
            self.logger.error(f"Failed to place order for {symbol}: {e}")

    def get_contract(self, symbol: str, sec_type: str, currency: str, exchange: str) -> Contract:
        """
        Define the contract for a given symbol and security type.

        :param symbol: Symbol to trade
        :param sec_type: Security type (e.g., 'CASH', 'STK')
        :param currency: Currency (e.g., 'USD')
        :param exchange: Exchange (e.g., 'IDEALPRO')
        :return: IB Insync Contract object
        """
        if sec_type == 'CASH':
            return Forex(symbol)
        elif sec_type == 'STK':
            return Stock(symbol, exchange=exchange, currency=currency)
        elif sec_type == 'FUT':
            return Future(symbol, exchange=exchange, currency=currency, lastTradeDateOrContractMonth='202412')
        elif sec_type == 'OPT':
            return Option(
                symbol, exchange=exchange, currency=currency,
                lastTradeDateOrContractMonth='202412', right='CALL', strike=100
            )
        else:
            raise ValueError(f"Unsupported security type: {sec_type}")
