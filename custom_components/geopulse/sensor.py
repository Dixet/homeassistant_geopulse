"""Sensor platform for Geopulse."""

from homeassistant.components.sensor import SensorEntity

from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Geopulse sensors from a config entry."""
    async_add_entities([], True)
