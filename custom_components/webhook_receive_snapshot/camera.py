"""Camera platform for Webhook Receive Snapshot."""

from __future__ import annotations

from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import WebhookSnapshotConfigEntry, WebhookSnapshotManager


async def async_setup_entry(
    hass: HomeAssistant,
    entry: WebhookSnapshotConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the camera entity."""
    async_add_entities([WebhookSnapshotCamera(entry.runtime_data)])


class WebhookSnapshotCamera(Camera):
    """Camera entity showing the latest webhook snapshot."""

    _attr_has_entity_name = True
    _attr_name = "Latest Snapshot"

    def __init__(self, manager: WebhookSnapshotManager) -> None:
        """Initialize the camera."""
        super().__init__()
        self._manager = manager
        self._attr_unique_id = f"{manager.entry.entry_id}_latest_snapshot"
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

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return the latest camera image."""
        return self._manager.snapshot_bytes

    @property
    def extra_state_attributes(self) -> dict[str, str]:
        """Return snapshot attributes."""
        return {
            "snapshot_path": self._manager.snapshot_path,
            "snapshot_url": self._manager.snapshot_url,
            "webhook_id": self._manager.webhook_id,
        }
