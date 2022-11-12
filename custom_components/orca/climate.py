from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from logging import getLogger
from homeassistant.components.climate import ClimateEntity
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.climate.const import HVACMode

_LOGGER = getLogger(__name__)
DOMAIN = 'orca'

MODE_MAPPING = {
    "auto": HVACMode.HEAT_COOL,
    "cool": HVACMode.COOL,
    "heat": HVACMode.HEAT
}

REVERSE_MODE_MAPPING = {
    'heat_cool': 3,
    'cool': 2,
    'heat': 1
}


async def async_setup_entry(hass, entry, async_add_entities, discovery_info=None):
    _LOGGER.info(f'Configuring ORCA climate')
    orca = hass.data[DOMAIN]['orca_obj']
    coordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
            [OrcaClimate(coordinator, orca)]
        )

class OrcaClimate(CoordinatorEntity, ClimateEntity):
    def __init__(self, coordinator, orca):
        super().__init__(coordinator, orca)
        _LOGGER.debug('Climate creating class HEHE')
        self.orca = orca
        self.coordinator = coordinator
        self._attr_name = 'orca_hp'
        self._attr_unique_id = 'b53d1ef8-17b9-49ca-8c82-73f16a4b9b5a'
        self._attr_temperature_unit = TEMP_CELSIUS
        self._attr_current_temperature = float()
        #self._attr_target_temperature = float()
        self._attr_target_temperature_high = float()
        self._attr_target_temperature_low = float()
        self._attr_target_temperature_step = 0.1
        self._attr_hvac_mode = HVACMode.HEAT_COOL
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.HEAT_COOL]
        #self._attr_hvac_action = ''  # todo current hvac state  
        self._attr_supported_features = 3

    @callback
    def _handle_coordinator_update(self) -> None:
        _LOGGER.debug(f"climate callback update")
        """Handle updated data from the coordinator."""
        self._attr_current_temperature = self.coordinator.data['2_Temp_Prostora'].value
        #self._attr_target_temperature = self.coordinator.data['2_Temp_prostor_dnevna'].value
        self._attr_target_temperature_high = self.coordinator.data['2_Temp_prostor_dnevna'].value
        self._attr_target_temperature_low  = self.coordinator.data['2_Temp_prostor_nocna'].value
        self._attr_hvac_mode = MODE_MAPPING.get(self.coordinator.data['2_Rezim_MK1'].value)
        _LOGGER.debug(f"""Climate update: 
        _attr_current_temperature: {self._attr_current_temperature}
        self._attr_target_temperature_high: {self._attr_target_temperature_high}
        self._attr_target_temperature_low: {self._attr_target_temperature_low}
        self._attr_hvac_mode: {self._attr_hvac_mode}""")
        self.async_write_ha_state()


# 2022-11-01 00:43:33.235 DEBUG (SyncWorker_6) [custom_components.orca.climate] climate setting temperature: kw={'temperature': 20.3, 'entity_id': ['climate.orca_hp']}
# 2022-11-01 00:42:19.296 DEBUG (SyncWorker_1) [custom_components.orca.climate] climate setting temperature: kw={'target_temp_low': 20.1, 'target_temp_high': 20.4, 'entity_id': ['climate.orca_hp']}
    def set_temperature(self, **kwargs):
        _LOGGER.debug(f"climate setting temperature: kw={kwargs}")
        """Set new target temperature."""
        if temperature := kwargs.get('target_temp_low', 0) * 10:
            resp = self.orca.set_value('2_Temp_prostor_nocna', temperature)
        if temperature := kwargs.get('target_temp_high', 0) * 10:
            resp = self.orca.set_value('2_Temp_prostor_dnevna', temperature)
        _LOGGER.debug(f'Set temperature response: {resp}')
        self.coordinator.async_refresh()


    def set_hvac_mode(self, hvac_mode) -> None:
        _LOGGER.debug(f"climate setting mode: mode={hvac_mode}")
        mode = REVERSE_MODE_MAPPING.get(hvac_mode)
        if mode is None:
            _LOGGER.error(f'Unknown mode: {hvac_mode}')
            return
        resp = self.orca.set_value('2_Rezim_MK1', mode)
        _LOGGER.debug(f'Set mode response: {resp}')
        self.coordinator.async_refresh()










