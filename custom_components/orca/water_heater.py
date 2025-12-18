"""Water heater platform for Orca integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.water_heater import (
    WaterHeaterEntity,
    WaterHeaterEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_LANGUAGE, DOMAIN, LANG_EN, LANG_SI
from .coordinator import OrcaDataUpdateCoordinator
from .entity import OrcaEntity

OPERATION_IDLE = "idle"
OPERATION_HEATING = "heating"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Orca water heater platform."""
    coordinator: OrcaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    # Circuit 4 is water heater as defined in config.yml
    if 4 in coordinator.api.available_circuits:
        entities.append(OrcaWaterHeater(coordinator, "wh_temp_top"))
    async_add_entities(entities)


class OrcaWaterHeater(OrcaEntity, WaterHeaterEntity):
    """Representation of an Orca Water Heater."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_min_temp = 25.0
    _attr_max_temp = 60.0
    _attr_supported_features = (
        WaterHeaterEntityFeature.TARGET_TEMPERATURE | WaterHeaterEntityFeature.AWAY_MODE
    )
    _attr_operation_list = [OPERATION_IDLE, OPERATION_HEATING]

    def __init__(self, coordinator: OrcaDataUpdateCoordinator, unique_id: str) -> None:
        """Initialize."""
        super().__init__(coordinator, unique_id)

        if coordinator.config_entry.data.get(CONF_LANGUAGE, LANG_EN) == LANG_SI:
            self._attr_name = "Bojler"
        else:
            self._attr_name = "Water Heater"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_water_heater"

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self.tag_data.value

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if desired := self.coordinator.data.get("wh_desired_temp"):
            return desired.value
        return None

    @property
    def current_operation(self) -> str:
        """Return current operation."""
        valve = self.coordinator.data.get("valve_pos")
        pump_running = self.coordinator.data.get("outdoor_unit_pump")

        if valve and valve.value == "hot_water" and pump_running and pump_running.value:
            return OPERATION_HEATING
        return OPERATION_IDLE

    @property
    def is_away_mode_on(self) -> bool | None:
        """Return true if away mode is on."""
        # Away mode = Water heating disabled
        if tag := self.coordinator.data.get("wh_turned_on"):
            return not tag.value
        return None

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temp := kwargs.get("temperature")) is not None:
            await self.coordinator.api.set_value_by_id("wh_desired_temp", temp)
        await self.coordinator.async_request_refresh()

    async def async_turn_away_mode_on(self) -> None:
        """Turn away mode on (Disable DHW)."""
        await self.coordinator.api.set_value_by_id("wh_turned_on", False)
        await self.coordinator.async_request_refresh()

    async def async_turn_away_mode_off(self) -> None:
        """Turn away mode off (Enable DHW)."""
        await self.coordinator.api.set_value_by_id("wh_turned_on", True)
        await self.coordinator.async_request_refresh()
