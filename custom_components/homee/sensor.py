"""The homee sensor platform."""

import logging

import homeassistant
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass
)
from homeassistant.config_entries import ConfigEntry
from pymee.const import AttributeType, NodeProfile
from pymee.model import HomeeAttribute, HomeeNode

from . import HomeeNodeEntity, helpers

_LOGGER = logging.getLogger(__name__)

VALID_ATTRIBUTES = [AttributeType.CURRENT_ENERGY_USE,
                    AttributeType.ACCUMULATED_ENERGY_USE]

def get_device_class(attribute: HomeeAttribute) -> int:
    """Determine the device class a homee node based on the node profile."""
    if attribute.type == AttributeType.CURRENT_ENERGY_USE:
        return SensorDeviceClass.POWER
    elif attribute.type == AttributeType.ACCUMULATED_ENERGY_USE:
        return SensorDeviceClass.ENERGY
    else:
        return None

def get_state_class(attribute: HomeeAttribute) -> int:
    """Determine the device class a homee node based on the node profile."""
    if attribute.type == AttributeType.CURRENT_ENERGY_USE:
        return SensorStateClass.MEASUREMENT
    elif attribute.type == AttributeType.ACCUMULATED_ENERGY_USE:
        return SensorStateClass.TOTAL_INCREASING
    else:
        return None

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Add the homee platform for the sensor components."""

    devices = []
    for node in helpers.get_imported_nodes(hass, config_entry):
        sensor_type_counts = {}
        for attribute in node.attributes:
            if attribute.type not in sensor_type_counts.keys():
                sensor_type_counts[attribute.type] = 0
            if attribute.type in VALID_ATTRIBUTES:
                devices.append(HomeeSensor(node, config_entry, attribute, sensor_type_counts))
                sensor_type_counts[attribute.type] += 1
    if devices:
        async_add_devices(devices)


async def async_unload_entry(hass: homeassistant, entry: ConfigEntry):
    """Unload a config entry."""
    return True


class HomeeSensor(HomeeNodeEntity, SensorEntity):
    """Representation of a homee sensor."""
    _attr_has_entity_name = True

    def __init__(
        self,
        node: HomeeNode,
        entry: ConfigEntry,
        measurement_attribute: HomeeAttribute = None,
        sensor_type_counts = {},
    ):
        """Initialize a homee sensor entity."""
        HomeeNodeEntity.__init__(self, node, self, entry)
        self._measurement = measurement_attribute
        self._sensor_counts = sensor_type_counts
        self._device_class = get_device_class(measurement_attribute)
        self._state_class = get_state_class(measurement_attribute)

        self._unique_id = f"{self._node.id}-sensor-{self._measurement.id}"

    @property
    def name(self):
        """Return the display name of this entity."""
        if self._measurement.name != "":
            return f"{self._measurement.name}"

        if self._sensor_counts[self._measurement.type] > 1:
            index = self._sensor_counts[self._measurement.type]
            name = f"{self._device_class} {index}"
            self._sensor_counts[self._measurement.type] -= 1
            return name

        return f"{self._device_class}"

    @property
    def native_value(self):
        return self._measurement.current_value

    @property
    def native_unit_of_measurement(self):
        return self._measurement.unit

    @property
    def state_class(self):
        return self._state_class

    @property
    def device_class(self):
        """Return the class of this node."""
        return self._device_class
