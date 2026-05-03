# Home Assistant Webhook Snapshot

Receive a camera webhook JSON payload in Home Assistant, store the latest base64
snapshot as a local image, and update a template sensor for dashboards.

This project includes:

- A HACS-ready custom integration called **Home Assistant Webhook Snapshot**.
- An automation blueprint for the per-camera webhook setup.
- A support package that provides the image writer and template sensor.

## Repository files

```text
custom_components/
  webhook_receive_snapshot/
blueprints/
  automation/
    webhook-camera-template.yaml
packages/
  webhook_camera_support.yaml
```

## Custom integration

The recommended install path is the custom integration:

```text
custom_components/webhook_receive_snapshot
```

It provides:

- A UI config flow named **Home Assistant Webhook Snapshot**
- Multiple cameras, added as separate config entries with the + button
- A camera entity showing the latest received snapshot
- Sensor entities for event, device, time, region, coordinates, resolution,
  snapshot bytes, snapshot URL, and received time
- Per-camera image files written to:

```text
/config/www/temp/images/webhook_receive_snapshot/<camera_slug>_last_motion.jpg
```

Dashboard URL:

```text
/local/temp/images/webhook_receive_snapshot/<camera_slug>_last_motion.jpg
```

Webhook URL:

```text
https://YOUR_HOME_ASSISTANT_URL/api/webhook/YOUR_WEBHOOK_ID
```

This repository includes `hacs.json` and the Home Assistant custom component
layout expected by HACS.

## Install with HACS

In Home Assistant, go to:

```text
HACS > Integrations > three-dot menu > Custom repositories
```

Add:

```text
Repository: https://github.com/WiFiGuys-NZ/home-assistant-webhook-camera
Category: Integration
```

Then install **Home Assistant Webhook Snapshot** from HACS and restart Home
Assistant.

After restart, go to:

```text
Settings > Devices & services > Add integration > Home Assistant Webhook Snapshot
```

Create one entry per camera. Use the + button to add more cameras later.

## Install the blueprint

The blueprint/package method is still available as a simple YAML-based install.

In Home Assistant, go to:

```text
Settings > Automations & scenes > Blueprints > Import blueprint
```

Use this URL:

```text
https://raw.githubusercontent.com/WiFiGuys-NZ/home-assistant-webhook-camera/main/blueprints/automation/webhook-camera-template.yaml
```

Or use this My Home Assistant import link:

```text
https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fraw.githubusercontent.com%2FWiFiGuys-NZ%2Fhome-assistant-webhook-camera%2Fmain%2Fblueprints%2Fautomation%2Fwebhook-camera-template.yaml
```

## Install the support package

Copy this file into Home Assistant:

```text
/config/packages/webhook_camera_support.yaml
```

The package file is:

```text
packages/webhook_camera_support.yaml
```

## Simple install from Terminal/SSH

From the Home Assistant Terminal/SSH add-on, run:

```sh
curl -fsSL https://raw.githubusercontent.com/WiFiGuys-NZ/home-assistant-webhook-camera/main/install.sh | sh
```

This downloads:

```text
/config/blueprints/automation/WiFiGuys-NZ/webhook-camera-template.yaml
/config/packages/webhook_camera_support.yaml
```

Make sure packages are enabled in `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages/
```

Restart Home Assistant after installing the support package.

## Create a camera automation

After importing the blueprint, create a new automation from it.

Set:

- Camera name
- Webhook ID
- Local only on/off
- Snapshot writer service, usually `notify.webhook_camera_snapshot_writer`
- Snapshot path, usually `/config/www/tmp/webhook_camera_latest.jpg`
- Dashboard image URL, usually `/local/tmp/webhook_camera_latest.jpg`
- Event type, usually `webhook_camera_event`

The webhook URL is:

```text
https://YOUR_HOME_ASSISTANT_URL/api/webhook/YOUR_WEBHOOK_ID
```

For direct internet webhooks, turn off **Local only** in the blueprint
automation. Keep it on for LAN or Home Assistant Cloud/Nabu Casa access.

## Expected JSON payload

```json
{
  "event": "Region Entrance",
  "device": "camera-name",
  "time": "2026-05-02 12:55:03",
  "resolution_w": 2592,
  "resolution_h": 1520,
  "detection_region": 1,
  "coordinate_x1": 486,
  "coordinate_y1": 1178,
  "coordinate_x2": 591,
  "coordinate_y2": 1273,
  "snapshot": "BASE64_JPEG_DATA"
}
```

The `snapshot` value should be the base64 JPEG data without a data URL prefix.
Send the webhook request as JSON with:

```text
Content-Type: application/json
```

## Dashboard image

The latest image is written to:

```text
/config/www/tmp/webhook_camera_latest.jpg
```

Use this URL in dashboards:

```text
/local/tmp/webhook_camera_latest.jpg
```
