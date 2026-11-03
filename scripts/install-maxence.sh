#!/bin/sh
set -eu

installer="$(mktemp)"
trap 'rm -f "$installer"' EXIT

curl --fail --show-error --location --silent \
    https://ollama.com/install.sh \
    --output "$installer"

OLLAMA_VERSION=0.40.14 sh "$installer"

if [ ! -f /etc/systemd/system/ollama.service ]; then
    echo "Maxence: Ollama's systemd service was not installed" >&2
    exit 1
fi

mkdir -p /etc/systemd/system/default.target.wants
ln -sfn ../ollama.service /etc/systemd/system/default.target.wants/ollama.service
