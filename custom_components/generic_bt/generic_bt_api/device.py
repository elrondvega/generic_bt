"""generic bt device"""

from uuid import UUID
import asyncio
import logging
from contextlib import AsyncExitStack

from bleak import BleakClient
from bleak.exc import BleakError

_LOGGER = logging.getLogger(__name__)


from typing import Any

class GenericBTDevice:
    """Generic BT Device Class"""
    def __init__(self, ble_device):
        self._ble_device = ble_device
        self._client: BleakClient | None = None
        self._client_stack = AsyncExitStack()
        self._lock = asyncio.Lock()
        self._manufacturer_data: dict[int, str] = {}
        # Initialize manufacturer_data with the device's address
        self._manufacturer_data["device_address"] = ble_device.address

    async def update(self):
        pass

    async def stop(self):
            pass

    @property
    def connected(self):
        return not self._client is None

    async def get_client(self):
        async with self._lock:
            if not self._client:
                _LOGGER.debug("Connecting")
                try:
                    self._client = await self._client_stack.enter_async_context(BleakClient(self._ble_device, timeout=30))
                except asyncio.TimeoutError as exc:
                    _LOGGER.debug("Timeout on connect", exc_info=True)
                    raise IdealLedTimeout("Timeout on connect") from exc
                except BleakError as exc:
                    _LOGGER.debug("Error on connect", exc_info=True)
                    raise IdealLedBleakError("Error on connect") from exc
            else:
                _LOGGER.debug("Connection reused")

    async def write_gatt(self, target_uuid, data):
        await self.get_client()
        uuid_str = "{" + target_uuid + "}"
        uuid = UUID(uuid_str)
        data_as_bytes = bytearray.fromhex(data)
        await self._client.write_gatt_char(uuid, data_as_bytes, True)

    async def read_gatt(self, target_uuid):
        await self.get_client()
        uuid_str = "{" + target_uuid + "}"
        uuid = UUID(uuid_str)
        data = await self._client.read_gatt_char(uuid)
        print(data)
        return data

    def update_from_advertisement(self, service_info: Any) -> None:
        """Update the device from a Bluetooth advertisement."""
        if service_info.manufacturer_data:
            # Extract the first manufacturer data item and convert its value to hex
            manufacturer_id, manufacturer_data = list(service_info.manufacturer_data.items())[0]
            # handle different manufacturers
            if manufacturer_id == 1076:
                self._manufacturer_data = {manufacturer_id: bytes(manufacturer_data[6:]).hex()}
            elif manufacturer_id == 65535:
                # 0x25 = 37
                if manufacturer_data[15] == 37:
                    self._manufacturer_data = {manufacturer_id: bytes(manufacturer_data).hex(), "mac_address": bytes(manufacturer_data[2:8]).hex(), "size": (manufacturer_data[18] << 8 | manufacturer_data[17]) / 100  }
                else:
                    self._manufacturer_data = {manufacturer_id: bytes(manufacturer_data).hex(), "mac_address": bytes(manufacturer_data[2:8]).hex() }
            else:
                self._manufacturer_data = {manufacturer_id: bytes(manufacturer_data).hex()}

    @property
    def manufacturer_data(self) -> dict[int, str]:
        """Return the manufacturer data."""
        return self._manufacturer_data
