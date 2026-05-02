#!/usr/bin/env sh
set -eu

REPO_RAW="https://raw.githubusercontent.com/WiFiGuys-NZ/home-assistant-webhook-camera/main"
CONFIG_DIR="${CONFIG_DIR:-/config}"

BLUEPRINT_DIR="$CONFIG_DIR/blueprints/automation/WiFiGuys-NZ"
PACKAGES_DIR="$CONFIG_DIR/packages"

echo "Installing Home Assistant Webhook Camera files..."

mkdir -p "$BLUEPRINT_DIR"
mkdir -p "$PACKAGES_DIR"

download() {
  url="$1"
  dest="$2"

  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url" -o "$dest"
  elif command -v wget >/dev/null 2>&1; then
    wget -qO "$dest" "$url"
  else
    echo "Error: curl or wget is required." >&2
    exit 1
  fi
}

download \
  "$REPO_RAW/blueprints/automation/webhook-camera-template.yaml" \
  "$BLUEPRINT_DIR/webhook-camera-template.yaml"

download \
  "$REPO_RAW/packages/webhook_camera_support.yaml" \
  "$PACKAGES_DIR/webhook_camera_support.yaml"

echo
echo "Installed:"
echo "  $BLUEPRINT_DIR/webhook-camera-template.yaml"
echo "  $PACKAGES_DIR/webhook_camera_support.yaml"
echo
echo "Make sure configuration.yaml contains:"
echo
echo "homeassistant:"
echo "  packages: !include_dir_named packages/"
echo
echo "Then check configuration and restart Home Assistant."
