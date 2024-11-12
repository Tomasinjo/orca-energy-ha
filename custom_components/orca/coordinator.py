from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from logging import getLogger
from datetime import timedelta
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

DOMAIN = 'orca'
_LOGGER = getLogger(__name__)

class Coordinate(DataUpdateCoordinator):
    """https://developers.home-assistant.io/docs/integration_fetching_data/"""

    def __init__(self, hass, orca):
        """Initialize Orca coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Orca Sensors",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )
        self.orca = orca
        self.hass = hass

    async def _async_update_data(self):
        """
        Fetch data from API endpoint.
        """
        try:
            data = await self.orca.sensor_status_all()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")
        
        return {
            obj.tag: obj for obj in data
        }
        
class OrcaDevice(CoordinatorEntity):
    """Base class for all ORCA entities."""
    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, "orca_device_1234")},
            name="Orca Heat Pump",
            manufacturer="Orca",
            model="Orca",
            sw_version="1.0",
        )