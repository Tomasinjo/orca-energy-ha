"""Sensor platform for Orca integration."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
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
    """Set up Orca sensors."""
    coordinator: OrcaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for unique_id, tag_value in coordinator.data.items():
        if (
            tag_value.config.type in ["float", "multimode"]
            and not tag_value.config.adjustable.enabled
            and tag_value.config.id not in EXCLUDED_IDS
        ):
            entities.append(OrcaSensor(coordinator, unique_id))

    async_add_entities(entities)


class OrcaSensor(OrcaEntity, SensorEntity):
    """Representation of an Orca sensor."""

    def __init__(self, coordinator: OrcaDataUpdateCoordinator, unique_id: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, unique_id)

        unit = getattr(self.tag_data.config, "unit", "")

        if unit == "°C":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif unit == "%":
            self._attr_device_class = SensorDeviceClass.POWER_FACTOR
            self._attr_state_class = SensorStateClass.MEASUREMENT

        if unit:
            self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self.tag_data.value
