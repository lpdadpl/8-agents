import json, os, fcntl, datetime
D='/workspace/desk'
now=datetime.datetime.now().astimezone().isoformat()
scan=json.load(open(f'{D}/whale/scan_result.json'))
def note(r):
    parts=[]
    if r.get('ref_in_holders') or r.get('ref_in_trades'):
        parts.append(f"wallets de referencia: {r.get('ref_in_holders')} {r.get('ref_in_trades')}")
    else:
        parts.append("ninguna wallet de la lista de referencia (winrate30 ≥60%% en /workspace/solana_copy/candidate_wallets.csv) en top holders (RugCheck) ni en las últimas %d operaciones del pool (GeckoTerminal)"%r.get('n_trades',0))
    parts.append(f"liq ${r.get('liq'):,.0f}, cambio precio {r.get('pc')}" if r.get('liq') is not None else "sin par en DexScreener")
    parts.append(f"holders {r.get('holders_total')}, top10 sin pool {r.get('top10_nonpool_pct')}%, insiders detectados por RugCheck {r.get('insiders_detected')}")
    if r.get('n_trades'):
        parts.append(f"últimas {r['n_trades']} ops en {r['trades_span_min']} min: compras ${r['buy_usd']:,.0f} / ventas ${r['sell_usd']:,.0f}; máx. {r['max_cluster_5m']} compradores distintos (≥$100) en 5 min")
        acc=r.get('stealth_accumulators') or []
        if acc: parts.append("acumuladores sin ventas (≥2 compras): "+", ".join(f"{w} (+${v:,.0f}, {n} compras)" for w,v,n in acc[:3]))
    else:
        parts.append("sin operaciones recientes en el pool")
    return " | ".join(parts)
def why(r):
    pc=r.get('pc') or {}
    if r.get('n_trades',0)==0 or (pc.get('h24') or 0)<-80: return "No confirmado: token hundido o sin actividad, no hay acumulación."
    if r.get('max_cluster_5m',0)>=8: return "No confirmado: hay ráfaga de compras en 5 min, pero dentro de un volumen alto y visible en el gráfico, sin wallets de historial probado; no es acumulación sigilosa de smart money."
    return "No confirmado: sin evidencia de smart money ni acumulación sigilosa relevante."
with open(f'{D}/state.lock','w') as lk:
    fcntl.flock(lk,fcntl.LOCK_EX)
    leads=json.load(open(f'{D}/leads.json'))
    act=json.load(open(f'{D}/activity.json'))
    n=0
    for l in leads['leads']:
        r=scan.get(l['lead_id'])
        if not r or l['stage']!='aprobado' or (l.get('confirms') or {}).get('whale'): continue
        wallets=[w for w,_,_ in (r.get('stealth_accumulators') or [])[:5]]
        l.setdefault('confirms',{})['whale']={"result":"no confirmado","at":now,"by":"WHALE","note":why(r)+" "+note(r),"wallets":wallets,"sources":["DexScreener","RugCheck","GeckoTerminal"]}
        l['updated_at']=now
        act['entries'].append({"ts":now,"agent":"WHALE","lead_id":l['lead_id'],"action":"info","detail":f"NO CONFIRMADO | {l['symbol']} | {l['contract']} | {why(r)}"})
        n+=1
    act['entries'].append({"ts":now,"agent":"WHALE","lead_id":None,"action":"info","detail":f"Revisión WHALE horaria: {n} leads aprobados revisados, 0 confirmados. Fuentes: DexScreener, RugCheck (top holders/insiders), GeckoTerminal (últimas 300 ops por pool). Lista de referencia: kolscan winrate30 ≥60% (no hay lista propia de Alberto en la carpeta de la mesa)."})
    for fn,obj in (('leads.json',leads),('activity.json',act)):
        tmp=f'{D}/{fn}.tmp'; json.dump(obj,open(tmp,'w'),indent=1,ensure_ascii=False); os.replace(tmp,f'{D}/{fn}')
print(n)
