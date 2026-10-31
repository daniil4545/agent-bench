#!/usr/bin/env bash
# Runs the same task on one Kimi model in a fresh git copy of base/; prints elapsed seconds.
set -u
B=$(cd "$(dirname "$0")" && pwd)
name=$1 model=$2
dir=$B/runs/$name
rm -rf "$dir"
mkdir -p "$B/runs"
cp -R "$B/base" "$dir"
git -C "$dir" init -q -b main
git -C "$dir" add -A
git -C "$dir" -c user.name=trial -c user.email=trial@local commit -qm "chore: initial"
git -C "$dir" switch -qc T-1-seconds
start=$(date +%s)
(cd "$dir" && kimi -p "$(cat "$B/task.md")" -m "$model" --output-format stream-json </dev/null >"$B/runs/$name.jsonl" 2>"$B/runs/$name.err")
echo "$name exit=$? seconds=$(($(date +%s) - start))"
