"""Switch platform for Orca integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up Orca switches."""
    coordinator: OrcaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    for unique_id, tag_value in coordinator.data.items():
        if (
            tag_value.config.type == "boolean"
            and tag_value.config.adjustable.enabled
            and tag_value.config.id not in EXCLUDED_IDS
        ):
            entities.append(OrcaSwitch(coordinator, unique_id))

    async_add_entities(entities)


class OrcaSwitch(OrcaEntity, SwitchEntity):
    """Representation of an Orca switch."""

    @property
    def is_on(self) -> bool | None:
        """Return true if device is on."""
        return self.tag_data.value

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.coordinator.api.set_value_by_id(self.unique_id_, True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.coordinator.api.set_value_by_id(self.unique_id_, False)
        await self.coordinator.async_request_refresh()
