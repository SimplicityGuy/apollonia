#!/bin/bash
set -e

# Fix permissions on /data directory
if [ "$(id -u)" = "0" ]; then
    chown -R apollonia:apollonia /data
    chmod -R 755 /data
    exec gosu apollonia "$@"
else
    exec "$@"
fi
