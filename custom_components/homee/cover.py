"""The homee cover platform."""

import logging

import homeassistant
from homeassistant.components.cover import (
    ATTR_POSITION,
    SUPPORT_OPEN,
    SUPPORT_CLOSE,
    SUPPORT_STOP,
    SUPPORT_SET_POSITION,
    CoverEntity,
)
from typing import Any, cast
from homeassistant.config_entries import ConfigEntry
from pymee.const import AttributeType, NodeProfile
from pymee.model import HomeeNode

from . import HomeeNodeEntity, helpers

_LOGGER = logging.getLogger(__name__)


def get_cover_features(node: HomeeNodeEntity, default=0) -> int:
    """Determine the supported cover features of a homee node based on the available attributes."""
    features = default

    if node.has_attribute(AttributeType.UP_DOWN) and node.has_attribute(AttributeType.MANUAL_OPERATION):
        features |= SUPPORT_OPEN
        features |= SUPPORT_CLOSE
        features |= SUPPORT_STOP
    if node.has_attribute(AttributeType.POSITION):
        features |= SUPPORT_SET_POSITION
    return features


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add the homee platform for the cover integration."""
    # homee: Homee = hass.data[DOMAIN][config_entry.entry_id]

    devices = []
    for node in helpers.get_imported_nodes(hass, config_entry):
        if not is_cover_node(node):
            continue
        devices.append(HomeeCover(node, config_entry))
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: homeassistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


def is_cover_node(node: HomeeNode):
    """Determine if a node is controllable as a homee cover based on its profile and attributes."""
    return node.profile in [
        NodeProfile.ELECTRIC_MOTOR_METERING_SWITCH,
        NodeProfile.OPEN_CLOSE_WITH_TEMPERATURE_AND_BRIGHTNESS_SENSOR,
        NodeProfile.ELECTRIC_MOTOR_METERING_SWITCH_WITHOUT_SLAT_POSITION,
        NodeProfile.GARAGE_DOOR_OPERATOR,
        NodeProfile.GARAGE_DOOR_IMPULSE_OPERATOR
    ]


class HomeeCover(HomeeNodeEntity, CoverEntity):
    """Representation of a homee climate device."""

    def __init__(self, node: HomeeNode, entry: ConfigEntry):
        """Initialize a homee cover entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._supported_features = get_cover_features(self)

    @property
    def supported_features(self):
        """Return the supported features of the entity."""
        return self._supported_features

    @property
    def current_cover_position(self):
        """Return the cover's position"""
        return self.attribute(AttributeType.POSITION)

    @property
    def is_opening(self):
        """opening status of the cover."""
        return True if self.attribute(AttributeType.UP_DOWN) == 2 else False

    @property
    def is_closing(self):
        """Return the closing status of the cover."""
        return True if self.attribute(AttributeType.UP_DOWN) == 3 else False

    @property
    def is_closed(self):
        """Return the state of the cover."""
        return True if self.attribute(AttributeType.POSITION) == 1 else False

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        await self.async_set_value(
            AttributeType.UP_DOWN, 0
        )

    async def async_close_cover(self, **kwargs):
        """Close cover."""
        await self.async_set_value(
            AttributeType.UP_DOWN, 1
        )

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        position = cast(int, kwargs[ATTR_POSITION])
        await self.async_set_value(
            AttributeType.POSITION, position
        )

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        await self.async_set_value(
            AttributeType.UP_DOWN, 4
        )