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
from pymee import Homee
from pymee.const import AttributeType, NodeProfile
from pymee.model import HomeeAttribute, HomeeNode

from . import HomeeNodeHelper
from .const import DOMAIN, HOMEE_LIGHT_MAX_MIRED, HOMEE_LIGHT_MIN_MIRED

_LOGGER = logging.getLogger(__name__)


def get_light_features(node: HomeeNodeHelper, default=0) -> int:
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
    homee: Homee = hass.data[DOMAIN][config_entry.entry_id]

    devices = []
    for node in homee.nodes:
        if not is_light_node(node):
            continue
        devices.append(HomeeLight(node))
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
        ]
        and AttributeType.ON_OFF in node._attribute_map
    )


class HomeeLight(LightEntity):
    """Representation of a homee light."""

    def __init__(self, node: HomeeNode):
        """Initialize a homee light."""
        self._node = node
        self.node = HomeeNodeHelper(node, self)
        # self._remove_node_updated_listener = None
        self._supported_features = get_light_features(self.node)
        _LOGGER.info(f"{node.name}: {node.profile}")

    async def async_added_to_hass(self) -> None:
        """Add the homee light to home assistant."""

        # def handle_attribute_update(event):
        #     node = event.data.get(ATTR_NODE)
        #     if node == self._node.id:
        #         self.schedule_update_ha_state()

        # self._close_attribute_listener = self.hass.bus.async_listen(
        #     EVENT_HOMEE_ATTRIBUTE_CHANGED, handle_attribute_update
        # )

        # self._remove_node_updated_listener = self._node.add_on_changed_listener(
        #     self._on_node_updated
        # )
        self.node.register_listener()

    async def async_will_remove_from_hass(self):
        """Cleanup the entity."""
        # if self._remove_node_updated_listener != None:
        #     self._remove_node_updated_listener()
        self.node.clear_listener()

    @property
    def should_poll(self) -> bool:
        """Return if the light should poll."""
        return False

    @property
    def unique_id(self):
        """Return the unique ID of the light."""
        return self._node.id

    @property
    def name(self):
        """Return the display name of this light."""
        return self._node.name

    @property
    def supported_features(self):
        """Return the supported features of the light."""
        return self._supported_features

    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self.node.attribute(AttributeType.DIMMING_LEVEL) * 2.55

    @property
    def hs_color(self):
        """Return the color of the light."""
        # Handle color temperature mode
        if self.node.has_attribute(AttributeType.COLOR_MODE):
            mode = self.node.attribute(AttributeType.COLOR_MODE)

            # Light is in color temperature mode
            if mode == 2:
                return None

        rgb = decimal_to_rgb_list(self.node.attribute(AttributeType.COLOR))
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
            self.node.attribute(AttributeType.COLOR_TEMPERATURE)
        )

    @property
    def is_on(self):
        """Return true if light is on."""
        return self.node.attribute(AttributeType.ON_OFF)

    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        await self.node.async_set_value(AttributeType.ON_OFF, 1)

        if ATTR_BRIGHTNESS in kwargs:
            await self.node.async_set_value(
                AttributeType.DIMMING_LEVEL, kwargs[ATTR_BRIGHTNESS] / 2.55
            )
        if ATTR_COLOR_TEMP in kwargs:
            await self.node.async_set_value(
                AttributeType.COLOR_TEMPERATURE,
                color_temperature_mired_to_kelvin(kwargs[ATTR_COLOR_TEMP]),
            )
        if ATTR_HS_COLOR in kwargs:
            color = kwargs[ATTR_HS_COLOR]
            await self.node.async_set_value(
                AttributeType.COLOR,
                rgb_list_to_decimal(color_hs_to_RGB(*color)),
            )

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        await self.node.async_set_value(AttributeType.ON_OFF, 0)

    async def async_update(self):
        """Fetch new state data for this light."""
        self._node._remap_attributes()

    def _on_node_updated(self, node: HomeeNode, attribute: HomeeAttribute):
        self.schedule_update_ha_state()
