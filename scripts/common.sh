#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

dc() {
  docker compose "$@"
}

wait_healthy() {
  local service
  for service in zk1 zk2 zk3; do
    for _ in $(seq 1 40); do
      if [ "$(dc ps --format json "$service" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("Health", ""))' 2>/dev/null || true)" = "healthy" ]; then
        break
      fi
      sleep 1
    done
    dc exec -T "$service" bash -lc 'test "$(echo ruok | nc -w 2 localhost 2181)" = imok'
  done
}

zk_cmd() {
  local service="$1"
  local command="$2"
  dc exec -T "$service" bash -lc "echo '$command' | nc -w 2 localhost 2181"
}

