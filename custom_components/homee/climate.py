"""The homee climate platform."""

import logging

import homeassistant
from homeassistant.components.climate import (
    ATTR_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_RANGE,
    ClimateEntity,
)
from homeassistant.components.climate.const import HVAC_MODE_HEAT
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT
from pymee import Homee
from pymee.const import AttributeType, NodeProfile
from pymee.model import HomeeAttribute, HomeeNode

from . import HomeeNodeHelper
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

HOMEE_UNIT_TO_HA_UNIT = {"°C": TEMP_CELSIUS, "°F": TEMP_FAHRENHEIT}


def get_climate_features(node: HomeeNodeHelper, default=0) -> int:
    """Determine the supported climate features of a homee node based on the available attributes."""
    features = default

    if node.has_attribute(AttributeType.TARGET_TEMPERATURE):
        features |= SUPPORT_TARGET_TEMPERATURE
    if node.has_attribute(AttributeType.TARGET_TEMPERATURE_LOW) and node.has_attribute(
        AttributeType.TARGET_TEMPERATURE_HIGH
    ):
        features |= SUPPORT_TARGET_TEMPERATURE_RANGE

    return features


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add the homee platform for the light integration."""
    homee: Homee = hass.data[DOMAIN][config_entry.entry_id]

    devices = []
    for node in homee.nodes:
        if not is_climate_node(node):
            continue
        devices.append(HomeeClimate(node))
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: homeassistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


def is_climate_node(node: HomeeNode):
    """Determine if a node is controllable as a homee light based on it's profile and attributes."""
    return node.profile in [
        NodeProfile.RADIATOR_THERMOSTAT,
        NodeProfile.THERMOSTAT_WITH_HEATING_AND_COOLING,
        NodeProfile.HEATING_SYSTEM,
    ]


class HomeeClimate(ClimateEntity):
    """Representation of a homee climate device."""

    def __init__(self, node: HomeeNode):
        """Initialize a homee climate entity."""
        self._node = node
        self.node = HomeeNodeHelper(node, self)
        self._supported_features = get_climate_features(self.node)
        _LOGGER.info(f"{node.name}: {node.profile}")

    async def async_added_to_hass(self) -> None:
        """Add the homee climate device to home assistant."""
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
    def supported_features(self):
        """Return the supported features of the entity."""
        return self._supported_features

    @property
    def temperature_unit(self) -> str:
        """Return the temperature unit of the device."""
        return HOMEE_UNIT_TO_HA_UNIT[
            self.node.get_attribute(AttributeType.TEMPERATURE).unit
        ]

    @property
    def hvac_modes(self):
        """Return the available hvac operation modes."""
        return [HVAC_MODE_HEAT]

    @property
    def hvac_mode(self):
        """Return the hvac operation mode."""
        return HVAC_MODE_HEAT

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self.node.attribute(AttributeType.TEMPERATURE)

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self.node.attribute(AttributeType.TARGET_TEMPERATURE)

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self.node.get_attribute(AttributeType.TARGET_TEMPERATURE).step_value

    async def async_set_temperature(self, **kwargs) -> None:
        """Set new target temperature."""

        if ATTR_TEMPERATURE in kwargs:
            await self.node.async_set_value(
                AttributeType.TARGET_TEMPERATURE, kwargs[ATTR_TEMPERATURE]
            )

    async def async_update(self):
        """Fetch new state data for this light."""
        self._node._remap_attributes()

    def _on_node_updated(self, node: HomeeNode, attribute: HomeeAttribute):
        self.schedule_update_ha_state()
