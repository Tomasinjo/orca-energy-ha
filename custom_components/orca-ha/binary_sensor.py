from logging import getLogger
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

_LOGGER = getLogger(__name__)
DOMAIN = 'orca'
BINARY_SENSOR_TYPES = ['boolean']

async def async_setup_entry(hass, entry, async_add_entities, discovery_info=None):
    _LOGGER.info(f'Configuring ORCA binary sensors')
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        OrcaBinarySensor(coordinator, tag) for tag, obj in coordinator.data.items() if obj.type in BINARY_SENSOR_TYPES
    )

class OrcaBinarySensor(CoordinatorEntity, BinarySensorEntity):
    def __init__(self, coordinator, tag):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)
        self.tag = tag
        _type = self.coordinator.data[self.tag].type
        if _type not in ['boolean']:
            return
        _LOGGER.debug(f'Setting up sensor {self.coordinator.data[self.tag].name}')
        self._attr_name = self.coordinator.data[self.tag].name
        self._attr_unique_id = self.coordinator.data[self.tag].name

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_is_on  = self.coordinator.data[self.tag].value
        self.async_write_ha_state()