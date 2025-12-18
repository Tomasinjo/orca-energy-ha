"""Climate platform for Orca integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import CONF_LANGUAGE, DOMAIN, LANG_EN, LANG_SI, LOGGER
from .coordinator import OrcaDataUpdateCoordinator
from .entity import OrcaEntity
from .orca_api import CIRCUIT_NAME_MAP_SI

# Mapping of Orca modes to HA modes
MODE_MAPPING = {
    "auto": HVACMode.HEAT_COOL,
    "cool": HVACMode.COOL,
    "heat": HVACMode.HEAT,
}

REVERSE_MODE_MAPPING = {
    HVACMode.HEAT_COOL: "auto",
    HVACMode.COOL: "cool",
    HVACMode.HEAT: "heat",
    HVACMode.OFF: "off",  # cannot be directly used
}

ACTION_MAPPING = {
    "idle": HVACAction.IDLE,
    "heating": HVACAction.HEATING,
    "cooling": HVACAction.COOLING,
    "defrost": HVACAction.HEATING,  # Treat defrost as heating for consistency
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Orca climate platform."""
    coordinator: OrcaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # iterates thru integers representing available circuits, create separate climate entities for each circuit
    # circuts 1 and 2 are used for room heating, usually floor and/or radiators
    entities = [
        OrcaClimate(coordinator, circuit_id)
        for circuit_id in coordinator.api.available_circuits
        if circuit_id in [1, 2]
    ]
    async_add_entities(entities)


class OrcaClimate(OrcaEntity, ClimateEntity):
    """Representation of an Orca Climate Device."""

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.COOL, HVACMode.HEAT_COOL]
    _attr_target_temperature_step = 0.1

    def __init__(self, coordinator: OrcaDataUpdateCoordinator, circuit_id: int) -> None:
        """Initialize the climate entity."""
        self._circuit_id = circuit_id
        super().__init__(coordinator, self._get_unique_id("hc_room_temp"))

        # support for both languages
        eng_name: str = self.coordinator.data.get(self._get_unique_id("hc_name")).value
        if coordinator.config_entry.data.get(CONF_LANGUAGE, LANG_EN) == LANG_SI:
            self._attr_name = str(CIRCUIT_NAME_MAP_SI[eng_name]).title()
        else:
            self._attr_name = eng_name
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_climate_{eng_name.lower()}"
        )

        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
        )

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._get_value("hc_room_temp")

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        if not self._single_temp_in_use():
            return None
        return self._get_value("hc_desired_day_temp")

    @property
    def target_temperature_high(self) -> float | None:
        """Return the highbound target temperature."""
        if self._single_temp_in_use():
            return None
        return self._get_value("hc_desired_day_temp")

    @property
    def target_temperature_low(self) -> float | None:
        """Return the lowbound target temperature."""
        if self._single_temp_in_use():
            return None
        return self._get_value("hc_desired_night_temp")

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, cool mode."""
        is_on = self._get_value("hc_turned_on")
        if not is_on:
            return HVACMode.OFF

        mode_val = self._get_value("hc_mode")
        return MODE_MAPPING.get(mode_val, HVACMode.HEAT_COOL)

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation if supported."""
        valve_status = self._get_value("valve_pos", convert_to_unique=False)
        pump_running = self._get_value("hc_pump_status")  # on circuit level

        # "room_heating" indicates heating circuit active (and not hot water)
        if valve_status == "room_heating" and pump_running:
            hp_status = self._get_value("current_state", convert_to_unique=False)
            return ACTION_MAPPING.get(hp_status, HVACAction.IDLE)
        return HVACAction.IDLE

    def _get_value(self, id_: str, convert_to_unique: bool = True) -> Any:
        """Safe getter for mapped keys."""
        if convert_to_unique:
            id_ = self._get_unique_id(id_)
        if id_ in self.coordinator.data:
            return self.coordinator.data[id_].value
        return None

    def _get_unique_id(self, id_: str) -> str:
        """Get the unique ID for a given tag ID based on circuit ID."""
        return f"{id_}_{self._circuit_id}"

    def _single_temp_in_use(self) -> bool:
        """Check if we are in 24h regime. If yes, only single temp is used."""
        if self._get_value("hc_24_sch"):
            return True
        return False  # Orca mono doesnt support 24h and will not return value

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""

        if (temp_low := kwargs.get("target_temp_low")) is not None:
            await self.coordinator.api.set_value_by_id(
                self._get_unique_id("hc_desired_night_temp"), value=temp_low
            )

        if (temp_high := kwargs.get("target_temp_high")) is not None:
            await self.coordinator.api.set_value_by_id(
                self._get_unique_id("hc_desired_day_temp"), value=temp_high
            )

        if (temp := kwargs.get("temperature")) is not None:
            await self.coordinator.api.set_value_by_id(
                self._get_unique_id("hc_desired_day_temp"), value=temp
            )

        await self.coordinator.async_request_refresh()

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        val = REVERSE_MODE_MAPPING.get(hvac_mode)
        if val is None:
            LOGGER.error("Unknown mode: %s", hvac_mode)
            return

        if val == "off":
            await self.coordinator.api.set_value_by_id("hc_turned_on", False)
        else:
            # Ensure On, then set mode
            await self.coordinator.api.set_value_by_id("hc_turned_on", True)
            await self.coordinator.api.set_value_by_id("hc_mode", val)

        await self.coordinator.async_request_refresh()
