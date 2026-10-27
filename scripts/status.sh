#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

wait_healthy
for service in zk1 zk2 zk3; do
  printf '%s: ' "$service"
  zk_cmd "$service" srvr | awk -F': ' '/Mode:/{print $2}'
done

