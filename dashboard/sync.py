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
        R=req("GET"); remote=R.get("state.json") or {}; remote_dig=R.get("files_digest",""); local=rd("state.json")
        if T(remote)>T(local):
            tmp=f"{D}/state.json.tmp"; json.dump(remote,open(tmp,"w"),indent=2,ensure_ascii=False); os.replace(tmp,f"{D}/state.json"); print(time.strftime("%H:%M:%S"),"pulled state from Render",flush=True)
        body={}
        try:
            import hashlib,importlib.util
            spec=importlib.util.spec_from_file_location("srv_files",f"{D}/dashboard/files_lib.py"); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
            fl=m.collect(); dig=hashlib.sha256(json.dumps(fl,sort_keys=True).encode()).hexdigest()
            if dig!=remote_dig: body={"files":fl,"files_digest":dig}
        except Exception as e: print(time.strftime("%H:%M:%S"),"files error",e,flush=True)
        req("PUT",{**body,"state.json":rd("state.json"),"leads.json":rd("leads.json"),"top10.json":rd("top10.json"),"activity.json":rd("activity.json")})
    except Exception as e: print(time.strftime("%H:%M:%S"),"sync error",e,flush=True)
    time.sleep(int(os.environ.get("SYNC_EVERY","30")))
