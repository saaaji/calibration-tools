#!/bin/bash
OUT=".devcontainer/docker-compose.devices.yml"

echo "services:" > $OUT
echo "  calib-dev:" >> $OUT
echo "    devices:" >> $OUT

for dev in /dev/video*; do
    [ -e "$dev" ] && echo "      - ${dev}:${dev}" >> $OUT
done