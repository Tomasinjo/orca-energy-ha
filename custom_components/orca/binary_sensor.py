"""Binary sensor platform for Orca integration."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
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
    """Set up Orca binary sensors."""
    coordinator: OrcaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for unique_id, tag_value in coordinator.data.items():
        if tag_value.config.id in EXCLUDED_IDS:
            continue

        config = tag_value.config

        if config.type == "boolean" and not config.adjustable:
            entities.append(OrcaBinarySensor(coordinator, unique_id))

    async_add_entities(entities)


class OrcaBinarySensor(OrcaEntity, BinarySensorEntity):
    """Representation of an Orca binary sensor."""

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        return self.tag_data.value
