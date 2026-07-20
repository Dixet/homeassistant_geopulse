"""The GeoPulse integration."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util

from .const import CONF_API_URL, CONF_MONITORED_DEVICE, CONF_TOKEN, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass, config):
    """Set up the GeoPulse component."""
    return True


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

        old_lat = None
        old_lon = None
        old_accuracy = None
        old_altitude = None
        old_speed = None
        old_battery = None
        new_lat = None
        new_lon = None
        new_accuracy = None
        new_altitude = None
        new_speed = None
        new_battery = None

        if old_state:
            old_lat = old_state.attributes.get("latitude")
            old_lon = old_state.attributes.get("longitude")
            old_accuracy = old_state.attributes.get("gps_accuracy")
            old_altitude = old_state.attributes.get("altitude")
            old_speed = old_state.attributes.get("speed")
            old_battery = old_state.attributes.get("battery_level")

        if new_state:
            new_lat = new_state.attributes.get("latitude")
            new_lon = new_state.attributes.get("longitude")
            new_accuracy = new_state.attributes.get("gps_accuracy")
            new_altitude = new_state.attributes.get("altitude")
            new_speed = new_state.attributes.get("speed")
            new_battery = new_state.attributes.get("battery_level")

        # only report if any of the relevant attributes have changed
        if old_lat == new_lat and old_lon == new_lon and old_accuracy == new_accuracy and old_altitude == new_altitude and old_speed == new_speed and old_battery == new_battery:
            return

        # do not report when lat or lon is None (e.g., when device is not reporting location)
        if new_lat is None or new_lon is None:
            _LOGGER.debug("Skipping GeoPulse report for %s: lat or lon is None", monitored_device)
            return

        # Build payload according to requested schema
        device_id = monitored_device.split(".", 1)[1] if "." in monitored_device else monitored_device

        # Battery: prefer device attribute, fallback to sensor.<device>_battery_level, else 0
        battery_level = new_battery if new_battery is not None else None
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
                "accuracy": new_accuracy if new_accuracy is not None else 0,
                "altitude": new_altitude if new_altitude is not None else 0,
                "speed": new_speed if new_speed is not None else 0,
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
                # record last report timestamp and location data and notify any sensors
                try:
                    last_ts = payload.get("timestamp")
                    location_data = payload.get("location", {})
                    battery_data = payload.get("battery", {})
                    
                    hass.data[DOMAIN].setdefault(entry.entry_id, {})
                    hass.data[DOMAIN][entry.entry_id]["last_report"] = last_ts
                    hass.data[DOMAIN][entry.entry_id]["latitude"] = location_data.get("latitude")
                    hass.data[DOMAIN][entry.entry_id]["longitude"] = location_data.get("longitude")
                    hass.data[DOMAIN][entry.entry_id]["accuracy"] = location_data.get("accuracy")
                    hass.data[DOMAIN][entry.entry_id]["altitude"] = location_data.get("altitude")
                    hass.data[DOMAIN][entry.entry_id]["speed"] = location_data.get("speed")
                    hass.data[DOMAIN][entry.entry_id]["battery"] = battery_data.get("level")
                    
                    # Send signal with full data
                    async_dispatcher_send(
                        hass, 
                        f"{DOMAIN}_{entry.entry_id}_last_report", 
                        {
                            "timestamp": last_ts,
                            "latitude": location_data.get("latitude"),
                            "longitude": location_data.get("longitude"),
                            "accuracy": location_data.get("accuracy"),
                            "altitude": location_data.get("altitude"),
                            "speed": location_data.get("speed"),
                            "battery": battery_data.get("level")
                        }
                    )
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
