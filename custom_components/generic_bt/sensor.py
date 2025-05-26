"""Support for Generic BT sensor to store manufacturer data."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import GenericBTCoordinator
from .entity import GenericBTEntity

# Initialize the logger
_LOGGER = logging.getLogger(__name__)
PARALLEL_UPDATES = 0

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up Generic BT device based on a config entry."""
    coordinator: GenericBTCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GenericBTManufacturerDataSensor(coordinator)])

class GenericBTManufacturerDataSensor(GenericBTEntity, SensorEntity):
    """Representation of a Generic BT Manufacturer Data Sensor."""

    _attr_name = "Manufacturer Data"

    def __init__(self, coordinator: GenericBTCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

    @property
    def native_value(self) -> dict:
        """Return the manufacturer data as the sensor value."""
        return self._device.manufacturer_data

    @property
    def extra_state_attributes(self) -> dict:
        """Return the device state attributes."""
        return {
            "manufacturer_data": self._device.manufacturer_data,
        }

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        return "mdi:bluetooth"
