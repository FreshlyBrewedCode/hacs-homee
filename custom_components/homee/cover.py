"""The homee cover platform."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntityFeature,
    CoverEntity,
    CoverDeviceClass,
)
from typing import cast
from homeassistant.config_entries import ConfigEntry
from pymee.const import AttributeType, NodeProfile
from pymee.model import HomeeNode

from . import HomeeNodeEntity, helpers

_LOGGER = logging.getLogger(__name__)


def get_cover_features(node: HomeeNodeEntity, default=0) -> int:
    """Determine the supported cover features of a homee node based on the available attributes."""
    features = default

    for attribute in node.attributes:
        if (
            attribute.type == AttributeType.UP_DOWN
            or attribute.type == AttributeType.OPEN_CLOSE
        ):
            if attribute.editable:
                features |= CoverEntityFeature.OPEN
                features |= CoverEntityFeature.CLOSE
                features |= CoverEntityFeature.STOP

        if attribute.type == AttributeType.POSITION:
            if attribute.editable:
                features |= CoverEntityFeature.SET_POSITION

    return features


def get_device_class(node: HomeeNode) -> int:
    """Determine the device class a homee node based on the node profile."""
    if node.profile == NodeProfile.GARAGE_DOOR_OPERATOR:
        return CoverDeviceClass.GARAGE

    if node.profile == NodeProfile.SHUTTER_POSITION_SWITCH:
        return CoverDeviceClass.SHUTTER


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_devices):
    """Add the homee platform for the cover integration."""
    # homee: Homee = hass.data[DOMAIN][config_entry.entry_id]

    devices = []
    for node in helpers.get_imported_nodes(hass, config_entry):
        if not is_cover_node(node):
            continue
        devices.append(HomeeCover(node, config_entry))
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


def is_cover_node(node: HomeeNode):
    """Determine if a node is controllable as a homee cover based on its profile and attributes."""
    return node.profile in [
        NodeProfile.ELECTRIC_MOTOR_METERING_SWITCH,
        NodeProfile.ELECTRIC_MOTOR_METERING_SWITCH_WITHOUT_SLAT_POSITION,
        NodeProfile.GARAGE_DOOR_OPERATOR,
        NodeProfile.SHUTTER_POSITION_SWITCH,
    ]


class HomeeCover(HomeeNodeEntity, CoverEntity):
    """Representation of a homee cover device."""

    _attr_has_entity_name = True

    def __init__(self, node: HomeeNode, entry: ConfigEntry) -> None:
        """Initialize a homee cover entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._supported_features = get_cover_features(node)
        self._device_class = get_device_class(node)

        self._unique_id = f"{self._node.id}-cover"

        # Since we only support covers without tilt, there should only be one of these.
        if self.has_attribute(AttributeType.UP_DOWN):
            self._open_close_attribute = AttributeType.UP_DOWN
        else:
            self._open_close_attribute = AttributeType.OPEN_CLOSE

    @property
    def name(self):
        """Return the display name of this cover."""
        return None

    @property
    def supported_features(self):
        """Return the supported features of the entity."""
        return self._supported_features

    @property
    def current_cover_position(self):
        """Return the cover's position."""
        return 100 - self.attribute(AttributeType.POSITION)

    @property
    def is_opening(self):
        """Return teh opening status of the cover."""
        return True if self.attribute(self._open_close_attribute) == 3 else False

    @property
    def is_closing(self):
        """Return the closing status of the cover."""
        return True if self.attribute(self._open_close_attribute) == 4 else False

    @property
    def is_closed(self):
        """Return the state of the cover."""
        return True if self.attribute(AttributeType.POSITION) == 100 else False

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        await self.async_set_value(self._open_close_attribute, 0)

    async def async_close_cover(self, **kwargs):
        """Close cover."""
        await self.async_set_value(self._open_close_attribute, 1)

    async def async_set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        if CoverEntityFeature.SET_POSITION in self._supported_features:
            position = 100 - cast(int, kwargs[ATTR_POSITION])
            await self.async_set_value(AttributeType.POSITION, position)

    async def async_stop_cover(self, **kwargs):
        """Stop the cover."""
        await self.async_set_value(self._open_close_attribute, 2)
