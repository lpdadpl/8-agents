#!/bin/bash
pkill -f /workspace/desk/dashboard/sync.py; sleep 0.5
nohup python3 /workspace/desk/dashboard/sync.py >> /workspace/desk/dashboard/sync.log 2>&1 &
echo sync pid $!
