"""Home Assistant Webhook Snapshot integration."""

from __future__ import annotations

import base64
from collections.abc import Callable
from datetime import datetime
import logging
from pathlib import Path
from typing import Any

from aiohttp import web

from homeassistant.components import webhook
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.util import dt as dt_util
from homeassistant.util import slugify

from .const import (
    ATTR_CAMERA_NAME,
    ATTR_RECEIVED_AT,
    ATTR_SNAPSHOT_PATH,
    ATTR_SNAPSHOT_URL,
    ATTR_WEBHOOK_ID,
    CONF_CAMERA_NAME,
    CONF_IMAGE_FILENAME,
    CONF_LOCAL_ONLY,
    CONF_WEBHOOK_ID,
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
    DEFAULT_LOCAL_ONLY,
    DOMAIN,
    PLATFORMS,
    STORAGE_PATH_PARTS,
    STORAGE_URL_BASE,
)

_LOGGER = logging.getLogger(__name__)


WebhookSnapshotConfigEntry = ConfigEntry


async def async_setup_entry(
    hass: HomeAssistant, entry: WebhookSnapshotConfigEntry
) -> bool:
    """Set up Home Assistant Webhook Snapshot from a config entry."""
    manager = WebhookSnapshotManager(hass, entry)
    entry.runtime_data = manager

    webhook.async_register(
        hass,
        DOMAIN,
        entry.title,
        manager.webhook_id,
        manager.async_handle_webhook,
        local_only=entry.data.get(CONF_LOCAL_ONLY, DEFAULT_LOCAL_ONLY),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: WebhookSnapshotConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        webhook.async_unregister(hass, entry.runtime_data.webhook_id)
    return unload_ok


class WebhookSnapshotManager:
    """Hold latest webhook data and snapshot bytes for one camera."""

    def __init__(self, hass: HomeAssistant, entry: WebhookSnapshotConfigEntry) -> None:
        """Initialize the manager."""
        self.hass = hass
        self.entry = entry
        self.camera_name: str = entry.data[CONF_CAMERA_NAME]
        self.webhook_id: str = entry.data[CONF_WEBHOOK_ID]
        self.camera_slug = slugify(self.camera_name)
        self.snapshot_bytes: bytes | None = None
        self.data: dict[str, Any] = {
            ATTR_CAMERA_NAME: self.camera_name,
            ATTR_WEBHOOK_ID: self.webhook_id,
            ATTR_SNAPSHOT_PATH: self.snapshot_path,
            ATTR_SNAPSHOT_URL: self.snapshot_url,
        }
        self._listeners: set[Callable[[], None]] = set()

    @property
    def filename(self) -> str:
        """Return the snapshot filename."""
        configured = self.entry.data.get(CONF_IMAGE_FILENAME)
        if configured:
            configured_path = Path(configured).name
            configured_stem = slugify(Path(configured_path).stem)
            configured_suffix = Path(configured_path).suffix.lower()
            filename = configured_stem or f"{self.camera_slug}_last_motion"
            if configured_suffix in (".jpg", ".jpeg"):
                filename = f"{filename}{configured_suffix}"
        else:
            filename = f"{self.camera_slug}_last_motion.jpg"
        return filename

    @property
    def snapshot_path(self) -> str:
        """Return the snapshot file path."""
        return self.hass.config.path(*STORAGE_PATH_PARTS, self.filename)

    @property
    def snapshot_url(self) -> str:
        """Return the dashboard image URL."""
        return f"{STORAGE_URL_BASE}/{self.filename}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info shared by entities."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.entry.entry_id)},
            name=self.camera_name,
            manufacturer="Home Assistant Webhook Snapshot",
            model="Webhook snapshot receiver",
        )

    @callback
    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register a listener for new webhook data."""
        self._listeners.add(listener)

        @callback
        def remove_listener() -> None:
            self._listeners.discard(listener)

        return remove_listener

    @callback
    def _async_notify_listeners(self) -> None:
        """Notify entities that new data is available."""
        for listener in list(self._listeners):
            listener()

    async def async_handle_webhook(
        self, hass: HomeAssistant, webhook_id: str, request: web.Request
    ) -> web.Response:
        """Handle an incoming webhook request."""
        try:
            payload = await request.json()
        except ValueError:
            _LOGGER.warning("Received webhook payload that was not valid JSON")
            return web.json_response({"success": False, "error": "invalid_json"}, status=400)

        if not isinstance(payload, dict):
            return web.json_response({"success": False, "error": "invalid_payload"}, status=400)

        snapshot_base64 = _first_value(
            payload,
            "snapshot",
            "snapshot_base64",
            "image",
            "image_base64",
            "jpeg",
            "jpg",
        )
        snapshot_written = False

        if isinstance(snapshot_base64, str) and snapshot_base64:
            try:
                image = _decode_base64_image(snapshot_base64)
            except ValueError:
                _LOGGER.warning("Received webhook snapshot that was not valid base64")
            else:
                self.snapshot_bytes = image
                await hass.async_add_executor_job(_write_snapshot, self.snapshot_path, image)
                snapshot_written = True

        received_at = dt_util.utcnow()
        self.data = _normalize_payload(payload, received_at)
        self.data.update(
            {
                ATTR_CAMERA_NAME: self.camera_name,
                ATTR_WEBHOOK_ID: self.webhook_id,
                ATTR_SNAPSHOT_PATH: self.snapshot_path,
                ATTR_SNAPSHOT_URL: self.snapshot_url,
                DATA_SNAPSHOT_BYTES: len(self.snapshot_bytes or b""),
            }
        )

        self._async_notify_listeners()

        return web.json_response(
            {
                "success": True,
                "snapshot_written": snapshot_written,
                "snapshot_url": self.snapshot_url,
            }
        )


def _decode_base64_image(value: str) -> bytes:
    """Decode a base64 image value."""
    if value.startswith("data:") and "," in value:
        value = value.split(",", 1)[1]
    try:
        return base64.b64decode(value, validate=False)
    except Exception as err:
        raise ValueError("Invalid base64 image") from err


def _write_snapshot(path: str, image: bytes) -> None:
    """Write snapshot bytes to disk."""
    snapshot_path = Path(path)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_bytes(image)


def _normalize_payload(payload: dict[str, Any], received_at: datetime) -> dict[str, Any]:
    """Normalize known payload fields while tolerating missing or alternate names."""
    bbox = _first_value(payload, "bbox", "box", "bounding_box", "coordinates")

    data = {
        DATA_EVENT: _first_value(payload, "event", "event_type", "type", "name"),
        DATA_DEVICE: _first_value(payload, "device", "device_name", "camera", "camera_name"),
        DATA_TIME: _first_value(payload, "time", "timestamp", "event_time", "datetime"),
        DATA_RESOLUTION_W: _first_value(payload, "resolution_w", "image_width", "width", "w"),
        DATA_RESOLUTION_H: _first_value(payload, "resolution_h", "image_height", "height", "h"),
        DATA_DETECTION_REGION: _first_value(payload, "detection_region", "region", "region_id", "roi"),
        DATA_COORDINATE_X1: _coordinate_value(payload, bbox, 0, "coordinate_x1", "x1", "left", "bbox_x1"),
        DATA_COORDINATE_Y1: _coordinate_value(payload, bbox, 1, "coordinate_y1", "y1", "top", "bbox_y1"),
        DATA_COORDINATE_X2: _coordinate_value(payload, bbox, 2, "coordinate_x2", "x2", "right", "bbox_x2"),
        DATA_COORDINATE_Y2: _coordinate_value(payload, bbox, 3, "coordinate_y2", "y2", "bottom", "bbox_y2"),
        ATTR_RECEIVED_AT: received_at.isoformat(),
    }
    return {key: value for key, value in data.items() if value not in (None, "")}


def _coordinate_value(
    payload: dict[str, Any], bbox: Any, index: int, *keys: str
) -> Any:
    """Return a coordinate value from named fields or a bounding box list."""
    value = _first_value(payload, *keys)
    if value is not None:
        return value
    if isinstance(bbox, (list, tuple)) and len(bbox) > index:
        return bbox[index]
    return None


def _first_value(payload: dict[str, Any], *keys: str) -> Any:
    """Return the first present payload value using case-insensitive keys."""
    lowered = {str(key).lower(): value for key, value in payload.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value not in (None, ""):
            return value
    return None
