#!/bin/bash
# Quick tunnel: URL cambia en cada reinicio. URL actual en tunnel_url.txt
pkill -f "cloudflared tunnel http://localhost:8787"; sleep 1
nohup /home/box/bin/cloudflared tunnel --no-autoupdate --protocol http2 --url http://localhost:8787 > /workspace/desk/dashboard/tunnel.log 2>&1 &
for i in $(seq 30); do u=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' /workspace/desk/dashboard/tunnel.log | head -1); [ -n "$u" ] && break; sleep 1; done
echo "$u" > /workspace/desk/dashboard/tunnel_url.txt; echo "URL: $u"
