"""The homee light platform."""

import logging

import homeassistant
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR,
    SUPPORT_COLOR_TEMP,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.util.color import (
    color_hs_to_RGB,
    color_RGB_to_hs,
    color_temperature_kelvin_to_mired,
    color_temperature_mired_to_kelvin,
)
from pymee.const import AttributeType, NodeProfile
from pymee.model import HomeeNode

from . import HomeeNodeEntity, helpers
from .const import HOMEE_LIGHT_MAX_MIRED, HOMEE_LIGHT_MIN_MIRED

_LOGGER = logging.getLogger(__name__)


def get_light_features(node: HomeeNodeEntity, default=0) -> int:
    """Determine the supported features of a homee light based on the available attributes."""
    features = default

    if node.has_attribute(AttributeType.DIMMING_LEVEL):
        features |= SUPPORT_BRIGHTNESS
    if node.has_attribute(AttributeType.COLOR) or node.has_attribute(AttributeType.HUE):
        features |= SUPPORT_COLOR
    if node.has_attribute(AttributeType.COLOR_TEMPERATURE):
        features |= SUPPORT_COLOR_TEMP

    return features


def rgb_list_to_decimal(color):
    """Convert an rgb color from list to decimal representation."""
    return int(int(color[0]) << 16) + (int(color[1]) << 8) + (int(color[2]))


def decimal_to_rgb_list(color):
    """Convert an rgb color from decimal to list representation."""
    return [(color & 0xFF0000) >> 16, (color & 0x00FF00) >> 8, (color & 0x0000FF)]


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add the homee platform for the light integration."""

    devices = []
    for node in helpers.get_imported_nodes(hass, config_entry):
        if not is_light_node(node):
            continue
        devices.append(HomeeLight(node, config_entry))
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: homeassistant, entry: ConfigEntry):
    """Unload a config entry."""


def is_light_node(node: HomeeNode):
    """Determine if a node is controllable as a homee light based on it's profile and attributes."""
    return (
        node.profile
        in [
            NodeProfile.DIMMABLE_LIGHT,
            NodeProfile.DIMMABLE_COLOR_LIGHT,
            NodeProfile.DIMMABLE_EXTENDED_COLOR_LIGHT,
            NodeProfile.DIMMABLE_COLOR_TEMPERATURE_LIGHT,
            NodeProfile.DIMMABLE_LIGHT_WITH_BRIGHTNESS_SENSOR,
            NodeProfile.DIMMABLE_LIGHT_WITH_BRIGHTNESS_AND_PRESENCE_SENSOR,
            NodeProfile.DIMMABLE_LIGHT_WITH_PRESENCE_SENSOR,
            NodeProfile.DIMMABLE_RGBWLIGHT,
            NodeProfile.DIMMABLE_PLUG,
            NodeProfile.DIMMABLE_SWITCH,
        ]
        and AttributeType.ON_OFF in node._attribute_map
    )


class HomeeLight(HomeeNodeEntity, LightEntity):
    """Representation of a homee light."""

    def __init__(self, node: HomeeNode, entry: ConfigEntry):
        """Initialize a homee light."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._supported_features = get_light_features(self)
        _LOGGER.info(f"{node.name}: {node.profile}")

    @property
    def supported_features(self):
        """Return the supported features of the light."""
        return self._supported_features

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self.attribute(AttributeType.DIMMING_LEVEL) * 2.55

    @property
    def hs_color(self):
        """Return the color of the light."""
        # Handle color temperature mode
        if self.has_attribute(AttributeType.COLOR_MODE):
            mode = self.attribute(AttributeType.COLOR_MODE)

            # Light is in color temperature mode
            if mode == 2:
                return None

        rgb = decimal_to_rgb_list(self.attribute(AttributeType.COLOR))
        return color_RGB_to_hs(rgb[0], rgb[1], rgb[2])

    @property
    def min_mireds(self):
        """Return the minimum mireds of the light."""
        return HOMEE_LIGHT_MIN_MIRED

    @property
    def max_mireds(self):
        """Return the maximum mireds of the light."""
        return HOMEE_LIGHT_MAX_MIRED

    @property
    def color_temp(self):
        """Return the color temperature of the light."""
        return color_temperature_kelvin_to_mired(
            self.attribute(AttributeType.COLOR_TEMPERATURE)
        )

    @property
    def is_on(self):
        """Return true if light is on."""
        return self.attribute(AttributeType.ON_OFF)

    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        await self.async_set_value(AttributeType.ON_OFF, 1)

        if ATTR_BRIGHTNESS in kwargs:
            await self.async_set_value(
                AttributeType.DIMMING_LEVEL, kwargs[ATTR_BRIGHTNESS] / 2.55
            )
        if ATTR_COLOR_TEMP in kwargs:
            await self.async_set_value(
                AttributeType.COLOR_TEMPERATURE,
                color_temperature_mired_to_kelvin(kwargs[ATTR_COLOR_TEMP]),
            )
        if ATTR_HS_COLOR in kwargs:
            color = kwargs[ATTR_HS_COLOR]
            await self.async_set_value(
                AttributeType.COLOR,
                rgb_list_to_decimal(color_hs_to_RGB(*color)),
            )

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        await self.async_set_value(AttributeType.ON_OFF, 0)
