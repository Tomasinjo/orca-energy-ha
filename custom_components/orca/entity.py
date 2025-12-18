"""Base entity class for Orca integration."""

from __future__ import annotations

from homeassistant.const import EntityCategory
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_LANGUAGE, DOMAIN, LANG_EN, LANG_SI
from .coordinator import OrcaDataUpdateCoordinator
from .orca_api import OrcaTagValue


class OrcaEntity(CoordinatorEntity[OrcaDataUpdateCoordinator]):
    """Defines a base Orca entity."""

    def __init__(
        self,
        coordinator: OrcaDataUpdateCoordinator,
        unique_id_: str,  # as defined in config.yml
        entity_description=None,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.unique_id_ = unique_id_
        if entity_description:
            self.entity_description = entity_description

        # Determine name and unique ID from the coordinator data
        tag_data = self.coordinator.data[self.unique_id_]

        # get language according to setup
        selected_lang = self.coordinator.config_entry.data.get(CONF_LANGUAGE, LANG_EN)

        if selected_lang == LANG_SI:
            # Use slovenian entity name
            self._attr_name = tag_data.config.final_name_si
        else:
            # Use english entity name
            self._attr_name = tag_data.config.final_name

        # Unique ID must be globally unique. Combine entry_id + API unique_id
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{unique_id_}"
        self._attr_has_entity_name = False

        self._attr_entity_category = self._get_category(tag_data)

    def _get_category(self, tag_data: OrcaTagValue) -> EntityCategory | None:
        """Determine the category based on config flags."""
        config = tag_data.config

        # Configuration section
        if config.adjustable:
            return EntityCategory.CONFIG

        # diagnostic section
        if config.type in ["power_factor", "boolean"]:
            return EntityCategory.DIAGNOSTIC

        # default sensor section
        return None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.entry_id)},
            name="Orca Heat Pump",
            manufacturer="Orca",
            model="Heat Pump",
        )

    @property
    def tag_data(self) -> OrcaTagValue:
        """Return the current data for this specific tag."""
        return self.coordinator.data[self.unique_id_]

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return super().available and self.unique_id_ in self.coordinator.data
