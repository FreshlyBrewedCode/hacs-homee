import asyncio
import logging
from pymee import Homee
from .registry import HomeeEntityRegistry
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class HassHomee(Homee):
    """Custom homee class used by the integration."""

    def __init__(
        self,
        host: str,
        user: str,
        password: str,
        device: str = "Home Assistant",
        pingInterval: int = 30,
        reconnectInterval: int = 10,
        reconnect: bool = True,
        maxRetries: int = 5,
        loop: asyncio.AbstractEventLoop = None,
    ) -> None:
        super().__init__(
            host,
            user,
            password,
            device=device,
            pingInterval=pingInterval,
            reconnectInterval=reconnectInterval,
            reconnect=reconnect,
            maxRetries=maxRetries,
            loop=loop,
        )

        _LOGGER.info("Setting up HassHomee...")

        # Import providers
        from .providers import HomeeLightProvider

        self.registry: HomeeEntityRegistry = HomeeEntityRegistry()

    async def on_message(self, msg: dict):
        msgType = list(msg)[0]

        if msgType == "all" or msgType == "nodes":
            self.registry.clear()

            _LOGGER.info(f"Registering nodes ({len(self.nodes)})")

            for node in self.nodes:
                self.registry.register(node)

            _LOGGER.info(f"Entries: {self.registry._entries}")