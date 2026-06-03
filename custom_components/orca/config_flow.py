"""Config flow for Orca integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback

from .const import (
    CONF_CIRCUITS,
    CONF_HOSTNAME,
    CONF_LANGUAGE,
    CONF_PASSWORD,
    CONF_USERNAME,
    DOMAIN,
    LANG_EN,
    LANGUAGES,
    LOGGER,
)
from .orca_api import OrcaApi


class OrcaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Orca."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OrcaOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOSTNAME]
            username = user_input[CONF_USERNAME]
            password = user_input[CONF_PASSWORD]

            orca = OrcaApi(username, password, host)
            try:
                await orca.initialize()
                await orca.fetch_all()
            except Exception as err:
                LOGGER.error("Connection error: %s", err)
                errors["base"] = str(err)
            else:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=host,
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOSTNAME): str,
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                    vol.Required(CONF_LANGUAGE, default=LANG_EN): vol.In(LANGUAGES),
                }
            ),
            errors=errors,
        )

class OrcaOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            # Collect selected circuits from individual checkboxes
            circuits = []
            for circuit_id in ["1", "2", "3", "4", "5"]:
                if user_input.get(f"circuit_{circuit_id}", False):
                    circuits.append(int(circuit_id))
            
            new_data = {**self._entry.data}
            # Only store circuits if non-empty, otherwise remove to use auto-detect
            if circuits:
                new_data[CONF_CIRCUITS] = circuits
            elif CONF_CIRCUITS in new_data:
                del new_data[CONF_CIRCUITS]
            
            self.hass.config_entries.async_update_entry(
                self._entry, data=new_data
            )
            return self.async_create_entry(title="", data={})

        current_lang = self._entry.data.get(CONF_LANGUAGE, LANG_EN)
        current_circuits = self._entry.data.get(CONF_CIRCUITS, [])
        
        # If circuits are not configured, run auto-detection to pre-select
        if not current_circuits:
            host = self._entry.data[CONF_HOSTNAME]
            username = self._entry.data[CONF_USERNAME]
            password = self._entry.data[CONF_PASSWORD]
            
            orca = OrcaApi(username, password, host)
            try:
                await orca.initialize()
                # Get detected circuits (excluding circuit 0 which is always present)
                current_circuits = [c for c in orca.available_circuits if c != 0]
            except Exception as err:
                LOGGER.error("Error detecting circuits: %s", err)
                # Fall back to empty list if detection fails
                current_circuits = []

        # Build schema with individual checkboxes for each circuit
        schema_dict = {
            vol.Required(CONF_LANGUAGE, default=current_lang): vol.In(
                LANGUAGES
            ),
        }
        
        circuit_options = {
            "1": "Heating Circuit 1",
            "2": "Heating Circuit 2",
            "3": "Solar",
            "4": "Domestic Hot Water",
            "5": "Buffer Tank",
        }
        
        for circuit_id, label in circuit_options.items():
            schema_dict[
                vol.Optional(
                    f"circuit_{circuit_id}",
                    default=(int(circuit_id) in current_circuits)
                )
            ] = bool
        
        data_schema = vol.Schema(schema_dict)
        
        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
        )
