#!/bin/bash
pkill -f /workspace/desk/dashboard/server.py; sleep 0.5
nohup python3 /workspace/desk/dashboard/server.py > /workspace/desk/dashboard/server.log 2>&1 &
echo started pid $!
