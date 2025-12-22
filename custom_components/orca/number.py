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
        if (
            tag_value.config.type == "float"
            and tag_value.config.adjustable.enabled
            and tag_value.config.id not in EXCLUDED_IDS
        ):
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

        self._attr_native_min_value = config.adjustable.range.min
        self._attr_native_max_value = config.adjustable.range.max
        self._attr_native_step = config.adjustable.range.step
        self._attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float | None:
        """Return the entity value."""
        return self.tag_data.value

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        await self.coordinator.api.set_value_by_id(self.unique_id_, value)
        await self.coordinator.async_request_refresh()
