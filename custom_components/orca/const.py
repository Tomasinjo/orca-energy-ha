"""Constants for the Orca integration."""

from logging import Logger, getLogger

DOMAIN = "orca"
LOGGER: Logger = getLogger(__package__)

CONF_HOSTNAME = "hostname"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"

CONF_LANGUAGE = "Language"
LANG_EN = "English"
LANG_SI = "Slovenščina"
LANGUAGES = [LANG_EN, LANG_SI]

# IDs (from config.yml) that should not be created as entities because they are handled elsewhere
# used only when configuring settable entities (switch, number)
EXCLUDED_IDS = {
    # set by climate entities
    "hc_desired_day_temp",
    "hc_desired_night_temp",
    "hc_turned_on",
    # set by water heater entity
    "wh_turned_on",
    "wh_desired_temp",
    # for internal purposes only
    "hc_name",
}
