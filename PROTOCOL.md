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

### risk_checks (lo escribe RISK)
Al revisar un lead en `escaneado` con `approval=="pendiente"`, RISK añade al lead:
- `risk_checks`: objeto `{clave:{ok:bool, note:str}}` con estas claves: `contract_match` (dirección on-chain vs SEARCH, carácter a carácter: RPC getAccountInfo + RugCheck + DexScreener), `mint_revoked`, `freeze_revoked`, `lp_locked` (LP bloqueada/quemada ≥95%), `taxes_ok` (transfer fee Token-2022 = 0), `honeypot_ok` (ventas reales y sin transferHook/permanentDelegate/pausable), `dev_history_ok`, `liquidity_ok` (≥ 10.000 $), `top_holders_ok` (top 10 sin pools/LP/lockers ≤ 30%), `wash_ok` (vol 1h ≤ 5x liq, vol 24h ≤ 25x liq, compras/ventas 1h ≤ 4:1).
- `risk_verdict`: `APROBADO|RECHAZADO`; `risk_decisive`: comprobación que decidió (`clave: nota`); `risk_checked_at`: ISO.
- Aprobado: `stage="aprobado"`, `approval` sigue `pendiente` (el APPROVE es solo de Alberto). Rechazado: `stage` se queda en `escaneado`, `approval="RECHAZADO"` y se añade `{stage:"rechazado",by:"RISK"}` a history. Un dato crítico que falte = fallo.

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

## activity.json (log por agente, opcional)
`{"entries":[{"ts":ISO,"agent":"SEARCH|RISK|...|BOT DESK","lead_id":"L-...|null","action":"escaneado|aprobado|rechazado|confirmado|ejecutado|cerrado|alerta|info","detail":str}]}`
Los agentes AÑADEN al final (leer, append, escritura atómica tmp+rename); nunca borran. Se sincroniza a Render igual que leads/top10 (el box manda). El panel muestra las últimas 30 por agente en "Ver últimas operaciones".

## UI oficina
`/` = oficina animada (clic en bot: ver operaciones / parar-reanudar; clic en jefe: histórico / parar-reanudar todo con confirmación). `/clasico` = tabla antigua. APIs: /api/state, /api/leads, /api/top10, /api/activity (Basic Auth); /api/sync (Bearer SYNC_TOKEN); /healthz.

## Modo papel (SNIPER)
- Prueba de concepto: no hay carteras ni dinero real. Nunca se conecta ni se firma nada real.
- Saldo simulado inicial: 50 USD, llevado en `paper.json` (cash, positions, closed, realized_pnl, unrealized_pnl).
- Con un lead `confirmado`, SNIPER prepara la orden simulada: tamaño sobre el saldo, entrada, stop, objetivos y slippage, con CA verificada contra SEARCH y RISK.
- Solo tras el literal `APPROVE #id` de Alberto: se apunta como ejecutada en papel en `leads.json` (precio de entrada real del momento), se registra en `activity.json` y se descuenta de `paper.json`.

## Archivos (visor de solo lectura)
Sidebar → 📁 Archivos. API: `GET /api/files`, `GET /api/file?path=<raíz>/<ruta>` (Basic Auth). Raíces: `desk`=/workspace/desk, `leads`=/workspace/leads, `risk`=/workspace/risk. Allowlist: solo .json/.md/.csv ≤3 MB; se rechaza (403) cualquier segmento oculto (.auth, .sync, .render_url, .env…), `..`, rutas absolutas, nombres con auth/sync/env/secret/token/password/credential o .log, y todo lo que resuelva fuera de la raíz. En Render los contenidos llegan por `sync.py` (solo cuando cambia el digest SHA-256).
