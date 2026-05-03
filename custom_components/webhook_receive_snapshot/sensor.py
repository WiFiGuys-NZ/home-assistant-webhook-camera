"""Sensor platform for Home Assistant Webhook Snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import WebhookSnapshotConfigEntry, WebhookSnapshotManager
from .const import (
    ATTR_RECEIVED_AT,
    ATTR_SNAPSHOT_URL,
    DATA_COORDINATE_X1,
    DATA_COORDINATE_X2,
    DATA_COORDINATE_Y1,
    DATA_COORDINATE_Y2,
    DATA_DETECTION_REGION,
    DATA_DEVICE,
    DATA_EVENT,
    DATA_RESOLUTION_H,
    DATA_RESOLUTION_W,
    DATA_SNAPSHOT_BYTES,
    DATA_TIME,
)


@dataclass(frozen=True, kw_only=True)
class WebhookSnapshotSensorEntityDescription(SensorEntityDescription):
    """Description for webhook snapshot sensors."""

    data_key: str


SENSORS: tuple[WebhookSnapshotSensorEntityDescription, ...] = (
    WebhookSnapshotSensorEntityDescription(
        key="event",
        name="Event",
        icon="mdi:calendar-star",
        data_key=DATA_EVENT,
    ),
    WebhookSnapshotSensorEntityDescription(
        key="device",
        name="Device",
        icon="mdi:cctv",
        data_key=DATA_DEVICE,
    ),
    WebhookSnapshotSensorEntityDescription(
        key="time",
        name="Event Time",
        icon="mdi:clock-outline",
        data_key=DATA_TIME,
    ),
    WebhookSnapshotSensorEntityDescription(
        key="detection_region",
        name="Detection Region",
        icon="mdi:map-marker-radius-outline",
        data_key=DATA_DETECTION_REGION,
    ),
    WebhookSnapshotSensorEntityDescription(
        key="coordinates",
        name="Coordinates",
        icon="mdi:vector-square",
        data_key="coordinates",
    ),
    WebhookSnapshotSensorEntityDescription(
        key="resolution",
        name="Resolution",
        icon="mdi:aspect-ratio",
        data_key="resolution",
    ),
    WebhookSnapshotSensorEntityDescription(
        key="snapshot_bytes",
        name="Snapshot Bytes",
        icon="mdi:file-image-outline",
        data_key=DATA_SNAPSHOT_BYTES,
    ),
    WebhookSnapshotSensorEntityDescription(
        key="snapshot_url",
        name="Snapshot URL",
        icon="mdi:image-outline",
        data_key=ATTR_SNAPSHOT_URL,
    ),
    WebhookSnapshotSensorEntityDescription(
        key="received_at",
        name="Received At",
        icon="mdi:clock-check-outline",
        data_key=ATTR_RECEIVED_AT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WebhookSnapshotConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up webhook snapshot sensors."""
    manager = entry.runtime_data
    async_add_entities(
        WebhookSnapshotSensor(manager, description) for description in SENSORS
    )


class WebhookSnapshotSensor(SensorEntity):
    """Sensor for one webhook snapshot data field."""

    _attr_has_entity_name = True

    entity_description: WebhookSnapshotSensorEntityDescription

    def __init__(
        self,
        manager: WebhookSnapshotManager,
        description: WebhookSnapshotSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        self._manager = manager
        self.entity_description = description
        self._attr_unique_id = f"{manager.entry.entry_id}_{description.key}"
        self._attr_device_info = manager.device_info
        self._remove_listener = None

    async def async_added_to_hass(self) -> None:
        """Subscribe to manager updates."""
        self._remove_listener = self._manager.async_add_listener(self._handle_update)

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from manager updates."""
        if self._remove_listener is not None:
            self._remove_listener()
            self._remove_listener = None

    @callback
    def _handle_update(self) -> None:
        """Handle updated snapshot data."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        data = self._manager.data
        key = self.entity_description.data_key

        if key == "coordinates":
            values = [
                data.get(DATA_COORDINATE_X1),
                data.get(DATA_COORDINATE_Y1),
                data.get(DATA_COORDINATE_X2),
                data.get(DATA_COORDINATE_Y2),
            ]
            if any(value is not None for value in values):
                return ",".join("" if value is None else str(value) for value in values)
            return None

        if key == "resolution":
            width = data.get(DATA_RESOLUTION_W)
            height = data.get(DATA_RESOLUTION_H)
            if width is not None and height is not None:
                return f"{width}x{height}"
            return None

        return data.get(key)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional attributes for grouped values."""
        data = self._manager.data
        if self.entity_description.data_key == "coordinates":
            return {
                DATA_COORDINATE_X1: data.get(DATA_COORDINATE_X1),
                DATA_COORDINATE_Y1: data.get(DATA_COORDINATE_Y1),
                DATA_COORDINATE_X2: data.get(DATA_COORDINATE_X2),
                DATA_COORDINATE_Y2: data.get(DATA_COORDINATE_Y2),
            }
        if self.entity_description.data_key == "resolution":
            return {
                DATA_RESOLUTION_W: data.get(DATA_RESOLUTION_W),
                DATA_RESOLUTION_H: data.get(DATA_RESOLUTION_H),
            }
        return None
