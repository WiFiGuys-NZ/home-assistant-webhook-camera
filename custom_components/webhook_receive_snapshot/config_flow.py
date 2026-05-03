"""Config flow for Webhook Receive Snapshot."""

from __future__ import annotations

import uuid
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.util import slugify

from .const import (
    CONF_CAMERA_NAME,
    CONF_IMAGE_FILENAME,
    CONF_LOCAL_ONLY,
    CONF_WEBHOOK_ID,
    DEFAULT_CAMERA_NAME,
    DEFAULT_LOCAL_ONLY,
    DOMAIN,
)


class WebhookReceiveSnapshotConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Webhook Receive Snapshot."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            camera_name = user_input[CONF_CAMERA_NAME].strip()
            webhook_id = user_input[CONF_WEBHOOK_ID].strip()
            image_filename = user_input.get(CONF_IMAGE_FILENAME, "").strip()

            if not camera_name:
                errors[CONF_CAMERA_NAME] = "required"
            if not webhook_id:
                errors[CONF_WEBHOOK_ID] = "required"

            if not errors:
                await self.async_set_unique_id(webhook_id)
                self._abort_if_unique_id_configured()

                if not image_filename:
                    image_filename = f"{slugify(camera_name)}_last_motion.jpg"

                return self.async_create_entry(
                    title=camera_name,
                    data={
                        CONF_CAMERA_NAME: camera_name,
                        CONF_WEBHOOK_ID: webhook_id,
                        CONF_LOCAL_ONLY: user_input[CONF_LOCAL_ONLY],
                        CONF_IMAGE_FILENAME: image_filename,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CAMERA_NAME, default=DEFAULT_CAMERA_NAME): str,
                    vol.Required(CONF_WEBHOOK_ID, default=uuid.uuid4().hex): str,
                    vol.Required(CONF_LOCAL_ONLY, default=DEFAULT_LOCAL_ONLY): bool,
                    vol.Optional(CONF_IMAGE_FILENAME, default=""): str,
                }
            ),
            errors=errors,
        )
