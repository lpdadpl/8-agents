import json,datetime
EXCL={"So11111111111111111111111111111111111111112","EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v","Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"}
toks={}
for f in ["pools.json","pools2.json","pools3.json"]:
    d=json.load(open(f)); inc={i["id"]:i["attributes"] for i in d.get("included",[])}
    for p in d["data"]:
        a=p["attributes"]; bid=p["relationships"]["base_token"]["data"]["id"]; t=inc.get(bid,{})
        mint=t.get("address") or bid.split("_",1)[1]
        if mint in EXCL: continue
        v=float(a["volume_usd"]["h1"] or 0)
        e=toks.setdefault(mint,{"symbol":t.get("symbol"),"name":t.get("name"),"mint":mint,"volume_1h_usd":0,"top_pool":a["address"],"_pv":-1})
        e["volume_1h_usd"]+=v
        if v>e["_pv"]: e["_pv"]=v; e["top_pool"]=a["address"]
top=sorted(toks.values(),key=lambda x:-x["volume_1h_usd"])[:10]
for i,t in enumerate(top,1):
    t.pop("_pv"); t["rank"]=i; t["volume_1h_usd"]=round(t["volume_1h_usd"],2)
    t["source_url"]=f"https://www.geckoterminal.com/solana/pools/{t['top_pool']}"
    t["api_url"]=f"https://api.geckoterminal.com/api/v2/networks/solana/tokens/{t['mint']}"
out={"generated_at":datetime.datetime.now().astimezone().isoformat(),"source":"GeckoTerminal API, top 60 pools by 24h vol, aggregated 1h vol per base token (excl. SOL/USDC/USDT)","tokens":top}
json.dump(out,open("top10.json","w"),indent=2)
for t in top: print(t["rank"],t["symbol"],t["mint"],t["volume_1h_usd"])
