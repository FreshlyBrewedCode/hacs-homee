"""The homee switch platform."""

import logging

import homeassistant
from homeassistant.components.switch import (
    SwitchDeviceClass,
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
    NodeProfile.DOUBLE_ON_OFF_PLUG,
    NodeProfile.IMPULSE_PLUG,
]

HOMEE_SWITCH_PROFILES = [
    NodeProfile.METERING_SWITCH,
    NodeProfile.ON_OFF_SWITCH,
    NodeProfile.DOUBLE_ON_OFF_SWITCH,
    NodeProfile.ON_OFF_SWITCH_WITH_BINARY_INPUT,
    NodeProfile.DOUBLE_METERING_SWITCH,
    NodeProfile.IMPULSE_RELAY,
    NodeProfile.GARAGE_DOOR_OPERATOR,
    NodeProfile.GARAGE_DOOR_IMPULSE_OPERATOR,
]

HOMEE_SWITCH_ATTRIBUTES = [
    AttributeType.ON_OFF,
    AttributeType.IMPULSE,
    AttributeType.LIGHT_IMPULSE,
    AttributeType.OPEN_PARTIAL_IMPULSE,
    AttributeType.AUTOMATIC_MODE_IMPULSE,
    AttributeType.BRIEFLY_OPEN_IMPULSE,
    AttributeType.PERMANENTLY_OPEN_IMPULSE,
    AttributeType.SLAT_ROTATION_IMPULSE,
    AttributeType.VENTILATE_IMPULSE,
]


def get_device_class(node: HomeeNode) -> int:
    """Determine the device class a homee node based on the node profile."""
    if node.profile in HOMEE_PLUG_PROFILES:
        return SwitchDeviceClass.OUTLET
    else:
        return SwitchDeviceClass.SWITCH


def is_switch_node(node: HomeeNode):
    """Determine if a node contains switches based on attributes."""
    for attribute in node.attributes:
        if attribute.type in HOMEE_SWITCH_ATTRIBUTES:
            return (
                node.profile in HOMEE_PLUG_PROFILES
                or node.profile in HOMEE_SWITCH_PROFILES
            )
    return False


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add the homee platform for the switch component."""

    devices = []
    for node in helpers.get_imported_nodes(hass, config_entry):
        if not is_switch_node(node):
            continue
        switch_count = 0
        for attribute in node.attributes:
            if attribute.type in HOMEE_SWITCH_ATTRIBUTES and attribute.editable:
                devices.append(HomeeSwitch(node, config_entry, attribute, switch_count))
                switch_count += 1
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: homeassistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


class HomeeSwitch(HomeeNodeEntity, SwitchEntity):
    """Representation of a homee switch."""

    _attr_has_entity_name = True

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
        """Return the display name of this entity. Entity is the main feature of a device when the index == 0"""
        for key, val in AttributeType.__dict__.items():
            if val == self._on_off.type:
                attribute_name = key

        # special impulses should always be named descriptive
        if attribute_name.find("_IMPULSE") > -1:
            return attribute_name[0, attribute_name.find("_IMPULSE")]

        if self._switch_index <= 0:
            return None

        if self._switch_index > 0:
            return f"switch {self._switch_index + 1}"

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
        else:
            return None

    @property
    def today_energy_kwh(self):
        """Return the total power usage in kWh."""
        if self.has_attribute(AttributeType.ACCUMULATED_ENERGY_USE):
            return self.attribute(AttributeType.ACCUMULATED_ENERGY_USE)
        else:
            return None

    @property
    def device_class(self):
        """Return the class of this node."""
        return self._device_class
