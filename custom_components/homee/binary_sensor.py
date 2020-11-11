"""The homee binary sensor platform."""

import logging

import homeassistant
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_LOCK,
    DEVICE_CLASS_OPENING,
    DEVICE_CLASS_PLUG,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from pymee import Homee
from pymee.const import AttributeType, NodeProfile
from pymee.model import HomeeNode

from . import HomeeNodeEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def get_device_class(node: HomeeNodeEntity) -> int:
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


class HomeeBinarySensor(HomeeNodeEntity, BinarySensorEntity):
    """Representation of a homee binary sensor device."""

    def __init__(self, node: HomeeNode):
        """Initialize a homee binary sensor entity."""
        HomeeNodeEntity.__init__(self, node, self)

        self._device_class, self._state_attr = get_device_class(self)
        _LOGGER.info(f"{node.name}: {node.profile}")

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return bool(self.attribute(self._state_attr))

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._device_class
