"""Support for generic bluetooth devices."""

import logging

from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN
from .coordinator import GenericBTCoordinator
from .generic_bt_api.device import GenericBTDevice


_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.BINARY_SENSOR, Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Generic BT from a config entry."""
    assert entry.unique_id is not None
    hass.data.setdefault(DOMAIN, {})
    address: str = entry.data[CONF_ADDRESS]
    ble_device = bluetooth.async_ble_device_from_address(hass, address.upper(), True)
    if not ble_device:
        raise ConfigEntryNotReady(f"Could not find Generic BT Device with address {address}")
    device = GenericBTDevice(ble_device)

    # Get the service info to extract manufacturer data
    service_info = bluetooth.async_last_service_info(hass, ble_device.address)
    if service_info and service_info.manufacturer_data:
        # Extract the first manufacturer data item and convert its value to hex
        manufacturer_id, manufacturer_data = list(service_info.manufacturer_data.items())[0]
        # handle different manufacturers
        if manufacturer_id == 1076:
            device._manufacturer_data = {manufacturer_id: bytes(manufacturer_data[6:]).hex()}
        elif manufacturer_id == 65535:
            # 0x25 = 37
            if manufacturer_data[15] == 37:
                device._manufacturer_data = {manufacturer_id: bytes(manufacturer_data).hex(), "mac_address": bytes(manufacturer_data[2:8]).hex(), "size": (manufacturer_data[18] << 8 | manufacturer_data[17]) / 100  }
            else:
                device._manufacturer_data = {manufacturer_id: bytes(manufacturer_data).hex(), "mac_address": bytes(manufacturer_data[2:8]).hex() }
        else:
            device._manufacturer_data = {manufacturer_id: bytes(manufacturer_data).hex()}

    coordinator = hass.data[DOMAIN][entry.entry_id] = GenericBTCoordinator(hass, _LOGGER, ble_device, device, entry.title, entry.unique_id, True)
    entry.async_on_unload(coordinator.async_start())

    if not await coordinator.async_wait_ready():
        raise ConfigEntryNotReady(f"{address} is not advertising state")

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.config_entries.async_entries(DOMAIN):
            hass.data.pop(DOMAIN)

    return unload_ok
