# Current UV Index – Home Assistant Integration

This custom integration provides **current and forecast UV index** from [currentuvindex.com](https://currentuvindex.com/).  
It creates a device with the following entities:

- `sensor.current_uv_index`
- `sensor.today_min_uv_index` (with `time` attribute)
- `sensor.today_max_uv_index` (with `time` attribute)
- `sensor.tomorrow_min_uv_index` (with `time` attribute)
- `sensor.tomorrow_max_uv_index` (with `time` attribute)

## Features
- Fetches **current UV index**.
- Provides **min and max forecast** for today and tomorrow.  
- Min values exclude **0 at night**, reporting instead the lowest **positive UV**.  
- Each min/max sensor exposes the **time of occurrence** as an attribute.  
- Configurable update interval (default: 30 minutes).  
- Supports translations (`en`, `it`).

## Installation

### Via HACS
1. Go to HACS → Integrations → **Custom repositories**.
2. Add repository URL: `https://github.com/matteovisotto/hass-currentuvindex`.
3. Category: Integration.
4. Install, restart Home Assistant.

### Manual
1. Copy `custom_components/current_uvindex` into your Home Assistant config folder.
2. Restart Home Assistant.

## Configuration
Once installed, add via **UI**:
- Go to *Settings → Devices & Services → Add Integration → Current UV Index*.
- Enter your **latitude** and **longitude**.
- Set **update interval** (minutes).

## Example
Example of sensors created:

