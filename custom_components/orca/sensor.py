from logging import getLogger
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from .coordinator import OrcaDevice


_LOGGER = getLogger(__name__)
DOMAIN = 'orca'
SENSOR_TYPES = ['multimode', 'power_factor', 'temperature']

async def async_setup_entry(hass, entry, async_add_entities, discovery_info=None):
    _LOGGER.info(f'Configuring ORCA sensors')
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        OrcaSensor(coordinator, tag) for tag, obj in coordinator.data.items() if obj.type in SENSOR_TYPES
    )

class OrcaSensor(OrcaDevice, SensorEntity):
    def __init__(self, coordinator, tag):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.tag = tag
        _type = self.coordinator.data[self.tag].type
        if _type not in ['temperature', 'multimode', 'power_factor']:
            return
        _LOGGER.debug(f'Setting up sensor {self.coordinator.data[self.tag].name}')
        if _type != 'multimode':  # this is not a supported option
            self._attr_device_class = _type
        _unit = self.coordinator.data[self.tag].unit
        _LOGGER.debug(f'Unit is {_unit}')
        if _unit:
            self._attr_native_unit_of_measurement = _unit
        self._attr_name = self.coordinator.data[self.tag].name
        self._attr_unique_id = self.coordinator.data[self.tag].name

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value  = self.coordinator.data[self.tag].value
        self.async_write_ha_state()
