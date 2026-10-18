# Protocolo de la Mesa

## Formato de mensaje (grupo Trading Floor)
`[LEAD-ID] AGENTE → ETAPA | SÍMBOLO | CONTRATO | nota`
Ej: `[L-20261017-001] RISK → aprobado | GHOSTI | 9JxPFZ68WQBQR8JwMStZfeqxhSm1X79i3rpyHHbbe8B9 | mint authority revocada`
- LEAD-ID: `L-AAAAMMDD-NNN`, único, nunca se reutiliza.
- Etapas en orden: escaneado (SEARCH) → aprobado (RISK) → confirmado (WHALE+SHILL) → ejecutado (SNIPER, solo con APPROVE literal de Alberto) → cerrado (EXIT/RUG).
- Contrato siempre completo, nunca abreviado.

## Contrato de state.json
```
{"floor":"RUNNING|HALTED","updated_at":ISO,"agents":{"NOMBRE":{"role":str,"status":"RUNNING|PAUSED","updated_at":ISO}}}
```
Antes de cada ejecución/rutina, cada agente lee state.json y SOLO actúa si `floor=="RUNNING"` y su `status=="RUNNING"`. Si no, sale sin hacer nada (y lo registra). El panel es el único escritor normal.

## leads.json
`{"leads":[{lead_id,symbol,contract,stage,owner,approval:"pendiente|APPROVE|RECHAZADO",created_at,updated_at,history:[{stage,at,by}]}]}`

## Reglas fijas
Ningún agente guarda claves ni frases semilla. Ninguna firma sin APPROVE literal de Alberto. El panel no tiene funciones de wallet ni firma.

## Panel público (Render) y sincronización
- URL: https://mesa-desk-dashboard.onrender.com (Basic Auth; usuarios en env `DASH_USERS` en Render y en `dashboard/.auth` en el box, chmod 600).
- Render (plan free, Frankfurt) ejecuta el mismo `dashboard/server.py` en modo `STORAGE=memory`. El código va en la env `APP_B64` (no hay repo propio; el repo `render-examples/flask-hello-world` solo sirve de base). Nunca se suben secretos a git.
- **El box es la fuente de verdad** de leads.json y top10.json. state.json gana quien tenga el `updated_at` más reciente.
- `dashboard/sync.py` (lanzado con `dashboard/sync.sh`, log en `sync.log`) cada 30 s:
  1. `GET /api/sync` (Bearer `SYNC_TOKEN`, guardado en `dashboard/.sync`) → si el state de Render es más nuevo, lo escribe en state.json del box (escritura atómica).
  2. `PUT /api/sync` con state/leads/top10 del box (Render ignora un state más antiguo que el suyo).
- Si Render se reinicia (pierde memoria), el siguiente ciclo lo vuelve a poblar desde el box.
- Los agentes SIEMPRE leen el state.json local del box; una pausa desde la web llega en ≤30-60 s.
- Para actualizar el código en Render: volver a poner `APP_B64=$(base64 -w0 server.py)` en las env vars y redeployar.
