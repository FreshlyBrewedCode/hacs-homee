"""The homee integration."""
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity import Entity
from pymee import Homee
from pymee.model import HomeeAttribute, HomeeNode
import voluptuous as vol

from .const import ATTR_ATTRIBUTE, ATTR_NODE, ATTR_VALUE, DOMAIN, SERVICE_SET_VALUE

# TODO
CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

PLATFORMS = ["light", "climate", "binary_sensor"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the homee component."""
    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up homee from a config entry."""
    # Create the Homee api object using host, user and password from the config
    homee = Homee(
        entry.data[CONF_HOST],
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
        loop=hass.loop,
    )
    hass.data[DOMAIN][entry.entry_id] = homee

    # Start the homee websocket connection as a new task and wait until we are connected
    hass.loop.create_task(homee.run())
    await homee.wait_until_connected()

    # Register the set_value service that can be used for debugging and custom automations
    def handle_set_value(call: ServiceCall):
        """Handle the service call."""
        node = int(call.data.get(ATTR_NODE, 0))
        attribute = int(call.data.get(ATTR_ATTRIBUTE, 0))
        value = float(call.data.get(ATTR_VALUE, 0))

        hass.async_create_task(homee.set_value(node, attribute, value))

    hass.services.async_register(DOMAIN, SERVICE_SET_VALUE, handle_set_value)

    # Forward entry setup to the platforms
    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a homee config entry."""
    # Unload platforms
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        # Get Homee object and remove it from data
        homee: Homee = hass.data[DOMAIN][entry.entry_id]
        hass.data[DOMAIN].pop(entry.entry_id)

        # Schedule homee disconnect and wait for disconnected event
        homee.disconnect()
        await homee.wait_until_disconnected()

        # Remove services
        hass.services.async_remove(DOMAIN, SERVICE_SET_VALUE)

    return unload_ok


class HomeeNodeHelper:
    """Provides a wrapper around HomeeNode to simply usage in homee entities."""

    def __init__(self, node: HomeeNode, entity: Entity) -> None:
        """Initialize the wrapper using a HomeeNode and target entity."""
        self._node = node
        self._entity = entity
        self._clear_node_listener = None

    def register_listener(self):
        """Register the on_changed listener on the node."""
        self._clear_node_listener = self._node.add_on_changed_listener(
            self._on_node_updated
        )

    def clear_listener(self):
        """Clear the on_changed listener on the node."""
        if self._clear_node_listener is not None:
            self._clear_node_listener()

    def attribute(self, attributeType):
        """Try to get the current value of the attribute of the given type."""
        try:
            return self._node.get_attribute_by_type(attributeType).current_value
        except Exception:
            raise AttributeNotFoundException(attributeType)

    def get_attribute(self, attributeType):
        """Get the attribute object of the given type."""
        return self._node.get_attribute_by_type(attributeType)

    def has_attribute(self, attributeType):
        """Check if an attribute of the given type exists."""
        return attributeType in self._node._attribute_map

    async def async_set_value(self, attribute_type: int, value: float):
        """Set an attribute value on the homee node."""
        await self.async_set_value_by_id(self.get_attribute(attribute_type).id, value)

    async def async_set_value_by_id(self, attribute_id: int, value: float):
        """Set an attribute value on the homee node."""
        await self._entity.hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_NODE: self._node.id,
                ATTR_ATTRIBUTE: attribute_id,
                ATTR_VALUE: value,
            },
        )

    def _on_node_updated(self, node: HomeeNode, attribute: HomeeAttribute):
        self._entity.schedule_update_ha_state()


class AttributeNotFoundException(Exception):
    """Raised if a requested attribute does not exist on a homee node."""

    def __init__(self, attributeType) -> None:
        """Initialize the exception."""
        self.attributeType = attributeType
