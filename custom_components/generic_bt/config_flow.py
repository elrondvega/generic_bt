"""Config flow for GenericBT integration."""
from __future__ import annotations

import logging
from typing import Any

from bluetooth_data_tools import human_readable_name
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak, async_discovered_service_info
from homeassistant.const import CONF_ADDRESS
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .generic_bt_api.device import GenericBTDevice

_LOGGER = logging.getLogger(__name__)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Generic BT."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(self, discovery_info: BluetoothServiceInfoBleak) -> FlowResult:
        """Handle the bluetooth discovery step."""
        #if discovery_info.name.startswith(UNSUPPORTED_SUB_MODEL):
        #    return self.async_abort(reason="not_supported")

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {"name": human_readable_name(None, discovery_info.name, discovery_info.address)}
        return await self.async_step_user()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the user step to pick discovered device."""
        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            discovery_info = self._discovered_devices[address]
            local_name = discovery_info.name
            await self.async_set_unique_id(discovery_info.address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            device = GenericBTDevice(discovery_info.device)
            # Extract manufacturer data from the discovery info
            if discovery_info.manufacturer_data:
                # Extract the first manufacturer data item and convert its value to hex
                manufacturer_id, manufacturer_data = list(discovery_info.manufacturer_data.items())[0]
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

            try:
                await device.update()
            except BLEAK_EXCEPTIONS:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected error")
                errors["base"] = "unknown"
            else:
                await device.stop()
                return self.async_create_entry(title=local_name,data={CONF_ADDRESS: discovery_info.address})

        if discovery := self._discovery_info:
            self._discovered_devices[discovery.address] = discovery
        else:
            current_addresses = self._async_current_ids()
            for discovery in async_discovered_service_info(self.hass):
                if (
                    discovery.address in current_addresses
                    or discovery.address in self._discovered_devices
                ):
                    continue
                self._discovered_devices[discovery.address] = discovery

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): vol.In(
                    {
                        service_info.address: (f"{service_info.name} ({service_info.address})")
                        for service_info in self._discovered_devices.values()
                    }
                ),
            }
        )
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
