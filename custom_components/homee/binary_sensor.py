"""The homee binary sensor platform."""

import logging

from pymee import Homee
from pymee.const import AttributeType, NodeProfile
from pymee.model import HomeeAttribute, HomeeNode

import homeassistant
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    DEVICE_CLASS_LOCK,
    DEVICE_CLASS_OPENING,
    DEVICE_CLASS_PLUG,
)
from homeassistant.config_entries import ConfigEntry

from . import HomeeNodeHelper
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def get_device_class(node: HomeeNodeHelper) -> int:
    """Determine the device class a homee node based on the available attributes."""
    device_class = DEVICE_CLASS_OPENING
    state_attr = AttributeType.OPEN_CLOSE

    if node.has_attribute(AttributeType.ON_OFF):
        state_attr = AttributeType.ON_OFF
        device_class = DEVICE_CLASS_PLUG

    if node.has_attribute(AttributeType.LOCK_STATE):
        state_attr = AttributeType.LOCK_STATE
        device_class = DEVICE_CLASS_LOCK

    return (device_class, state_attr)


def is_binary_sensor_node(node: HomeeNode):
    """Determine if a node is a binary sensor based on profile and attributes."""
    return node.profile in [
        NodeProfile.OPEN_CLOSE_SENSOR,
        NodeProfile.OPEN_CLOSE_AND_TEMPERATURE_SENSOR,
        NodeProfile.OPEN_CLOSE_WITH_TEMPERATURE_AND_BRIGHTNESS_SENSOR,
        NodeProfile.LOCK,
    ]


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add the homee platform for the binary sensor integration."""
    homee: Homee = hass.data[DOMAIN][config_entry.entry_id]

    devices = []
    for node in homee.nodes:
        if not is_binary_sensor_node(node):
            continue
        devices.append(HomeeBinarySensor(node))
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: homeassistant, entry: ConfigEntry):
    """Unload a config entry."""


class HomeeBinarySensor(BinarySensorEntity):
    """Representation of a homee binary sensor device."""

    def __init__(self, node: HomeeNode):
        """Initialize a homee binary sensor entity."""
        self._node = node
        self.node = HomeeNodeHelper(node, self)
        self._device_class, self._state_attr = get_device_class(self.node)
        _LOGGER.info(f"{node.name}: {node.profile}")

    async def async_added_to_hass(self) -> None:
        """Add the homee binary sensor device to home assistant."""
        self.node.register_listener()

    async def async_will_remove_from_hass(self):
        """Cleanup the entity."""
        self.node.clear_listener()

    @property
    def should_poll(self) -> bool:
        """Return if the entity should poll."""
        return False

    @property
    def unique_id(self):
        """Return the unique ID of the entity."""
        return self._node.id

    @property
    def name(self):
        """Return the display name of this entity."""
        return self._node.name

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return bool(self.node.attribute(self._state_attr))

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._device_class

    async def async_update(self):
        """Fetch new state data for this light."""
        self._node._remap_attributes()
