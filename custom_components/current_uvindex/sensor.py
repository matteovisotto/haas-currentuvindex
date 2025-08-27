from __future__ import annotations
import logging
from datetime import datetime, timedelta, timezone
import aiohttp
import async_timeout

from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    CoordinatorEntity,
    UpdateFailed,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

DEVICE_MANUFACTURER = "CurrentUVIndex.com"
DEVICE_MODEL = "UV Index API"
UNIT = ""


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator = UVIndexDataUpdateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    sensors = [
        CurrentUVIndexSensor(coordinator, entry),
        TodayMaxUVSensor(coordinator, entry),
        TodayMinUVSensor(coordinator, entry),
        TomorrowMaxUVSensor(coordinator, entry),
        TomorrowMinUVSensor(coordinator, entry),
    ]
    async_add_entities(sensors)


class UVIndexDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.latitude = entry.data.get("latitude", hass.config.latitude)
        self.longitude = entry.data.get("longitude", hass.config.longitude)
        update_minutes = entry.options.get("update_interval", entry.data.get("update_interval", 30))
        super().__init__(
            hass,
            _LOGGER,
            name="UV Index Data",
            update_method=self._async_update_data,
            update_interval=timedelta(minutes=update_minutes),
        )

    async def _async_update_data(self):
        url = f"https://currentuvindex.com/api/v1/uvi?latitude={self.latitude}&longitude={self.longitude}"
        try:
            async with aiohttp.ClientSession() as session:
                with async_timeout.timeout(10):
                    async with session.get(url) as response:
                        if response.status != 200:
                            raise UpdateFailed(f"Error fetching data: {response.status}")
                        return await response.json()
        except Exception as err:
            raise UpdateFailed(f"Error fetching data: {err}")


class BaseUVSensor(CoordinatorEntity, SensorEntity):
    """Base sensor for UV index."""

    _attr_native_unit_of_measurement = UNIT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: UVIndexDataUpdateCoordinator, entry: ConfigEntry, translation_key: str, uid_suffix: str, name: str):
        super().__init__(coordinator)
        self.entry = entry
        self._attr_has_entity_name = True
        self._attr_translation_key = translation_key
        self._attr_unique_id = f"{entry.entry_id}_{uid_suffix}"
        #self._attr_name = name

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name="Current UV Index",
            manufacturer=DEVICE_MANUFACTURER,
            model=DEVICE_MODEL,
        )


def _values_for_day(forecast_list, target_date: datetime):
    """Return list of (timestamp, uvi) for the given UTC day."""
    values = []
    for item in forecast_list:
        # parse ISO UTC timestamps like "2025-08-26T07:00:00Z"
        try:
            ts = datetime.fromisoformat(item["time"].replace("Z", "+00:00"))
        except Exception:
            continue
        if ts.date() == target_date.date():
            values.append((ts, item.get("uvi")))
    return values


class CurrentUVIndexSensor(BaseUVSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "current_uv_index", "current", "Current UV Index")
        self._attr_icon = "mdi:white-balance-sunny"

    @property
    def native_value(self):
        return self.coordinator.data.get("now", {}).get("uvi")


class TodayMaxUVSensor(BaseUVSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "today_max_uv", "today_max", "Today Max UV Index")
        self._time = None
        self._attr_icon = "mdi:weather-sunset-up"

    @property
    def native_value(self):
        forecast = self.coordinator.data.get("forecast", [])
        today_values = _values_for_day(forecast, datetime.now(timezone.utc))
        if not today_values:
            self._time = None
            return None
        ts, val = max(today_values, key=lambda v: (v[1] if v[1] is not None else -1))
        self._time = ts.isoformat()
        return val

    @property
    def extra_state_attributes(self):
        return {"time": self._time} if self._time else {}


class TodayMinUVSensor(BaseUVSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "today_min_uv", "today_min", "Today Min UV Index")
        self._time = None
        self._attr_icon = "mdi:weather-sunset-down"

    @property
    def native_value(self):
        forecast = self.coordinator.data.get("forecast", [])
        today_values = _values_for_day(forecast, datetime.now(timezone.utc))
        # pick lowest positive value (ignore zeros and missing)
        positives = [v for v in today_values if v[1] is not None and v[1] > 0]
        if not positives:
            self._time = None
            return None
        ts, val = min(positives, key=lambda v: v[1])
        self._time = ts.isoformat()
        return val

    @property
    def extra_state_attributes(self):
        return {"time": self._time} if self._time else {}


class TomorrowMaxUVSensor(BaseUVSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "tomorrow_max_uv", "tomorrow_max", "Tomorrow Max UV Index")
        self._time = None
        self._attr_icon = "mdi:weather-sunset-up"

    @property
    def native_value(self):
        forecast = self.coordinator.data.get("forecast", [])
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        values = _values_for_day(forecast, tomorrow)
        if not values:
            self._time = None
            return None
        ts, val = max(values, key=lambda v: (v[1] if v[1] is not None else -1))
        self._time = ts.isoformat()
        return val

    @property
    def extra_state_attributes(self):
        return {"time": self._time} if self._time else {}


class TomorrowMinUVSensor(BaseUVSensor):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry, "tomorrow_min_uv", "tomorrow_min", "Tomorrow Min UV Index")
        self._time = None
        self._attr_icon = "mdi:weather-sunset-down"

    @property
    def native_value(self):
        forecast = self.coordinator.data.get("forecast", [])
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        values = _values_for_day(forecast, tomorrow)
        positives = [v for v in values if v[1] is not None and v[1] > 0]
        if not positives:
            self._time = None
            return None
        ts, val = min(positives, key=lambda v: v[1])
        self._time = ts.isoformat()
        return val

    @property
    def extra_state_attributes(self):
        return {"time": self._time} if self._time else {}
