from homeassistant.components.water_heater import WaterHeaterEntity, WaterHeaterEntityFeature
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from .coordinator import OrcaDevice
from homeassistant.core import callback
from typing import Any
from logging import getLogger

_LOGGER = getLogger(__name__)
DOMAIN = 'orca'

WH_ACTION_IDLE = "idle"
WH_ACTION_HEAT = "heating"

async def async_setup_entry(hass, entry, async_add_entities, discovery_info=None):
    _LOGGER.info(f'Configuring ORCA water heater')
    orca = hass.data[DOMAIN]['orca_obj']
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
            [OrcaWaterHeater(coordinator, orca)]
        )

class OrcaWaterHeater(OrcaDevice, WaterHeaterEntity):
    def __init__(self, coordinator, orca):
        super().__init__(coordinator, orca)
        self.orca = orca
        self.coordinator = coordinator
        self._attr_name = 'orca_water_heater'
        self._attr_unique_id = 'b53d1ef8-17b9-49ca-8c82-73f16a4b9b5b'
        self._attr_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_min_temp = 30.0
        self._attr_max_temp = 60.0
        self._attr_current_temperature = float()
        self._attr_target_temperature = float()
        
        self._attr_current_operation = WH_ACTION_IDLE
        self._attr_operation_list = [WH_ACTION_IDLE, WH_ACTION_HEAT]

        self._attr_supported_features = (
            WaterHeaterEntityFeature.TARGET_TEMPERATURE
            | WaterHeaterEntityFeature.AWAY_MODE
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        
        self._attr_target_temperature = self.coordinator.data['2_Temp_vode_sanitarna'].value
        self._attr_current_temperature = self.coordinator.data['2_Poti3'].value

        self._attr_current_operation = WH_ACTION_IDLE

        valve_status = self.coordinator.data['2_Preklop_PV1'].value
        if valve_status == 'hot_water':
            self._attr_current_operation = self.coordinator.data['2_Rezim_delov_TC'].value
        
        self.async_write_ha_state()

    @property
    def is_away_mode_on(self):
        """Return True if hot water heating is disabled"""
        if self.coordinator.data['2_SV_vklop'].value == 1:
            return False
        else:
            return True

    async def async_set_temperature(self, **kwargs: Any) -> None:
        if temperature := kwargs.get(ATTR_TEMPERATURE, 0) * 10:
            resp = await self.orca.set_value('2_Temp_vode_sanitarna', temperature)
        await self.coordinator.async_request_refresh()

    async def async_turn_away_mode_on(self) -> None:
        """Disable hot water heating."""
        await self.orca.set_value('2_SV_vklop', 0)
        await self.coordinator.async_request_refresh()

    async def async_turn_away_mode_off(self) -> None:
        """Enable hot water heating."""
        await self.orca.set_value('2_SV_vklop', 1)
        await self.coordinator.async_request_refresh()