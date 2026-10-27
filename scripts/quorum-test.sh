#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

mkdir -p logs
exec > >(tee logs/quorum-test.txt) 2>&1
wait_healthy
restore_nodes() {
  dc start zk1 zk2 zk3 >/dev/null 2>&1 || true
}
trap restore_nodes EXIT

mapfile_compat() { while IFS= read -r line; do printf '%s\n' "$line"; done; }
leader=""
for service in zk1 zk2 zk3; do
  if zk_cmd "$service" srvr | grep -q 'Mode: leader'; then leader="$service"; break; fi
done
test -n "$leader"
followers=()
for service in zk1 zk2 zk3; do [ "$service" = "$leader" ] || followers+=("$service"); done

echo "Initial roles"
./scripts/status.sh
echo "Stop one follower: ${followers[0]}"
dc stop "${followers[0]}"
test "$(zk_cmd "$leader" ruok)" = "imok"
echo "PASS: quorum still serves requests with two of three nodes"

echo "Stop second node: ${followers[1]}"
dc stop "${followers[1]}"
probe="/no-quorum-probe-$$"
if dc exec -T "$leader" bash -lc "timeout 12s sh -c \"printf 'create $probe value\\nquit\\n' | bin/zkCli.sh -server localhost:2181\"" 2>&1 | tee /tmp/zk-no-quorum.out | grep -q "Created $probe"; then
  echo "FAIL: write unexpectedly succeeded without quorum" >&2
  exit 1
fi
echo "PASS: one remaining node cannot commit a write"

dc start "${followers[0]}" "${followers[1]}"
wait_healthy
echo "Restored roles"
./scripts/status.sh
trap - EXIT
