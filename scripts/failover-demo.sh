#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/common.sh"

mode="${1:-unfenced}"
case "$mode" in
  unfenced) fencing=0 ;;
  fenced) fencing=1 ;;
  *) echo "usage: $0 {unfenced|fenced}" >&2; exit 2 ;;
esac

run_id="${mode}-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p logs runtime
exec > >(tee "logs/${run_id}-driver.log") 2>&1
export FENCING="$fencing" RUN_ID="$run_id"

wait_healthy
dc --profile coordinators rm -sf coordinator-a coordinator-b >/dev/null 2>&1 || true
dc exec -T zk1 bash -lc "printf 'deleteall /skill-pairs\nquit\n' | bin/zkCli.sh -server localhost:2181" >/dev/null 2>&1 || true
dc --profile coordinators up -d coordinator-a coordinator-b

count_writes() {
  awk '/wrote result/{n++} END{print n+0}' "logs/${run_id}-coordinator-a.log" "logs/${run_id}-coordinator-b.log" 2>/dev/null
}

echo "run_id=$run_id fencing=$fencing"
leader=""
leader_line=""
for _ in $(seq 1 60); do
  for service in coordinator-a coordinator-b; do
    candidate="$(grep -h 'became leader' "logs/${run_id}-${service}.log" 2>/dev/null | tail -1 || true)"
    if [ -n "$candidate" ]; then leader="$service"; leader_line="$candidate"; break 2; fi
  done
  sleep 1
done
test -n "$leader"
backup="coordinator-a"; [ "$leader" = "coordinator-a" ] && backup="coordinator-b"
echo "Initial leader: $leader; backup: $backup"

sleep 3
pause_ns="$(python3 -c 'import time; print(time.time_ns())')"
echo "Pausing $leader with SIGSTOP"
dc pause "$leader"

backup_line=""
for _ in $(seq 1 45); do
  backup_line="$(grep 'became leader' "logs/${run_id}-${backup}.log" 2>/dev/null | tail -1 || true)"
  [ -n "$backup_line" ] && break
  sleep 1
done
test -n "$backup_line"
backup_ts="$(sed -E 's/^([^ ]+).*/\1/' <<<"$backup_line")"
failover_seconds="$(python3 - "$pause_ns" "$backup_ts" <<'PY'
from datetime import datetime, timezone
import sys
paused = int(sys.argv[1]) / 1e9
elected = datetime.strptime(sys.argv[2], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).timestamp()
print(f"{elected-paused:.3f}")
PY
)"
echo "Backup became leader after ${failover_seconds}s"

for _ in $(seq 1 90); do
  grep -q 'wrote result' "logs/${run_id}-${backup}.log" 2>/dev/null && break
  sleep 1
done
grep -q 'wrote result' "logs/${run_id}-${backup}.log"
echo "Backup published; resuming stale leader $leader"
dc unpause "$leader"

if [ "$fencing" = 0 ]; then
  for _ in $(seq 1 60); do
    [ "$(count_writes)" -ge 2 ] && break
    sleep 1
  done
  test "$(count_writes)" -eq 2
else
  for _ in $(seq 1 60); do
    grep -q 'BadVersionError stale result rejected' "logs/${run_id}-${leader}.log" 2>/dev/null && break
    sleep 1
  done
  grep -q 'BadVersionError stale result rejected' "logs/${run_id}-${leader}.log"
  test "$(count_writes)" -eq 1
fi

dc exec -T zk1 bash -lc "printf 'get /skill-pairs/result\nstat /skill-pairs/result\nquit\n' | bin/zkCli.sh -server localhost:2181" | tee "logs/${run_id}-result.txt"
dc --profile coordinators stop coordinator-a coordinator-b >/dev/null
echo "$run_id" > "runtime/last-${mode}-run"
echo "PASS: $mode failover demonstration completed"
