"""The homee switch platform."""

import logging

import homeassistant
from homeassistant.components.switch import (
    DEVICE_CLASS_OUTLET,
    DEVICE_CLASS_SWITCH,
    SwitchEntity,
)
from homeassistant.config_entries import ConfigEntry
from pymee.const import AttributeType, NodeProfile
from pymee.model import HomeeAttribute, HomeeNode

from . import HomeeNodeEntity, helpers

_LOGGER = logging.getLogger(__name__)

HOMEE_PLUG_PROFILES = [
    NodeProfile.ON_OFF_PLUG,
    NodeProfile.METERING_PLUG,
    NodeProfile.DIMMABLE_METERING_PLUG,
    NodeProfile.DOUBLE_ON_OFF_PLUG,
    NodeProfile.IMPULSE_PLUG,
]

HOMEE_SWITCH_PROFILES = [
    NodeProfile.DIMMABLE_METERING_SWITCH,
    NodeProfile.METERING_SWITCH,
    NodeProfile.ON_OFF_SWITCH,
    NodeProfile.DOUBLE_ON_OFF_SWITCH,
    NodeProfile.ON_OFF_SWITCH_WITH_BINARY_INPUT,
    NodeProfile.DOUBLE_METERING_SWITCH,
    NodeProfile.SHUTTER_POSITION_SWITCH,
    NodeProfile.ELECTRIC_MOTOR_METERING_SWITCH,
    NodeProfile.ELECTRIC_MOTOR_METERING_SWITCH_WITHOUT_SLAT_POSITION,
]


def get_device_class(node: HomeeNode) -> int:
    """Determine the device class a homee node based on the node profile."""
    if node.profile in HOMEE_PLUG_PROFILES:
        return DEVICE_CLASS_OUTLET
    else:
        return DEVICE_CLASS_SWITCH


def is_switch_node(node: HomeeNode):
    """Determine if a node contains switches based on attributes."""
    return AttributeType.ON_OFF in node._attribute_map and (
        node.profile in HOMEE_PLUG_PROFILES or node.profile in HOMEE_SWITCH_PROFILES
    )


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add the homee platform for the switch component."""

    devices = []
    for node in helpers.get_imported_nodes(hass, config_entry):
        if not is_switch_node(node):
            continue
        switch_count = 0
        for attribute in node.attributes:
            if attribute.type == AttributeType.ON_OFF:
                devices.append(HomeeSwitch(node, config_entry, attribute, switch_count))
                switch_count += 1
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: homeassistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


class HomeeSwitch(HomeeNodeEntity, SwitchEntity):
    """Representation of a homee switch."""

    def __init__(
        self,
        node: HomeeNode,
        entry: ConfigEntry,
        on_off_attribute: HomeeAttribute = None,
        switch_index=-1,
    ):
        """Initialize a homee switch entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._on_off = on_off_attribute
        self._switch_index = switch_index
        self._device_class = get_device_class(node)
        self._unique_id = f"{self._node.id}-switch-{self._on_off.id}"

    @property
    def name(self):
        """Return the display name of this entity."""
        if self._on_off.name != "":
            return f"{self._node.name} {self._on_off.name}"

        if self._switch_index > 0:
            return f"{self._node.name} {self._switch_index + 1}"

        return self._node.name

    @property
    def is_on(self) -> bool:
        """Return True if entity is on."""
        return bool(self._on_off.current_value)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self.async_set_value_by_id(self._on_off.id, 1)

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        await self.async_set_value_by_id(self._on_off.id, 0)

    @property
    def current_power_w(self):
        """Return the current power usage in W."""
        if self.has_attribute(AttributeType.CURRENT_ENERGY_USE):
            return self.attribute(AttributeType.CURRENT_ENERGY_USE)

        return None

    @property
    def device_class(self):
        """Return the class of this node."""
        return self._device_class
