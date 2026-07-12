"""The Geopulse integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONF_API_URL, CONF_MONITORED_DEVICE, CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up the Geopulse component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Geopulse from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    token = entry.data.get(CONF_TOKEN)
    api_url = entry.data.get(CONF_API_URL)
    monitored_device = entry.data.get(CONF_MONITORED_DEVICE)
    session = async_get_clientsession(hass)

    if not token or not api_url or not monitored_device:
        _LOGGER.warning("Geopulse entry is missing required configuration")
        return True

    async def _async_handle_state_change(event: Event) -> None:
        """Send the updated location to the configured API endpoint."""
        if event.data.get("entity_id") != monitored_device:
            return

        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        payload = {
            "entity_id": monitored_device,
            "old_state": old_state.state if old_state else None,
            "new_state": new_state.state if new_state else None,
        }

        try:
            async with session.post(
                api_url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                timeout=10,
            ) as response:
                response.raise_for_status()
                _LOGGER.debug(
                    "Sent Geopulse update for %s to %s with status %s",
                    monitored_device,
                    api_url,
                    response.status,
                )
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Error calling Geopulse API: %s", err)

    unsubscribe = async_track_state_change_event(
        hass, monitored_device, _async_handle_state_change
    )
    entry.async_on_unload(unsubscribe)
    hass.data[DOMAIN][entry.entry_id] = {"unsubscribe": unsubscribe}

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Geopulse config entry."""
    entry_data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if entry_data and entry_data.get("unsubscribe"):
        entry_data["unsubscribe"]()

    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN, None)

    return True
