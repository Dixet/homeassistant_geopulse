"""Config flow for Geopulse."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers import selector

from .const import CONF_API_URL, CONF_MONITORED_DEVICE, CONF_TOKEN, DOMAIN


class GeopulseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Geopulse."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(title="Geopulse", data=user_input)

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
