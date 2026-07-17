# GeoPulse Home Assistant Integration

A custom Home Assistant integration for the `GeoPulse` geo tracking service. It reports monitored device location changes to GeoPulse and exposes a sensor for the last reported timestamp.

## Purpose

This integration:

- Sends location updates for a monitored `device_tracker` or `person` entity to GeoPulse.
- Creates a `sensor` entity that tracks the last time the device location was reported.
- Supports runtime configuration via Home Assistant config flow and options flow.

## Installation

### Manual installation

1. Copy the contents of the `custom_components` folder from this repository into your Home Assistant configuration directory.
2. The target path should be:

   ```text
   <home_assistant_config>/custom_components/geopulse
   ```

3. Restart Home Assistant.

### HACS installation

1. Add this repository to HACS as a custom repository.
2. In HACS, go to **Integrations → Explore & Add Repositories** and add the repository manually if it is not already listed.
3. Search for `GeoPulse` in HACS
4. Install `GeoPulse` from HACS.
5. Restart Home Assistant after installation.

## Configuration

1. In Home Assistant, go to **Settings → Devices & Services → Add Integration**.
2. Search for `GeoPulse` and follow the setup flow.
3. Provide the required values:
   - `token` 
   - `api_url`
   - monitored device or person entity

The token entered here should be the same as the token you enter in GeoPulse. See the GeoPulse documentation for more details:

- https://geopulse.cc/docs/user-guide/gps-sources/home_assistant


## Usage

After installation and setup:

- The integration will report observed location changes for the configured monitored entity.
- It exposes a sensor entity representing the last time GeoPulse was updated.
- The integration can be edited from the Home Assistant UI via the integration options.

