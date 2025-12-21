"""Number platform for Orca integration."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, EXCLUDED_IDS
from .coordinator import OrcaDataUpdateCoordinator
from .entity import OrcaEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Orca numbers."""
    coordinator: OrcaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for unique_id, tag_value in coordinator.data.items():
        if tag_value.config.id in EXCLUDED_IDS:
            continue

        config = tag_value.config

        # Check for numeric types that are adjustable
        if config.adjustable and config.type in [
            "curve_shift",
            "percentage",
            "power_factor",
            "temperature",
        ]:
            entities.append(OrcaNumber(coordinator, unique_id))

    async_add_entities(entities)


class OrcaNumber(OrcaEntity, NumberEntity):
    """Representation of an Orca number."""

    def __init__(self, coordinator: OrcaDataUpdateCoordinator, unique_id: str) -> None:
        """Initialize."""
        super().__init__(coordinator, unique_id)
        config = self.tag_data.config

        if config.unit:
            self._attr_native_unit_of_measurement = config.unit

        # Set reasonable defaults, HP doesn't provide min/max in metadata
        if config.type in {"percentage", "power_factor"}:
            self._attr_native_min_value = 0
            self._attr_native_max_value = 100
            self._attr_native_step = 0.1
            self._attr_mode = NumberMode.BOX
        elif config.type == "curve_shift":
            self._attr_native_min_value = -9.9
            self._attr_native_max_value = 9.9
            self._attr_native_step = 0.1
            self._attr_mode = NumberMode.BOX
        elif "electric_heater_on_temp" in config.id:
            self._attr_native_min_value = -30.0  # lowest temp allowed by heat pump
            self._attr_native_max_value = 10.0  # heat pump allows higher values, but not really necessary to have it higher
            self._attr_native_step = 0.1
            self._attr_mode = NumberMode.BOX
        elif config.id in ["buffer_high_temp", "buffer_low_temp"]:
            self._attr_native_min_value = 25.0  # can be set lower, but not necessary
            self._attr_native_max_value = 55.0  # highest temp allowed by heat pump
            self._attr_native_step = 0.1
            self._attr_mode = NumberMode.BOX
        elif config.id == "buffer_on_diff":
            self._attr_native_min_value = 0.0  # lowest allowed by heat pump
            self._attr_native_max_value = 9.0  # highest allowed by heat pump
            self._attr_native_step = 0.1
            self._attr_mode = NumberMode.BOX
        elif config.id == "wh_on_diff":
            self._attr_native_min_value = 0.0  # lowest allowed by heat pump
            self._attr_native_max_value = 8.0  # highest allowed by heat pump
            self._attr_native_step = 0.1
            self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float | None:
        """Return the entity value."""
        return self.tag_data.value

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self.coordinator.api.set_value_by_id(self.unique_id_, value)
        await self.coordinator.async_request_refresh()
