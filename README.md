<H3><img alt="GeoPulse icon" src="https://github.com/user-attachments/assets/90fa1384-2525-43a0-8ace-ac5194251a69" style="height: 3em; vertical-align: middle;"/>
GeoPulse Home Assistant Integration</H3>

A custom Home Assistant integration for the [GeoPulse](https://github.com/tess1o/geopulse) geo tracking service. It reports monitored device location changes to GeoPulse and exposes a sensor for the last reported timestamp.

## Purpose

This integration:

- Sends location updates for a monitored `device_tracker` or `person` entity to GeoPulse.
- Creates a `sensor` entity that tracks the last time the device location was reported.
- Supports runtime configuration via Home Assistant config flow and options flow.

## Installation

### HACS installation

The easiest way to install is using the button

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=dixet&repository=homeassistant_geopulse&category=integration)

Or find the integration in HACS yourself:

1. From the Home Assistant sidebar, select HACS. This will open the Home Assistant Community Store dashboard
2. Select the search bar at the top of the dashboard and search for `GeoPulse`.
3. Select `GeoPulse` and choose Download

Restart Home Assistant after installation.

### Manual installation

1. Copy the contents of the `custom_components` folder from this repository into your Home Assistant configuration directory.
2. The target path should be:

   ```text
   <home_assistant_config>/custom_components/geopulse
   ```

3. Restart Home Assistant.

## Configuration

1. In Home Assistant, go to **Settings → Devices & Services → Add Integration**.
2. Search for `GeoPulse` and follow the setup flow.
3. Provide the required values:
   - `token` 
   - `api_url`
   - monitored device or person entity

The token entered here should be the same as the token you enter in GeoPulse. See the GeoPulse documentation for more details:
- https://geopulse.cc/docs/user-guide/gps-sources/home_assistant

Please note that using a person entity will not report speed (and battery) information and is therefore less suited for logging to GeoPulse.

## Usage

After installation and setup:

- The integration will report observed location changes for the configured monitored entity.
- It exposes a sensor entity representing the last time GeoPulse was updated.
- The integration can be edited from the Home Assistant UI via the integration options.

