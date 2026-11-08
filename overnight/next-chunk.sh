#!/usr/bin/env bash
# Writes the next N not-yet-pushed lines of /home/user/logs/push-list.txt (tier order) to /home/user/logs/push-chunk.txt.
cd "$(dirname "$0")/.."
awk '{print $2}' overnight/pushes-checkpoint.txt | sort -u > /tmp/claude-0/pushed
grep -vwFf /tmp/claude-0/pushed /home/user/logs/push-list.txt | head -${1:-20} > /home/user/logs/push-chunk.txt
grep -vwFf /tmp/claude-0/pushed /home/user/logs/push-list.txt | wc -l
