"""Sensor platform for onebusaway."""
from __future__ import annotations
from datetime import datetime, timezone
from time import time

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorDeviceClass,
)
from homeassistant.const import CONF_URL, CONF_ID, CONF_TOKEN
from homeassistant.helpers.aiohttp_client import async_get_clientsession


from .api import OneBusAwayApiClient

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
    client = OneBusAwayApiClient(
        url=entry.data[CONF_URL],
        key=entry.data[CONF_TOKEN],
        stop=entry.data[CONF_ID],
        session=async_get_clientsession(hass),
    )
    async_add_devices(
        OneBusAwaySensor(
            client=client,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class OneBusAwaySensor(OneBusAwayEntity, SensorEntity):
    """onebusaway Sensor class."""

    def __init__(
        self,
        client: OneBusAwayApiClient,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__()
        self.entity_description = entity_description
        self.client = client

    _attr_device_class = SensorDeviceClass.TIMESTAMP

    data = None

    @property
    def native_value(self) -> str:
        """Return the native value of the sensor."""
        if self.data is None:
            return None

        # This is a unix timestamp value except in
        # milliseconds because precision is super
        # important when discussing train departure
        # times

        current = time() * 1000
        # We want the soonest time that is after the current time
        departures = [
            d["scheduledDepartureTime"]
            for d in self.data.get("data")["entry"]["arrivalsAndDepartures"]
            if d["scheduledDepartureTime"] > current
        ]
        departure = min(departures)

        # convert unix timestamp to Python datetime
        return datetime.fromtimestamp(departure / 1000, timezone.utc)

    async def async_update(self):
        """Retrieve latest state."""
        self.data = await self.client.async_get_data()
