"""Sensor platform for onebusaway."""
from __future__ import annotations
from datetime import datetime, timezone
from time import time

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
)

from .const import DOMAIN
from .coordinator import OneBusAwayDataUpdateCoordinator
from .entity import OneBusAwayEntity

ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        key="onebusaway",
        name="OneBusAway Sensor",
        icon="mdi:bus-clock",
    ),
)


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_devices(
        OneBusAwaySensor(
            coordinator=coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class OneBusAwaySensor(OneBusAwayEntity, SensorEntity):
    """onebusaway Sensor class."""

    def __init__(
        self,
        coordinator: OneBusAwayDataUpdateCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__(coordinator)
        self.entity_description = entity_description

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""

        # This is a unix timestamp value except in
        # milliseconds because precision is super
        # important when discussing train departure
        # times

        current = time() * 1000
        # We want the soonest time that is after the current time
        departures = [
            d["scheduledDepartureTime"]
            for d in self.coordinator.data.get("data")["entry"]["arrivalsAndDepartures"]
            if d["scheduledDepartureTime"] > current
        ]
        departure = min(departures)

        # convert unix timestamp to Python datetime
        return datetime.fromtimestamp(departure / 1000, timezone.utc)
