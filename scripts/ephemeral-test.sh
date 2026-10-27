#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

mkdir -p logs
exec > >(tee logs/ephemeral-test.txt) 2>&1
wait_healthy
path="/ephemeral-demo-$$"
echo "Creating ephemeral node $path in a short-lived zkCli session"
dc exec -T zk2 bash -lc "printf 'create -e $path alive\nget $path\nquit\n' | bin/zkCli.sh -server localhost:2181"
sleep 2
output="$(dc exec -T zk2 bash -lc "printf 'get $path\nquit\n' | bin/zkCli.sh -server localhost:2181" 2>&1 || true)"
printf '%s\n' "$output"
grep -q 'Node does not exist' <<<"$output"
echo "PASS: ephemeral node disappeared when the client session closed"
