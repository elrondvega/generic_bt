"""Support for Generic BT binary sensor."""
from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, Schema
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

    if manufacturer_data.get("manufacturer_id") != 65535 and manufacturer_data.get("manufacturer_id") != 1076:
        async_add_entities([GenericBTBinarySensor(coordinator)])
        platform = entity_platform.async_get_current_platform()
        platform.async_register_entity_service("write_gatt", Schema.WRITE_GATT.value, "write_gatt")
        platform.async_register_entity_service("read_gatt", Schema.READ_GATT.value, "read_gatt")


class GenericBTBinarySensor(GenericBTEntity, BinarySensorEntity):
    """Representation of a Generic BT Binary Sensor."""

    _attr_name = None

    def __init__(self, coordinator: GenericBTCoordinator) -> None:
        """Initialize the Device."""
        super().__init__(coordinator)

    @property
    def is_on(self):
        return self._device.connected

    async def write_gatt(self, target_uuid, data):
        await self._device.write_gatt(target_uuid, data)
        self.async_write_ha_state()

    async def read_gatt(self, target_uuid):
        await self._device.read_gatt(target_uuid)
        self.async_write_ha_state()
