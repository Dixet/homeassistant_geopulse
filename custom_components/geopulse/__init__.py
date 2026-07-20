"""The GeoPulse integration."""

import logging

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util

from .const import CONF_API_URL, CONF_MONITORED_DEVICE, CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up the GeoPulse component."""
    return cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GeoPulse from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    token = entry.options.get(CONF_TOKEN, entry.data.get(CONF_TOKEN))
    api_url = entry.options.get(CONF_API_URL, entry.data.get(CONF_API_URL))
    monitored_device = entry.options.get(CONF_MONITORED_DEVICE, entry.data.get(CONF_MONITORED_DEVICE))
    session = async_get_clientsession(hass)

    if not token or not api_url or not monitored_device:
        _LOGGER.warning("GeoPulse entry is missing required configuration")
        return True

    # Forward setup to platforms (sensor)
    try:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
        )
    except Exception:  # pragma: no cover - defensive
        _LOGGER.exception("Failed to forward entry setup to platforms")

    async def _async_handle_state_change(event: Event) -> None:
        """Send the updated location to the configured API endpoint."""
        if event.data.get("entity_id") != monitored_device:
            return

        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        # Only act when latitude or longitude actually changed
        old_lat = None
        old_lon = None
        new_lat = None
        new_lon = None

        if old_state:
            old_lat = old_state.attributes.get("latitude")
            old_lon = old_state.attributes.get("longitude")

        if new_state:
            new_lat = new_state.attributes.get("latitude")
            new_lon = new_state.attributes.get("longitude")

        if old_lat == new_lat and old_lon == new_lon:
            return

        # Build payload according to requested schema
        device_id = monitored_device.split(".", 1)[1] if "." in monitored_device else monitored_device

        # Battery: prefer device attribute, fallback to sensor.<device>_battery_level, else 0
        battery_level = new_state.attributes.get("battery_level") if new_state else None
        if battery_level is None:
            battery_sensor = f"sensor.{device_id}_battery_level"
            battery_state = hass.states.get(battery_sensor)
            try:
                battery_level = int(battery_state.state) if battery_state and battery_state.state not in ("unknown", "unavailable") else 0
            except Exception:
                battery_level = 0

        payload = {
            "device_id": device_id,
            "timestamp": dt_util.now().isoformat(),
            "location": {
                "latitude": new_lat,
                "longitude": new_lon,
                "accuracy": new_state.attributes.get("gps_accuracy", 0) if new_state else 0,
                "altitude": new_state.attributes.get("altitude", 0) if new_state else 0,
                "speed": new_state.attributes.get("speed", 0) if new_state else 0,
            },
            "battery": {"level": battery_level},
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
                    "Sent GeoPulse location for %s to %s with status %s",
                    monitored_device,
                    api_url,
                    response.status,
                )
                # record last report timestamp and notify any sensors
                try:
                    last_ts = payload.get("timestamp")
                    hass.data[DOMAIN].setdefault(entry.entry_id, {})["last_report"] = last_ts
                    async_dispatcher_send(hass, f"{DOMAIN}_{entry.entry_id}_last_report", last_ts)
                except Exception:
                    _LOGGER.exception("Failed to set last_report in hass.data")
        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.exception("Error calling GeoPulse API: %s", err)

    async def _async_update_listener(hass: HomeAssistant, updated_entry: ConfigEntry) -> None:
        """Reload config entry when options or data are updated."""
        await hass.config_entries.async_reload(updated_entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    unsubscribe = async_track_state_change_event(
        hass, monitored_device, _async_handle_state_change
    )
    entry.async_on_unload(unsubscribe)
    hass.data[DOMAIN][entry.entry_id] = {"unsubscribe": unsubscribe}

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a GeoPulse config entry."""
    # unload platforms
    try:
        await hass.config_entries.async_forward_entry_unload(entry, ["sensor"])
    except Exception:
        _LOGGER.debug("Platform unload failed or not forwarded")

    entry_data = hass.data[DOMAIN].pop(entry.entry_id, None)
    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN, None)

    return True
