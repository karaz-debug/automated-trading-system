# execution_engine/engine.py

import asyncio
from typing import Dict, Any
from .brokers import IBKRBroker  # Ensure this matches your actual package name
from utils.logger import get_logger

class ExecutionEngine:
    def __init__(self, broker_configs: Dict[str, Any]):
        self.brokers = {}
        self.logger = get_logger('ExecutionEngine')
        for broker_name, config in broker_configs.items():
            if config.get('type') == 'IBKR':
                self.brokers[broker_name] = IBKRBroker(config)
            else:
                self.logger.error(f"Unsupported broker type: {config.get('type')}")
        # Initialize other components as needed

    async def start(self):
        """
        Start the execution engine by connecting to all brokers.
        """
        tasks = []
        for broker in self.brokers.values():
            tasks.append(asyncio.create_task(broker.connect()))
        await asyncio.gather(*tasks)
        self.logger.info("Execution Engine started.")

    async def stop(self):
        """
        Stop the execution engine by disconnecting from all brokers.
        """
        tasks = []
        for broker in self.brokers.values():
            tasks.append(asyncio.create_task(broker.disconnect()))
        await asyncio.gather(*tasks)
        self.logger.info("Execution Engine stopped.")

    async def send_order(self, signal: Dict[str, Any]):
        """
        Send an order based on the trading signal.

        :param signal: Dictionary containing order details.
        """
        broker_name = signal.get('broker')
        broker = self.brokers.get(broker_name)
        if not broker:
            self.logger.error(f"Broker {broker_name} not found.")
            return

        try:
            await broker.send_order(signal)  # Assuming send_order is async
            self.logger.info(f"Order sent: {signal}")
        except Exception as e:
            self.logger.error(f"Failed to send order: {e}")
