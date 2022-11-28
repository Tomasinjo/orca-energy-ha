import voluptuous as vol
from .orca_api import OrcaApi
from homeassistant import data_entry_flow, config_entries, exceptions
from homeassistant.core import HomeAssistant
from typing import Any
from logging import getLogger

_LOGGER = getLogger(__name__)

async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    orca = OrcaApi(
        data["username"],
        data["password"],
        data["hostname"],
    )
    success = await hass.async_add_executor_job(orca.test_connection)
    if not success:
        raise CannotConnect
    return {"title": data["hostname"]}

class OrcaConfigFlow(config_entries.ConfigFlow, domain='orca'):
    async def async_step_user(self, user_input=None):
        data_schema = {
            vol.Required("username"): str,
            vol.Required("password"): str,
            vol.Required("hostname"): str,
        }
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                await self.async_set_unique_id(user_input['hostname'])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema), errors=errors)



class CannotConnect(exceptions.HomeAssistantError):
    """ Cannot connect to orca"""