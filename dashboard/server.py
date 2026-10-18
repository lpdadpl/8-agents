import json,os,datetime,html,fcntl,base64,hmac
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse,parse_qs
D=os.environ.get("DESK_DIR","/workspace/desk"); P=int(os.environ.get("PORT","8787"))
MEM=os.environ.get("STORAGE")=="memory"; STORE={}; import threading; LK=threading.Lock()
SYNC=os.environ.get("SYNC_TOKEN","")
def rd(f):
    if MEM: return json.loads(json.dumps(STORE.get(f,{})))
    try: return json.load(open(f"{D}/{f}"))
    except Exception: return {}
def _ts(x):
    try: return datetime.datetime.fromisoformat(x.get("updated_at","")).timestamp()
    except Exception: return 0
def wr_state(fn):
    if MEM:
        with LK:
            s=rd("state.json"); fn(s); s["updated_at"]=datetime.datetime.now().astimezone().isoformat(); STORE["state.json"]=s
        return
    with open(f"{D}/state.lock","w") as lk:
        fcntl.flock(lk,fcntl.LOCK_EX); s=rd("state.json"); fn(s)
        s["updated_at"]=datetime.datetime.now().astimezone().isoformat()
        tmp=f"{D}/state.json.tmp"; json.dump(s,open(tmp,"w"),indent=2,ensure_ascii=False); os.replace(tmp,f"{D}/state.json")
e=html.escape
_u=os.environ.get("DASH_USERS") or open(f"{D}/dashboard/.auth").read()
AUTHS=["Basic "+base64.b64encode(l.strip().encode()).decode() for l in _u.replace(",","\n").splitlines() if ":" in l]
OFFICE_HTML=r'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mesa · Oficina</title>
<style>
:root{--bg:#1b1d2a;--floor:#2a2d40;--tile:#30344a;--txt:#eef}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,sans-serif;background:var(--bg);color:var(--txt)}
header{display:flex;flex-wrap:wrap;gap:10px;align-items:center;padding:10px 16px;background:#14151f;border-bottom:2px solid #333}
header h1{font-size:18px;margin:0 12px 0 0}.pill{padding:3px 10px;border-radius:12px;font-size:13px;background:#2b2e44}
.ok{background:#1f6d3a}.bad{background:#8b1e1e}.funnel span{margin-right:6px}
#floor{position:relative;margin:16px auto;max-width:1150px;padding:20px;border-radius:18px;
 background:repeating-conic-gradient(var(--floor) 0 25%,var(--tile) 0 50%) 0 0/60px 60px;box-shadow:inset 0 0 60px #0008}
.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:18px}
.boss{grid-column:2/4;grid-row:2}
@media(max-width:800px){.grid{grid-template-columns:repeat(2,1fr)}.boss{grid-column:1/3;grid-row:auto}}
.desk{position:relative;background:#00000040;border-radius:16px;padding:8px;text-align:center;cursor:pointer;transition:transform .2s}
.desk:hover{transform:translateY(-3px)}.desk svg{width:100%;height:auto;display:block}
.name{font-weight:700;letter-spacing:1px}.role{font-size:11px;opacity:.75}
.st{font-size:11px;font-weight:700;padding:1px 8px;border-radius:8px;display:inline-block;margin-top:3px}
.desk.run .st{background:#1f6d3a}.desk.off .st{background:#8b1e1e}
.desk.off svg .botg{filter:grayscale(1) brightness(.6)}
.run .bob{animation:bob 1.2s ease-in-out infinite}.run .armL{animation:type .25s infinite alternate;transform-origin:center}
.run .armR{animation:type .25s .12s infinite alternate}.run .scr{animation:flick 1.5s infinite}
.run .walk{animation:walk 9s ease-in-out infinite}.run .blink{animation:blink 4s infinite;transform-origin:center 50px}
.run .glow{animation:glow 1s infinite alternate}
.zz{display:none}.off .zz{display:block;animation:zz 2s infinite}.off .eyesOpen{display:none}.eyesShut{display:none}.off .eyesShut{display:block}
.off .scr{fill:#111!important}
@keyframes bob{50%{transform:translateY(-4px)}}@keyframes type{to{transform:translateY(-5px)}}
@keyframes flick{0%,100%{opacity:1}50%{opacity:.75}52%{opacity:.4}54%{opacity:1}}
@keyframes walk{0%,80%,100%{transform:translateX(0)}88%{transform:translateX(18px)}}
@keyframes blink{0%,94%,100%{transform:scaleY(1)}97%{transform:scaleY(.1)}}
@keyframes glow{to{opacity:.3}}@keyframes zz{0%{opacity:0;transform:translate(0,0)}50%{opacity:1}100%{opacity:0;transform:translate(10px,-14px)}}
.menu{position:absolute;z-index:20;background:#fff;color:#222;border-radius:10px;box-shadow:0 8px 30px #000a;overflow:hidden;min-width:200px}
.menu button{display:block;width:100%;padding:10px 14px;border:0;background:none;text-align:left;font-size:14px;cursor:pointer}.menu button:hover{background:#eef}
#modal{position:fixed;inset:0;background:#000a;display:none;align-items:center;justify-content:center;z-index:30}
#modal .box{background:#1f2133;max-width:95vw;width:1000px;max-height:85vh;overflow:auto;border-radius:14px;padding:16px}
table{border-collapse:collapse;width:100%;font-size:12px}td,th{border:1px solid #444;padding:4px 6px;text-align:left}code{font-size:11px}
.x{float:right;cursor:pointer;font-size:20px}footer{text-align:center;font-size:11px;opacity:.6;padding:10px}
</style></head><body>
<header><h1>🏢 Mesa de memecoins</h1><span id="fl" class="pill">…</span><span class="pill funnel" id="fn"></span><span class="pill" id="upd"></span></header>
<div id="floor"><div class="grid" id="grid"></div></div>
<div id="modal"><div class="box"><span class="x" onclick="closeM()">✕</span><div id="mc"></div></div></div>
<footer>Panel de control sin wallet, sin claves y sin firma · se actualiza cada 12 s · clic en un bot para opciones</footer>
<script>
const AG=[["SEARCH","#3fa7ff","search"],["RISK","#ffb02e","shield"],["WHALE","#2fd3c6","whale"],["SHILL","#ff5fa2","mega"],
["SNIPER","#7bd148","cross"],["EXIT","#b48cff","exit"],["RUG","#ff4b4b","alarm"]];
const STAGE={SEARCH:"escaneado",RISK:"aprobado",WHALE:"confirmado",SHILL:"confirmado",SNIPER:"ejecutado",EXIT:"cerrado",RUG:"cerrado"};
const STAGES=["escaneado","aprobado","confirmado","ejecutado","cerrado"];
let S={},LD=[],ACT=[];
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
function acc(k,c){return{
search:`<g transform="translate(78,8)"><circle cx="0" cy="0" r="9" fill="#cdf" stroke="#234" stroke-width="3"/><rect x="5" y="6" width="4" height="12" fill="#234" transform="rotate(-40 5 6)"/></g>`,
shield:`<path d="M60 4 l14 5 v10 c0 9-7 14-14 17 c-7-3-14-8-14-17 v-10z" fill="#ffd36e" stroke="#7a5200" stroke-width="2" transform="translate(0,-14) scale(.8) translate(15,0)"/>`,
whale:`<g><ellipse cx="60" cy="10" rx="24" ry="9" fill="#1e7fd0"/><path d="M82 8 q10-10 8 4 q-4-2-8 0z" fill="#1e7fd0"/><circle cx="50" cy="8" r="2" fill="#fff"/><path d="M60 1 q-3-8 -7-6 M60 1 q3-8 7-6" stroke="#9cf" stroke-width="2" fill="none"/></g>`,
mega:`<g transform="translate(84,40)"><path d="M0 0 l16-8 v22 l-16-8z" fill="#ffe" stroke="#a24" stroke-width="2"/><path d="M20 -6 q6 9 0 18" stroke="#fff" fill="none" stroke-width="2" class="glow"/></g>`,
cross:`<g><rect x="36" y="25" width="48" height="12" rx="6" fill="#0a2" opacity=".85"/><circle cx="60" cy="31" r="5" fill="none" stroke="#f33" stroke-width="2"/><path d="M60 24v14M53 31h14" stroke="#f33" stroke-width="1.5"/></g>`,
exit:`<g transform="translate(76,0)"><rect width="26" height="12" rx="2" fill="#1b5"/><text x="13" y="9" font-size="8" fill="#fff" text-anchor="middle" font-weight="700">EXIT</text></g>`,
alarm:`<g><rect x="54" y="0" width="12" height="9" rx="5" fill="#f22" class="glow"/><path d="M48 2 l-6-4 M72 2 l6-4" stroke="#f66" stroke-width="2" class="glow"/></g>`}[k]}
function bot(c,k,big){return `<svg viewBox="0 0 120 ${big?130:120}">
<rect x="10" y="${big?92:88}" width="100" height="10" rx="3" fill="#6b4a2d"/><rect x="18" y="${big?102:98}" width="6" height="20" fill="#4a3220"/><rect x="96" y="${big?102:98}" width="6" height="20" fill="#4a3220"/>
<g class="walk"><g class="botg bob">
<line x1="60" y1="14" x2="60" y2="20" stroke="#ccc" stroke-width="2"/><circle cx="60" cy="13" r="3" fill="${c}"/>
<rect x="40" y="20" width="40" height="30" rx="10" fill="${c}"/><rect x="45" y="27" width="30" height="16" rx="6" fill="#102"/>
<g class="eyesOpen blink"><circle cx="53" cy="35" r="3" fill="#7ff"/><circle cx="67" cy="35" r="3" fill="#7ff"/></g>
<g class="eyesShut"><path d="M50 35h6M64 35h6" stroke="#7ff" stroke-width="2"/></g>
<rect x="44" y="52" width="32" height="26" rx="8" fill="${c}"/><circle cx="60" cy="64" r="4" fill="#fff8"/>
<rect class="armL" x="32" y="60" width="12" height="7" rx="3" fill="${c}"/><rect class="armR" x="76" y="60" width="12" height="7" rx="3" fill="${c}"/>
${acc(k,c)}</g></g>
<rect x="74" y="66" width="34" height="22" rx="2" fill="#222"/><rect class="scr" x="76" y="68" width="30" height="17" fill="${c}55"/>
<path class="scr" d="M78 80 l5-4 4 3 5-7 5 3 6-5" stroke="#7f7" fill="none" stroke-width="1.5"/>
<rect x="30" y="84" width="34" height="5" rx="2" fill="#ccc"/>
<text class="zz" x="78" y="20" font-size="14" fill="#9cf" font-weight="700">Zzz</text></svg>`}
function bossSvg(){return `<svg viewBox="0 0 260 150"><rect x="20" y="104" width="220" height="16" rx="5" fill="#7a5530"/><rect x="34" y="120" width="10" height="26" fill="#4a3220"/><rect x="216" y="120" width="10" height="26" fill="#4a3220"/>
<g class="botg bob"><path d="M95 22 l10 -16 l12 12 l13 -14 l13 14 l12 -12 l10 16z" fill="#ffd700" stroke="#a80" stroke-width="2"/>
<rect x="88" y="22" width="84" height="56" rx="20" fill="#5a6cff"/><rect x="98" y="34" width="64" height="32" rx="12" fill="#0b0f2a"/>
<g class="eyesOpen blink"><circle cx="116" cy="50" r="6" fill="#8ff"/><circle cx="144" cy="50" r="6" fill="#8ff"/><circle cx="118" cy="48" r="2" fill="#fff"/><circle cx="146" cy="48" r="2" fill="#fff"/></g>
<g class="eyesShut"><path d="M110 50h12M138 50h12" stroke="#8ff" stroke-width="3"/></g>
<path d="M120 60 q10 6 20 0" stroke="#8ff" stroke-width="2" fill="none"/><circle cx="96" cy="58" r="4" fill="#f9a"/><circle cx="164" cy="58" r="4" fill="#f9a"/>
<rect x="100" y="80" width="60" height="26" rx="10" fill="#5a6cff"/><path d="M130 80 l-6 8 6 16 6-16z" fill="#e33"/>
<rect class="armL" x="78" y="86" width="22" height="10" rx="5" fill="#5a6cff"/><rect class="armR" x="160" y="86" width="22" height="10" rx="5" fill="#5a6cff"/></g>
<rect x="30" y="74" width="46" height="30" rx="3" fill="#222"/><rect class="scr" x="33" y="77" width="40" height="24" fill="#5a6cff55"/><path class="scr" d="M36 96 l8-6 8 4 8-10 10 4" stroke="#7f7" fill="none" stroke-width="2"/>
<rect x="190" y="88" width="30" height="16" rx="2" fill="#eee"/><text x="205" y="99" font-size="7" text-anchor="middle" fill="#333">APPROVE?</text>
<text class="zz" x="180" y="30" font-size="20" fill="#9cf" font-weight="700">Zzz</text></svg>`}
function build(){const g=document.getElementById("grid");let h="";
 AG.forEach(([n,c,k],i)=>{h+=`<div class="desk" id="d-${n}" onclick="menu(event,'${n}')">${bot(c,k)}<div class="name" style="color:${c}">${n}</div><div class="role" id="r-${n}"></div><div class="st" id="s-${n}"></div></div>`;
  if(i==3)h+=`<div class="desk boss" id="d-BOSS" onclick="menu(event,'BOSS')">${bossSvg()}<div class="name" style="color:#ffd700">BOT DESK · Jefe de Mesa</div><div class="st" id="s-BOSS"></div></div>`});
 g.innerHTML=h}
async function j(u){const r=await fetch(u,{cache:"no-store"});return r.json()}
async function load(){try{[S,LD,ACT]=await Promise.all([j("/api/state"),j("/api/leads").then(x=>x.leads||[]),j("/api/activity").then(x=>x.entries||[]).catch(()=>[])]);render()}catch(e){document.getElementById("upd").textContent="⚠ sin conexión"}}
function render(){const halted=S.floor!=="RUNNING",fl=document.getElementById("fl");
 fl.textContent="Planta: "+(halted?"PARADA (HALT)":"EN MARCHA");fl.className="pill "+(halted?"bad":"ok");
 document.getElementById("fn").innerHTML=STAGES.map(s=>`<span>${s}: <b>${LD.filter(l=>l.stage===s).length}</b></span>`).join("");
 document.getElementById("upd").textContent="act. "+new Date().toLocaleTimeString("es-ES");
 const ags=S.agents||{};AG.forEach(([n])=>{const a=ags[n]||{},on=a.status==="RUNNING"&&!halted,d=document.getElementById("d-"+n);
  d.className="desk "+(on?"run":"off");document.getElementById("r-"+n).textContent=a.role||"";
  document.getElementById("s-"+n).textContent=a.status==="PAUSED"?"PAUSADO":(halted?"PLANTA PARADA":"TRABAJANDO")});
 const b=ags["BOT DESK"]||{},bon=b.status==="RUNNING"&&!halted;document.getElementById("d-BOSS").className="desk boss "+(bon?"run":"off");
 document.getElementById("s-BOSS").textContent=halted?"PLANTA PARADA":(b.status==="PAUSED"?"PAUSADO":"COORDINANDO")}
function closeMenu(){document.querySelectorAll(".menu").forEach(m=>m.remove())}
function menu(ev,n){ev.stopPropagation();closeMenu();const m=document.createElement("div");m.className="menu";
 if(n==="BOSS"){const h=S.floor!=="RUNNING";m.innerHTML=`<button onclick="history_()">📜 Ver histórico de operaciones</button><button onclick="floorT(${h})">${h?"▶️ Reanudar todo":"⛔ Parar todo"}</button>`}
 else{const p=(S.agents||{})[n]?.status==="PAUSED";m.innerHTML=`<button onclick="ops('${n}')">📋 Ver últimas operaciones</button><button onclick="agT('${n}',${p})">${p?"▶️ Reanudar":"⏸️ Parar"}</button>`}
 m.style.left=(ev.pageX-20)+"px";m.style.top=(ev.pageY+8)+"px";document.body.appendChild(m)}
document.addEventListener("click",closeMenu);
async function post(u,b){await fetch(u,{method:"POST",headers:{"Content-Type":"application/x-www-form-urlencoded"},body:new URLSearchParams(b)});await load()}
function agT(n,p){closeMenu();post("/agent",{n,a:p?"resume":"pause"})}
function floorT(h){closeMenu();if(confirm(h?"¿Reanudar TODA la planta?":"¿Parar TODA la planta (HALT)? Ningún agente actuará."))post("/floor",{a:h?"resume":"halt"})}
function openM(h){document.getElementById("mc").innerHTML=h;document.getElementById("modal").style.display="flex"}
function closeM(){document.getElementById("modal").style.display="none"}
const dt=s=>s?new Date(s).toLocaleString("es-ES"):"";
function ops(n){closeMenu();const st=STAGE[n];
 const ls=LD.filter(l=>l.owner===n||l.stage===st||(l.history||[]).some(h=>h.by===n)).slice(-20).reverse();
 const ac=ACT.filter(a=>a.agent===n).slice(-30).reverse();
 openM(`<h2>${n} · últimas operaciones</h2><h3>Leads (${ls.length})</h3><table><tr><th>Lead</th><th>Símbolo</th><th>Contrato</th><th>Etapa</th><th>Aprobación</th><th>Actualizado</th></tr>${ls.map(l=>`<tr><td>${esc(l.lead_id)}</td><td>${esc(l.symbol)}</td><td><code>${esc(l.contract)}</code></td><td>${esc(l.stage)}</td><td>${esc(l.approval)}</td><td>${dt(l.updated_at)}</td></tr>`).join("")||"<tr><td colspan=6>Sin leads</td></tr>"}</table>
 <h3>Actividad (${ac.length})</h3><table><tr><th>Hora</th><th>Lead</th><th>Acción</th><th>Detalle</th></tr>${ac.map(a=>`<tr><td>${dt(a.ts)}</td><td>${esc(a.lead_id||"")}</td><td>${esc(a.action)}</td><td>${esc(a.detail)}</td></tr>`).join("")||"<tr><td colspan=4>Sin actividad registrada</td></tr>"}</table>`)}
function history_(){closeMenu();
 openM(`<h2>Histórico de operaciones</h2><p>${STAGES.map(s=>`${s}: <b>${LD.filter(l=>l.stage===s).length}</b>`).join(" → ")}</p><table><tr><th>Lead</th><th>Símbolo</th><th>Contrato</th><th>Etapa</th><th>Aprobación</th><th>Creado</th><th>Historial</th></tr>${LD.map(l=>`<tr><td>${esc(l.lead_id)}</td><td>${esc(l.symbol)}</td><td><code>${esc(l.contract)}</code></td><td>${esc(l.stage)}</td><td>${esc(l.approval)}</td><td>${dt(l.created_at)}</td><td>${(l.history||[]).map(h=>`${esc(h.stage)} (${esc(h.by)}, ${dt(h.at)})`).join("<br>")}</td></tr>`).join("")}</table>`)}
build();load();setInterval(load,12000);
</script></body></html>
'''
def page_old():
    s,l,t=rd("state.json"),rd("leads.json"),rd("top10.json"); fl=s.get("floor","?")
    r=[f"<html><head><meta charset=utf-8><meta http-equiv=refresh content=15><title>Mesa</title><style>body{{font-family:sans-serif;background:#111;color:#eee;margin:20px}}table{{border-collapse:collapse;margin-bottom:20px}}td,th{{border:1px solid #444;padding:4px 8px}}.RUNNING{{color:#4c4}}.PAUSED,.HALTED{{color:#f55}}button{{padding:4px 10px}}code{{font-size:12px}}</style></head><body>",
       f"<h1>Mesa de memecoins — Panel</h1><p>Planta: <b class={fl}>{fl}</b> · actualizado {e(s.get('updated_at',''))} · se refresca cada 15 s</p>",
       f"<form method=post action=/floor><button name=a value={'resume' if fl=='HALTED' else 'halt'}>{'REANUDAR PLANTA' if fl=='HALTED' else 'PARAR PLANTA (HALT)'}</button></form>",
       "<h2>Agentes</h2><table><tr><th>Agente</th><th>Rol</th><th>Estado</th><th>Efectivo</th><th></th></tr>"]
    for n,a in s.get("agents",{}).items():
        st=a["status"]; ef="RUNNING" if st=="RUNNING" and fl=="RUNNING" else "PAUSED"
        r.append(f"<tr><td>{e(n)}</td><td>{e(a.get('role',''))}</td><td class={st}>{st}</td><td class={ef}>{ef}</td><td><form method=post action=/agent style=margin:0><input type=hidden name=n value='{e(n)}'><button name=a value={'resume' if st=='PAUSED' else 'pause'}>{'Reanudar' if st=='PAUSED' else 'Pausar'}</button></form></td></tr>")
    r.append("</table><h2>Órdenes / leads</h2><table><tr><th>Lead ID</th><th>Símbolo</th><th>Contrato</th><th>Etapa</th><th>Aprobación</th><th>Creado</th><th>Actualizado</th></tr>")
    for x in l.get("leads",[]): r.append(f"<tr><td>{e(x['lead_id'])}</td><td>{e(str(x.get('symbol','')))}</td><td><code>{e(x['contract'])}</code></td><td>{e(x['stage'])}</td><td>{e(x.get('approval',''))}</td><td>{e(x.get('created_at',''))}</td><td>{e(x.get('updated_at',''))}</td></tr>")
    r.append(f"</table><h2>Top 10 SOL (vol 1h)</h2><p>{e(t.get('generated_at',''))}</p><table><tr><th>#</th><th>Símbolo</th><th>Nombre</th><th>Mint</th><th>Vol 1h USD</th><th>Fuente</th></tr>")
    for x in t.get("tokens",[]): r.append(f"<tr><td>{x['rank']}</td><td>{e(x['symbol'])}</td><td>{e(x['name'])}</td><td><code>{e(x['mint'])}</code></td><td>{x['volume_1h_usd']:,.0f}</td><td><a style=color:#8af href='{e(x['source_url'])}'>ver</a></td></tr>")
    r.append("</table>"+"".join(f"<p style=color:#fa0>⚠ {e(w)}</p>" for w in t.get("warnings",[]))+"<p style=color:#888>Panel de solo control: sin wallet, sin claves, sin firma.</p></body></html>")
    return "".join(r)
class H(BaseHTTPRequestHandler):
    def snd(self,c,b,ct="text/html; charset=utf-8"):
        b=b.encode(); self.send_response(c); self.send_header("Content-Type",ct); self.send_header("Content-Length",len(b)); self.end_headers(); self.wfile.write(b)
    def ok(self):
        h=self.headers.get("Authorization","")
        if any(hmac.compare_digest(h.encode(),a.encode()) for a in AUTHS): return True
        self.send_response(401); self.send_header("WWW-Authenticate",'Basic realm="Mesa"'); self.send_header("Content-Length","0"); self.end_headers(); return False
    def tok(self):
        return bool(SYNC) and hmac.compare_digest(self.headers.get("Authorization","").encode(),("Bearer "+SYNC).encode())
    def do_PUT(self):
        if self.path!="/api/sync" or not self.tok(): return self.snd(401,"")
        b=json.loads(self.rfile.read(int(self.headers.get("Content-Length",0))))
        with LK:
            for k in ("state.json","leads.json","top10.json","activity.json"):
                if k in b and b[k]:
                    if k=="state.json" and MEM and _ts(STORE.get(k,{}))>_ts(b[k]): continue
                    STORE[k]=b[k]
        self.snd(200,json.dumps({k:STORE.get(k) for k in ("state.json",)}),"application/json")
    def do_GET(self):
        if self.path=="/api/sync":
            return self.snd(200,json.dumps({"state.json":rd("state.json")}),"application/json") if self.tok() else self.snd(401,"")
        if self.path=="/healthz": return self.snd(200,"ok","text/plain")
        if not self.ok(): return
        p=urlparse(self.path).path
        if p=="/": self.snd(200,OFFICE_HTML)
        elif p=="/clasico": self.snd(200,page_old())
        elif p in("/api/state","/api/leads","/api/top10","/api/activity"): self.snd(200,json.dumps(rd(p[5:]+".json"),ensure_ascii=False),"application/json")
        else: self.snd(404,"no")
    def do_POST(self):
        if not self.ok(): return
        q=parse_qs(self.rfile.read(int(self.headers.get("Content-Length",0))).decode()); a=q.get("a",[""])[0]; p=urlparse(self.path).path
        if p=="/floor" and a in("halt","resume"): wr_state(lambda s:s.__setitem__("floor","HALTED" if a=="halt" else "RUNNING"))
        elif p=="/agent" and a in("pause","resume"):
            n=q.get("n",[""])[0]; now=datetime.datetime.now().astimezone().isoformat()
            def f(s):
                if n in s["agents"]: s["agents"][n].update(status="PAUSED" if a=="pause" else "RUNNING",updated_at=now)
            wr_state(f)
        else: return self.snd(400,"bad")
        self.send_response(303); self.send_header("Location","/"); self.end_headers()
    def log_message(self,*a): pass
ThreadingHTTPServer(("0.0.0.0",P),H).serve_forever()
