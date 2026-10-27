#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

unfenced="$(cat runtime/last-unfenced-run)"
fenced="$(cat runtime/last-fenced-run)"

test "$(awk '/wrote result/{n++} END{print n+0}' logs/"$unfenced"-coordinator-*.log)" -eq 2
grep -q 'dataVersion = 2' "logs/${unfenced}-result.txt"
test "$(awk '/wrote result/{n++} END{print n+0}' logs/"$fenced"-coordinator-*.log)" -eq 1
grep -q 'BadVersionError stale result rejected' logs/"$fenced"-coordinator-*.log
grep -q '"unique_pairs":22286' "logs/${fenced}-result.txt"
echo "PASS: unfenced run has two writes and pointer dataVersion 2"
echo "PASS: fenced run has one write, stale write rejection, and 22,286 pairs"
