"""Config flow for GeoPulse."""

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import CONF_GEOPULSE_URL, CONF_MONITORED_DEVICE, CONF_TOKEN, DOMAIN


class GeoPulseConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GeoPulse."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            # Get the friendly name of the monitored device for the entry title
            monitored_device = user_input[CONF_MONITORED_DEVICE]
            device_id = monitored_device.split(".", 1)[1] if "." in monitored_device else monitored_device
            
            # Try to get the friendly name from the current state
            hass = self.hass
            if hass and hass.states:
                state = hass.states.get(monitored_device)
                device_friendly_name = state.name if state and state.name else device_id
            else:
                device_friendly_name = device_id
            
            entry_title = f"GeoPulse {device_friendly_name}"
            return self.async_create_entry(title=entry_title, data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_TOKEN): str,
                vol.Required(CONF_GEOPULSE_URL): str,
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
            # If monitored device changed, update the entry title
            new_monitored_device = user_input.get(CONF_MONITORED_DEVICE)
            if new_monitored_device:
                device_id = new_monitored_device.split(".", 1)[1] if "." in new_monitored_device else new_monitored_device
                
                # Try to get the friendly name from the current state
                hass = self.hass
                if hass and hass.states:
                    state = hass.states.get(new_monitored_device)
                    device_friendly_name = state.name if state and state.name else device_id
                else:
                    device_friendly_name = device_id
                
                new_title = f"GeoPulse {device_friendly_name}"
                # Update the config entry title
                self.hass.config_entries.async_update_entry(
                    self._config_entry, title=new_title
                )
            
            return self.async_create_entry(title="", data=user_input)

        data = self._config_entry.options or self._config_entry.data
        data_schema = vol.Schema(
            {
                vol.Required(CONF_TOKEN, default=data.get(CONF_TOKEN, "")): str,
                vol.Required(CONF_GEOPULSE_URL, default=data.get(CONF_GEOPULSE_URL, "")): str,
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
