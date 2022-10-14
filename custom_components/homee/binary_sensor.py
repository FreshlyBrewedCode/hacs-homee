"""The homee binary sensor platform."""

from custom_components.homee.const import CONF_DOOR_GROUPS, CONF_WINDOW_GROUPS
import logging

import homeassistant
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_DOOR,
    DEVICE_CLASS_LOCK,
    DEVICE_CLASS_OPENING,
    DEVICE_CLASS_PLUG,
    BinarySensorEntity,
    DEVICE_CLASS_WINDOW,
)
from homeassistant.config_entries import ConfigEntry
from pymee.const import AttributeType, NodeProfile
from pymee.model import HomeeNode

from . import HomeeNodeEntity, helpers

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

    devices = []
    for node in helpers.get_imported_nodes(hass, config_entry):
        if not is_binary_sensor_node(node):
            continue
        devices.append(HomeeBinarySensor(node, config_entry))
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: homeassistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


class HomeeBinarySensor(HomeeNodeEntity, BinarySensorEntity):
    """Representation of a homee binary sensor device."""
    _attr_has_entity_name = True
    _attr_name = None

    def __init__(self, node: HomeeNode, entry: ConfigEntry):
        """Initialize a homee binary sensor entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)

        self._device_class = DEVICE_CLASS_OPENING
        self._state_attr = AttributeType.OPEN_CLOSE

        self._configure_device_class()
        self._unique_id = f"{self._node.id}-binary_sensor-{self._state_attr}"

    def _configure_device_class(self):
        """Configure the device class of the sensor"""

        # Get the initial device class and state attribute
        self._device_class, self._state_attr = get_device_class(self)

        # Set Window/Door device class based on configured groups
        if any(
            str(group.id) in self._entry.options.get(CONF_WINDOW_GROUPS, [])
            for group in self._node.groups
        ):
            self._device_class = DEVICE_CLASS_WINDOW
        elif any(
            str(group.id) in self._entry.options.get(CONF_DOOR_GROUPS, [])
            for group in self._node.groups
        ):
            self._device_class = DEVICE_CLASS_DOOR

    @property
    def is_on(self):
        """Return true if the binary sensor is on."""
        return bool(self.attribute(self._state_attr))

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._device_class
