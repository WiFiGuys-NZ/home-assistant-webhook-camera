"""Constants for Home Assistant Webhook Snapshot."""

from __future__ import annotations

DOMAIN = "webhook_receive_snapshot"

PLATFORMS = ["camera", "sensor"]

CONF_CAMERA_NAME = "camera_name"
CONF_WEBHOOK_ID = "webhook_id"
CONF_LOCAL_ONLY = "local_only"
CONF_IMAGE_FILENAME = "image_filename"

DEFAULT_CAMERA_NAME = "Webhook Camera"
DEFAULT_LOCAL_ONLY = True

STORAGE_URL_BASE = "/local/temp/images/webhook_receive_snapshot"
STORAGE_PATH_PARTS = ("www", "temp", "images", "webhook_receive_snapshot")

ATTR_CAMERA_NAME = "camera_name"
ATTR_WEBHOOK_ID = "webhook_id"
ATTR_SNAPSHOT_PATH = "snapshot_path"
ATTR_SNAPSHOT_URL = "snapshot_url"
ATTR_RECEIVED_AT = "received_at"

DATA_EVENT = "event"
DATA_DEVICE = "device"
DATA_TIME = "time"
DATA_RESOLUTION_W = "resolution_w"
DATA_RESOLUTION_H = "resolution_h"
DATA_DETECTION_REGION = "detection_region"
DATA_COORDINATE_X1 = "coordinate_x1"
DATA_COORDINATE_Y1 = "coordinate_y1"
DATA_COORDINATE_X2 = "coordinate_x2"
DATA_COORDINATE_Y2 = "coordinate_y2"
DATA_SNAPSHOT_BYTES = "snapshot_bytes"
