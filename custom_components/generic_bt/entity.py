"""An abstract class common to all Generic BT entities."""
from __future__ import annotations

import logging

from homeassistant.components.bluetooth.passive_update_coordinator import PassiveBluetoothCoordinatorEntity
from homeassistant.helpers import device_registry as dr

from .coordinator import GenericBTCoordinator
from .generic_bt_api.device import GenericBTDevice

_LOGGER = logging.getLogger(__name__)

class GenericBTEntity(PassiveBluetoothCoordinatorEntity[GenericBTCoordinator]):
    """Generic entity encapsulating common features of Generic BT device."""

    _device: GenericBTDevice
    _attr_has_entity_name = True

    def __init__(self, coordinator: GenericBTCoordinator) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self._device = coordinator.device
        self._address = coordinator.ble_device.address
        self._attr_unique_id = coordinator.base_unique_id
        # Ensure manufacturer_data is properly formatted
        manufacturer_data = self._device.manufacturer_data
        if "manufacturer_id" not in manufacturer_data and manufacturer_data:
            # Extract the manufacturer_id from the keys
            manufacturer_id = list(manufacturer_data.keys())[0]
            manufacturer_data["manufacturer_id"] = manufacturer_id
        self._attr_extra_state_attributes = manufacturer_data
        self._attr_device_info = {
            "connections":{(dr.CONNECTION_BLUETOOTH, self._address)},
            "name":coordinator.device_name
        }
