"""Update platform for GeoPulse."""

import logging
from datetime import timedelta

from aiohttp import ClientError, ClientResponseError, ClientTimeout
from homeassistant.components.update import UpdateEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo

from .const import CONF_GEOPULSE_URL, DOMAIN

_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(minutes=10)


class GeoPulseVersionUpdate(UpdateEntity):
    """Update entity for GeoPulse version."""

    def __init__(self, hass, entry_id, api_url, device_info=None):
        self.hass = hass
        self._entry_id = entry_id
        self._api_url = api_url.rstrip("/")
        self._attr_name = "GeoPulse"
        self._unique_id = f"{entry_id}_version"
        self._installed_version = None
        self._latest_version = None
        self._update_available = False
        self._release_url = None
        self._attr_device_info = device_info

    @property
    def name(self):
        return self._attr_name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def installed_version(self):
        return self._installed_version

    @property
    def latest_version(self):
        return self._latest_version

    @property
    def release_url(self):
        return self._release_url

    @property
    def in_progress(self):
        return False

    @property
    def can_install(self):
        return self._update_available

    @property
    def state(self):
        return "on" if self._update_available else "off"

    # async def async_install(self, version, backup, **kwargs):
    #     """Install the update."""
    #     if self._release_url:
    #         self.hass.components.websocket.async_send_message(
    #             f"open_url:{self._release_url}"
    #         )
    #     return True

    async def async_update(self):
        """Fetch version data from GeoPulse API."""
        session = async_get_clientsession(self.hass)
        url = f"{self._api_url}/api/version/status"

        try:
            async with session.get(
                url,
                timeout=ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self._installed_version = data.get("currentVersion")
                    self._latest_version = data.get("latestVersion")
                    self._update_available = data.get("updateAvailable", False)
                    self._release_url = data.get("releaseUrl")
                else:
                    self._installed_version = None
                    self._latest_version = None
                    self._update_available = False
                    self._release_url = None
        except (ClientError, ClientResponseError, Exception):
            self._installed_version = None
            self._latest_version = None
            self._update_available = False
            self._release_url = None

    _attr_should_poll = True
    _attr_update_interval = SCAN_INTERVAL


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up GeoPulse update entity from a config entry."""
    api_url = entry.options.get(CONF_GEOPULSE_URL, entry.data.get(CONF_GEOPULSE_URL))
    
    # Get device info from hass.data
    device_info = hass.data.get(DOMAIN, {}).get(entry.entry_id, {}).get("device_info")

    if api_url:
        update_entity = GeoPulseVersionUpdate(hass, entry.entry_id, api_url, device_info)
        async_add_entities([update_entity], True)