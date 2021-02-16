import logging
from typing import List
from pymee.model import HomeeNode
import itertools

_LOGGER = logging.getLogger(__name__)


class HomeeEntityEntry:
    def __init__(self, component: str, node: HomeeNode, extra_data: dict = {}) -> None:
        self.component = component
        self.node = node
        self.extra_data = extra_data

    @staticmethod
    def light(node: HomeeNode, extra_data: dict = {}):
        return HomeeEntityEntry("light", node, extra_data)


class HomeeEntityRegistry:
    def __init__(self) -> None:
        self._entries: List[HomeeEntityEntry] = []
        self._providers: List[HomeeEntityProvider] = HomeeEntityProvider.get_providers(
            self
        )

    def clear(self):
        """Clears all entries from the registry."""
        self._entries.clear()

    def register(self, node: HomeeNode):
        """Registers a homee node and adds matching entries to the registy."""
        new_entries = self._extract_entities(node)
        self._entries += new_entries

    def get_component_entries(self, component: str) -> List[HomeeEntityEntry]:
        """Returns the registered entries for the given component."""
        return [e for e in self._entries if e.component == component]

    def _extract_entities(self, node: HomeeNode) -> List[HomeeEntityEntry]:
        entries = []

        for p in self._providers:
            entries = p.provide(node)

        return entries


class HomeeEntityProvider:
    """Base class for all homee entity providers. A provider provides home assistant entities for a homee node."""

    _providers = []

    def __init__(self, registry: HomeeEntityRegistry) -> None:
        self._registry: HomeeEntityRegistry = registry

    def provide(self, node: HomeeNode) -> List[HomeeEntityEntry]:
        return []

    @staticmethod
    def get_providers(registry: HomeeEntityRegistry):
        return list([provider(registry) for provider in HomeeEntityProvider._providers])

    @staticmethod
    def register_provider(provider):
        HomeeEntityProvider._providers.append(provider)


def homee_entity_provider(provider_class):
    """Decorator to add a class to the global list of homee entity providers."""
    if issubclass(provider_class, HomeeEntityProvider):
        HomeeEntityProvider.register_provider(provider_class)
    return provider_class