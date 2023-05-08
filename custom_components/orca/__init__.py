
from logging import getLogger
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .orca_api import OrcaApi
from .coordinator import Coordinate

_LOGGER = getLogger(__name__)
PLATFORMS = ["sensor", "binary_sensor", "climate", "water_heater"]
DOMAIN = 'orca'

async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry,
    ):
    _LOGGER.info("Creating setup entry")
    user = entry.data["username"]
    passwd = entry.data["password"]
    host = entry.data["hostname"]

    orca = OrcaApi(user, passwd, host)
    coordinator  = Coordinate(hass, orca)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    hass.data[DOMAIN]['orca_obj'] = orca
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
