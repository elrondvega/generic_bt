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
    manufacturer_data = coordinator.device.manufacturer_data
    # Ensure manufacturer_id is included in the data
    if "manufacturer_id" not in manufacturer_data and manufacturer_data:
        # Extract the manufacturer_id from the keys
        manufacturer_id = list(manufacturer_data.keys())[0]
        manufacturer_data["manufacturer_id"] = manufacturer_id

    if manufacturer_data.get("manufacturer_id") == 65535 or manufacturer_data.get("manufacturer_id") == 1076:
        async_add_entities([GenericBTManufacturerDataSensor(coordinator)])

class GenericBTManufacturerDataSensor(GenericBTEntity, SensorEntity):
    """Representation of a Generic BT Manufacturer Data Sensor."""

    _attr_name = "Manufacturer Data"

    def __init__(self, coordinator: GenericBTCoordinator) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

    def _get_manufacturer_data(self) -> dict:
        """Return the manufacturer data from the device."""
        manufacturer_data = self._device.manufacturer_data
        # Ensure manufacturer_id is included in the data
        if "manufacturer_id" not in manufacturer_data and manufacturer_data:
            # Extract the manufacturer_id from the keys
            manufacturer_id = list(manufacturer_data.keys())[0]
            manufacturer_data["manufacturer_id"] = manufacturer_id
        return manufacturer_data

    @property
    def native_value(self) -> float | dict:
        """Return the size value or manufacturer data based on manufacturer_id."""
        manufacturer_data = self._get_manufacturer_data()
        if manufacturer_data.get("manufacturer_id") == 65535:
            return manufacturer_data.get("size", 0.0)
        return manufacturer_data

    @property
    def extra_state_attributes(self) -> dict[str, any]:
        """Return the device state attributes."""
        manufacturer_data = self._get_manufacturer_data()
        if manufacturer_data.get("manufacturer_id") == 65535:
            return {"size": manufacturer_data.get("size", 0.0), "mac_address": manufacturer_data.get("mac_address"), "manufacturer_data": manufacturer_data.get(65535)}
        return manufacturer_data

    @property
    def icon(self) -> str:
        """Return the icon for the sensor."""
        return "mdi:bluetooth"
