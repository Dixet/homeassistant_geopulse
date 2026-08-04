"""Sensor platform for GeoPulse."""

import logging
from datetime import timedelta

from aiohttp import ClientError, ClientResponseError, ClientTimeout
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import CONF_GEOPULSE_URL, DOMAIN, CONF_MONITORED_DEVICE

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=10)


class GeoPulseLastReportSensor(SensorEntity):
    """Sensor that shows the last time location was reported."""

    def __init__(self, hass, entry_id, monitored_device):
        self.hass = hass
        self._entry_id = entry_id
        self._monitored_device = monitored_device
        device_id = monitored_device.split(".", 1)[1] if "." in monitored_device else monitored_device
        # Use entity's friendly name if available
        state = hass.states.get(monitored_device)
        friendly = state.name if state and state.name else device_id
        self._attr_name = f"GeoPulse {friendly} Last Reported"
        self._unique_id = f"{entry_id}_{device_id}_last_reported"
        self._state = None
        self._latitude = None
        self._longitude = None
        self._accuracy = None
        self._altitude = None
        self._speed = None
        self._battery = None
        self._unsub = None
        self._response = None

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "latitude": self._latitude,
            "longitude": self._longitude,
            "accuracy": self._accuracy,
            "altitude": self._altitude,
            "speed": self._speed,
            "battery": self._battery,
            "response": self._response,
        }

    async def async_added_to_hass(self):
        """Subscribe to dispatcher updates and set initial state."""
        signal = f"{DOMAIN}_{self._entry_id}_last_report"
        self._unsub = async_dispatcher_connect(self.hass, signal, self._handle_signal)
        signal_legacy = f"{DOMAIN}_{self._entry_id}_last_reported"
        self._unsub_legacy = async_dispatcher_connect(self.hass, signal_legacy, self._handle_legacy_signal)

        # initial value from hass.data if present
        entry_data = self.hass.data.get(DOMAIN, {}).get(self._entry_id, {})
        last = entry_data.get("last_report") or entry_data.get("last_reported")
        if last:
            self._state = last
            self._latitude = entry_data.get("latitude")
            self._longitude = entry_data.get("longitude")
            self._accuracy = entry_data.get("accuracy")
            self._altitude = entry_data.get("altitude")
            self._speed = entry_data.get("speed")
            self._battery = entry_data.get("battery")
            self._response = entry_data.get("response")

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
        if getattr(self, "_unsub_legacy", None):
            self._unsub_legacy()

    def _handle_signal(self, data) -> None:
        """Handle new location data from the dispatcher."""
        if isinstance(data, dict):
            self._state = data.get("timestamp")
            self._latitude = data.get("latitude")
            self._longitude = data.get("longitude")
            self._accuracy = data.get("accuracy")
            self._altitude = data.get("altitude")
            self._speed = data.get("speed")
            self._battery = data.get("battery")
            self._response = data.get("response")
        else:
            # Legacy: only timestamp was sent
            self._state = data
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

    def _handle_legacy_signal(self, timestamp: str) -> None:
        """Handle legacy signal (timestamp only)."""
        self._state = timestamp
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)


class GeoPulseHealthSensor(SensorEntity):
    """Sensor that shows the health status of the GeoPulse API."""

    def __init__(self, hass, entry_id, api_url):
        """Initialize the sensor."""
        self.hass = hass
        self._entry_id = entry_id
        self._api_url = api_url.rstrip("/")
        self._attr_name = "GeoPulse Health"
        self._unique_id = f"{entry_id}_health"
        self._state = None
        self._message = None
        self._database = None
        self._status = None

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def state(self):
        return self._status

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            "message": self._message,
            "database": self._database,
            "status": self._status,
        }

    async def async_update(self):
        """Fetch health data from GeoPulse API."""
        session = async_get_clientsession(self.hass)
        url = f"{self._api_url}/api/health"

        try:
            async with session.get(
                url,
                headers={
                    "Content-Type": "application/json",
                },
                timeout=ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self._message = data.get("message")
                    health_data = data.get("data", {})
                    self._database = health_data.get("database")
                    self._status = health_data.get("status")
                else:
                    self._status = f"HTTP {response.status}"
                    self._message = "Error"
                    self._database = None
        except (ClientError, ClientResponseError, Exception) as e:
            self._status = "Error"
            self._message = str(e)
            self._database = None

    _attr_should_poll = True
    _attr_update_interval = SCAN_INTERVAL


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up GeoPulse sensors from a config entry."""
    monitored_device = entry.options.get(CONF_MONITORED_DEVICE, entry.data.get(CONF_MONITORED_DEVICE))
    api_url = entry.options.get(CONF_GEOPULSE_URL, entry.data.get(CONF_GEOPULSE_URL))

    sensors = []

    if monitored_device:
        sensor = GeoPulseLastReportSensor(hass, entry.entry_id, monitored_device)
        sensors.append(sensor)

    if api_url:
        health_sensor = GeoPulseHealthSensor(hass, entry.entry_id, api_url)
        sensors.append(health_sensor)

    async_add_entities(sensors, True)
