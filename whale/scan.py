import json, time, csv, urllib.request, sys, collections
def get(url, tries=3):
    for i in range(tries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'application/json'})
            return json.load(urllib.request.urlopen(req,timeout=25))
        except Exception as e:
            err=str(e); time.sleep(3*(i+1))
    return {'_error':err}
leads=json.load(open('/workspace/desk/leads.json'))['leads']
ref={}
for r in csv.DictReader(open('/workspace/solana_copy/candidate_wallets.csv')):
    try: wr=float(r['winrate30'])
    except: continue
    ref[r['wallet']]=(r['name'],wr)
ref60={w:v for w,v in ref.items() if v[1]>=0.6}
out={}
now=time.time()
for l in leads:
    if l['stage']!='aprobado' or (l.get('confirms') or {}).get('whale'): continue
    m=l['contract']; res={'lead_id':l['lead_id'],'symbol':l['symbol'],'contract':m}
    ds=get(f'https://api.dexscreener.com/latest/dex/tokens/{m}')
    pairs=[p for p in (ds.get('pairs') or []) if p.get('chainId')=='solana' and p['baseToken']['address']==m]
    pairs.sort(key=lambda p:(p.get('liquidity') or {}).get('usd',0),reverse=True)
    if pairs:
        p=pairs[0]; res['pair']=p['pairAddress']; res['dex']=p['dexId']; res['liq']=(p.get('liquidity') or {}).get('usd'); res['fdv']=p.get('fdv')
        res['pc']=p.get('priceChange'); res['txns']=p.get('txns'); res['vol']=p.get('volume')
    rc=get(f'https://api.rugcheck.xyz/v1/tokens/{m}/report')
    if '_error' not in rc:
        th=rc.get('topHolders') or []
        known=set((rc.get('knownAccounts') or {}).keys())
        pool_owners=set([res.get('pair')])|known
        nonpool=[h for h in th if h.get('owner') not in pool_owners and h.get('address') not in pool_owners]
        res['holders_total']=rc.get('totalHolders'); res['insiders_detected']=rc.get('graphInsidersDetected')
        res['top10_nonpool_pct']=round(sum(h['pct'] for h in nonpool[:10]),2)
        res['top_nonpool']=[(h['owner'],round(h['pct'],2),h.get('insider')) for h in nonpool[:10]]
        res['insider_count_top']=sum(1 for h in nonpool if h.get('insider'))
        res['ref_in_holders']=[(h['owner'],ref[h['owner']]) for h in th if h.get('owner') in ref]
    else: res['rugcheck_error']=rc['_error']
    trades=[]
    if res.get('pair'):
        gt=get(f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{res['pair']}/trades")
        for t in gt.get('data') or []:
            a=t['attributes']; trades.append((a['block_timestamp'],a['kind'],a['tx_from_address'],float(a.get('volume_in_usd') or 0)))
        if '_error' in gt or 'errors' in gt: res['gt_error']=gt.get('_error') or gt.get('errors')
        time.sleep(2.2)
    res['n_trades']=len(trades)
    if trades:
        import datetime
        ts=lambda s: datetime.datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
        tt=[(ts(a),k,w,v) for a,k,w,v in trades]
        res['trades_span_min']=round((max(x[0] for x in tt)-min(x[0] for x in tt))/60,1)
        net=collections.defaultdict(float); nb=collections.Counter(); ns=collections.Counter()
        for t,k,w,v in tt:
            if k=='buy': net[w]+=v; nb[w]+=1
            else: net[w]-=v; ns[w]+=1
        acc=[(w,round(net[w],1),nb[w]) for w in net if nb[w]>=2 and ns[w]==0 and net[w]>=100]
        acc.sort(key=lambda x:-x[1]); res['stealth_accumulators']=acc[:10]
        # clusters: 5-min windows, distinct buyers with >=$100 buy
        buys=sorted([x for x in tt if x[1]=='buy' and x[3]>=100])
        best=(0,None,[])
        for i,b in enumerate(buys):
            ws=set(x[2] for x in buys if b[0]<=x[0]<b[0]+300)
            if len(ws)>best[0]: best=(len(ws),b[0],sorted(ws))
        res['max_cluster_5m']=best[0]; res['cluster_wallets']=best[2][:12]
        res['cluster_start']=datetime.datetime.fromtimestamp(best[1]).isoformat() if best[1] else None
        res['buy_usd']=round(sum(x[3] for x in tt if x[1]=='buy'),0); res['sell_usd']=round(sum(x[3] for x in tt if x[1]=='sell'),0)
        res['ref_in_trades']=sorted(set((w,ref[w][0],ref[w][1]) for _,_,w,_ in tt if w in ref))
    out[l['lead_id']]=res
    time.sleep(1.5)
json.dump(out,open('/workspace/desk/whale/scan_result.json','w'),indent=1)
print(json.dumps(out,indent=1))
