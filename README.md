# Mesa de memecoins (8 agentes) — panel de control
Panel "oficina" animado (sin wallet, sin claves, sin firma) + sync con Render.
- `dashboard/server.py`: servidor (stdlib). Local: `dashboard/run.sh` (puerto 8787). Basic Auth desde `dashboard/.auth`.
- `dashboard/office.html`: fuente de la UI (embebida en server.py como OFFICE_HTML).
- `dashboard/sync.py` / `sync.sh`: sync box↔Render cada 30 s.
- `build_top10.py`: top 10 Solana por volumen 1h (GeckoTerminal).
- `PROTOCOL.md`: formato de leads, contratos de state/leads/activity.json.
Secretos: ver `.env.example`. Nunca se commitean.
