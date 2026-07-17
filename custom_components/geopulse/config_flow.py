"""Config flow for GeoPulse."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_API_URL, CONF_MONITORED_DEVICE, CONF_TOKEN, DOMAIN


class GeoPulseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GeoPulse."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="GeoPulse", data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_TOKEN): str,
                vol.Required(CONF_API_URL): str,
                vol.Required(CONF_MONITORED_DEVICE): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["device_tracker", "person"],
                        multiple=False,
                    )
                ),
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return GeoPulseOptionsFlowHandler(config_entry)


class GeoPulseOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle option updates for GeoPulse."""

    def __init__(self, config_entry):
        self._config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data = self._config_entry.options or self._config_entry.data
        data_schema = vol.Schema(
            {
                vol.Required(CONF_TOKEN, default=data.get(CONF_TOKEN, "")): str,
                vol.Required(CONF_API_URL, default=data.get(CONF_API_URL, "")): str,
                vol.Required(
                    CONF_MONITORED_DEVICE,
                    default=data.get(CONF_MONITORED_DEVICE, ""),
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(
                        domain=["device_tracker", "person"],
                        multiple=False,
                    )
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=data_schema)
