"""Data update coordinator for the Orca integration."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, LOGGER
from .orca_api import OrcaApi, OrcaTagValue


class OrcaDataUpdateCoordinator(DataUpdateCoordinator[dict[str, OrcaTagValue]]):
    """Class to manage fetching Orca data."""

    def __init__(self, hass: HomeAssistant, orca_api: OrcaApi) -> None:
        """Initialize."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )
        self.api = orca_api
        self.data: dict[str, OrcaTagValue]

    async def _async_update_data(self) -> dict[str, OrcaTagValue]:
        """Fetch data from API endpoint."""
        try:
            # fetch_all returns a list of OrcaTagValue
            data_list = await self.api.fetch_all()

            # Convert list to dict keyed by unique_id (from orca_api)
            return {item.config.unique_id: item for item in data_list}

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
