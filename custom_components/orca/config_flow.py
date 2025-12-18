"""Config flow for Orca integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import callback

from .const import (
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
        # self.config_entry = config_entry
        pass

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry, data={**self.config_entry.data, **user_input}
            )
            return self.async_create_entry(title="", data={})

        current_lang = self.config_entry.data.get(CONF_LANGUAGE, LANG_EN)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LANGUAGE, default=current_lang): vol.In(
                        LANGUAGES
                    ),
                }
            ),
        )
