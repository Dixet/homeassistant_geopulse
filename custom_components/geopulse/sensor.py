"""Sensor platform for GeoPulse."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, CONF_MONITORED_DEVICE


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
        else:
            # Legacy: only timestamp was sent
            self._state = data
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)

    def _handle_legacy_signal(self, timestamp: str) -> None:
        """Handle legacy signal (timestamp only)."""
        self._state = timestamp
        self.hass.loop.call_soon_threadsafe(self.async_write_ha_state)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up GeoPulse sensors from a config entry."""
    monitored_device = entry.options.get(CONF_MONITORED_DEVICE, entry.data.get(CONF_MONITORED_DEVICE))
    if not monitored_device:
        async_add_entities([], True)
        return

    sensor = GeoPulseLastReportSensor(hass, entry.entry_id, monitored_device)
    async_add_entities([sensor], True)
