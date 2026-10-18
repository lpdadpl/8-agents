# Box <-> Render sync. Render is source of truth for state.json only when its updated_at is newer.
import json,os,time,urllib.request,datetime
D="/workspace/desk"; URL=open(f"{D}/dashboard/.render_url").read().strip(); TOK=open(f"{D}/dashboard/.sync").read().strip()
def rd(f):
    try: return json.load(open(f"{D}/{f}"))
    except Exception: return {}
def T(x):
    try: return datetime.datetime.fromisoformat(x.get("updated_at","")).timestamp()
    except Exception: return 0
def req(m,body=None):
    r=urllib.request.Request(URL+"/api/sync",method=m,data=json.dumps(body).encode() if body else None,headers={"Authorization":"Bearer "+TOK,"Content-Type":"application/json"})
    return json.load(urllib.request.urlopen(r,timeout=90))
while True:
    try:
        remote=req("GET").get("state.json") or {}; local=rd("state.json")
        if T(remote)>T(local):
            tmp=f"{D}/state.json.tmp"; json.dump(remote,open(tmp,"w"),indent=2,ensure_ascii=False); os.replace(tmp,f"{D}/state.json"); print(time.strftime("%H:%M:%S"),"pulled state from Render",flush=True)
        req("PUT",{"state.json":rd("state.json"),"leads.json":rd("leads.json"),"top10.json":rd("top10.json"),"activity.json":rd("activity.json")})
    except Exception as e: print(time.strftime("%H:%M:%S"),"sync error",e,flush=True)
    time.sleep(int(os.environ.get("SYNC_EVERY","30")))
