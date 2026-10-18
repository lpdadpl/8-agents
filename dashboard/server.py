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
OFFICE_HTML=r'''<!doctype html><html lang="es"><head><meta charset="utf-8"><link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🤖</text></svg>"><link rel="apple-touch-icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='%231b1d2a'/><text y='.9em' x='5' font-size='80'>🤖</text></svg>"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Mesa · Oficina</title>
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

.ops h2{margin:0 0 4px;font-size:22px}.sub{opacity:.7;font-size:13px;margin-bottom:12px}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}.chip{border:1px solid #fff3;background:#ffffff10;color:#eef;padding:5px 12px;border-radius:20px;cursor:pointer;font-size:12px;transition:.2s}
.chip.on{background:#5a6cff;border-color:#5a6cff}.srch{width:100%;padding:10px 14px;border-radius:12px;border:1px solid #fff2;background:#0006;color:#fff;font-size:14px;outline:none}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:12px}
.card{background:linear-gradient(145deg,#ffffff14,#ffffff06);border:1px solid #ffffff1c;border-radius:16px;padding:12px 14px;cursor:pointer;backdrop-filter:blur(8px);transition:transform .2s,box-shadow .2s;animation:pop .35s both}
.card:hover{transform:translateY(-3px);box-shadow:0 10px 30px #0008;border-color:#5a6cff88}
@keyframes pop{from{opacity:0;transform:translateY(8px)}}
.ch{display:flex;align-items:center;gap:10px}.av{width:42px;height:42px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px;color:#fff;flex:none;box-shadow:inset 0 -3px 0 #0003}
.sym{font-size:22px;font-weight:800;letter-spacing:.5px;line-height:1}.lid{font-size:11px;opacity:.6;font-family:ui-monospace,monospace}
.pillS{margin-left:auto;font-size:11px;font-weight:700;padding:3px 9px;border-radius:10px;color:#111}
.fbar{display:flex;gap:3px;margin:10px 0 8px}.fbar i{flex:1;height:5px;border-radius:3px;background:#ffffff1a}.fbar i.f{background:var(--c)}
.row{display:flex;align-items:center;gap:8px;font-size:12px;flex-wrap:wrap}.ca{font-family:ui-monospace,monospace;background:#0005;padding:2px 7px;border-radius:6px}
.cp{border:0;background:#ffffff18;color:#fff;border-radius:6px;padding:2px 7px;cursor:pointer;font-size:11px}.cp:hover{background:#5a6cff}
.bd{font-size:10px;font-weight:700;padding:2px 7px;border-radius:8px;text-transform:uppercase}.b-pendiente{background:#8a6d00}.b-APPROVE{background:#1f6d3a}.b-RECHAZADO{background:#8b1e1e}
.pnl{font-weight:700}.pos{color:#4ee08a}.neg{color:#ff6b6b}.rt{margin-left:auto;opacity:.6}.warn{color:#ffb02e}
#drawer{position:fixed;top:0;right:0;height:100%;width:min(520px,100vw);background:#181a2bee;backdrop-filter:blur(16px);border-left:1px solid #fff2;z-index:40;transform:translateX(105%);transition:transform .35s cubic-bezier(.2,.8,.2,1);overflow:auto;padding:20px;box-shadow:-20px 0 50px #0009}
#drawer.open{transform:none}#dshade{position:fixed;inset:0;background:#0007;z-index:39;opacity:0;pointer-events:none;transition:.3s}#dshade.open{opacity:1;pointer-events:auto}
.dh{display:flex;align-items:center;gap:12px}.dh .av{width:56px;height:56px;font-size:24px}.big{font-size:30px;font-weight:800}
.sec{margin-top:18px}.sec h4{margin:0 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:1px;opacity:.6}
.full{font-family:ui-monospace,monospace;font-size:12px;word-break:break-all;background:#0006;padding:8px 10px;border-radius:10px;display:flex;gap:8px;align-items:center}
.links a{display:inline-block;margin:4px 6px 0 0;padding:6px 12px;border-radius:10px;background:#ffffff12;color:#cfe;text-decoration:none;font-size:12px;border:1px solid #fff2}.links a:hover{background:#5a6cff}
.tl{position:relative;margin-left:18px;border-left:2px solid #ffffff22;padding-left:20px}
.ti{position:relative;margin-bottom:14px;animation:pop .4s both}.ti .dot{position:absolute;left:-39px;top:-2px;width:34px;height:34px;border-radius:50%;overflow:hidden;background:#222;border:2px solid var(--c)}
.ti .dot svg{width:56px;margin:-6px 0 0 -11px}.ti.pend{opacity:.4}.ti b{font-size:14px}.ti .m{font-size:11px;opacity:.7}.ti .n{font-size:12px;margin-top:3px;background:#ffffff0c;padding:5px 8px;border-radius:8px}
.chk{display:flex;gap:8px;font-size:13px;margin:4px 0}.wbox{background:#ffb02e22;border:1px solid #ffb02e66;color:#ffd38a;padding:10px;border-radius:10px;font-size:13px;margin-top:6px}
.xx{position:absolute;right:16px;top:14px;font-size:22px;cursor:pointer;opacity:.7}
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#5a6cff;padding:8px 16px;border-radius:20px;z-index:60;font-size:13px}
#modal .box{background:#1b1d2ef0;backdrop-filter:blur(14px);border:1px solid #fff2}

#sb{position:fixed;top:0;left:0;height:100%;width:260px;background:#14151fe8;backdrop-filter:blur(14px);border-right:1px solid #fff2;z-index:35;overflow:auto;transition:transform .3s cubic-bezier(.2,.8,.2,1);padding:10px 12px 20px}
body.sbc #sb{transform:translateX(-100%)}body:not(.sbc) #floor{margin-left:max(280px,calc((100vw - 1150px)/2))}#floor{transition:margin .3s}
#sbt{position:fixed;top:10px;left:10px;z-index:36;border:1px solid #fff3;background:#1f2133e0;color:#fff;border-radius:10px;width:38px;height:38px;font-size:18px;cursor:pointer;transition:left .3s}
body:not(.sbc) #sbt{left:214px}
.sbh{padding:6px 0 14px;font-size:15px;padding-right:46px}.sbs{margin-bottom:16px}.sbt{font-size:11px;text-transform:uppercase;letter-spacing:1px;opacity:.55;margin:4px 0 6px}
#sb .pill{display:block;text-align:center;font-weight:700;padding:6px}.fn{display:grid;grid-template-columns:1fr auto;gap:3px 8px;font-size:12px;margin:8px 0}.fn .dotc{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px}
.ql a,.nav{display:flex;align-items:center;gap:8px;color:#dde;text-decoration:none;padding:7px 9px;border-radius:10px;font-size:13px;transition:.2s}.ql a:hover,.nav:hover{background:#ffffff14}
.ql{display:flex;gap:4px;flex-wrap:wrap}.nav .mini{width:28px;height:28px;border-radius:8px;overflow:hidden;background:#0004;flex:none}.nav .mini svg{width:46px;margin:-4px 0 0 -9px}
.nav .sd{margin-left:auto;width:8px;height:8px;border-radius:50%}
#sbshade{display:none}
@media(max-width:800px){body:not(.sbc) #floor{margin-left:auto}#sb{box-shadow:20px 0 40px #0009}body:not(.sbc) #sbshade{display:block;position:fixed;inset:0;background:#0007;z-index:34}}
#floor{margin-top:56px}
.doc h2{margin:0 0 6px}.doc h3{margin:18px 0 6px;font-size:15px;color:#9fb0ff}.doc p,.doc li{font-size:14px;line-height:1.55;opacity:.92}
.doc code{background:#0006;padding:1px 6px;border-radius:6px}.fl2{display:flex;flex-wrap:wrap;gap:6px;align-items:center}.fl2 span{padding:4px 10px;border-radius:10px;color:#111;font-weight:700;font-size:12px}
.rt2{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;font-size:13px}.rule{background:#8b1e1e33;border:1px solid #ff6b6b55;border-radius:10px;padding:8px 12px;margin:5px 0;font-size:13px}
.bh{display:flex;gap:14px;align-items:center}.bh .mini{width:90px;height:90px;border-radius:18px;background:#0005;overflow:hidden;flex:none}.bh .mini svg{width:130px;margin:-6px 0 0 -20px}
.btn{border:0;border-radius:10px;padding:8px 14px;font-weight:700;cursor:pointer;color:#fff}.bstop{background:#8b1e1e}.bgo{background:#1f6d3a}
#modal{z-index:45!important}#dshade{z-index:48!important}#drawer{z-index:50!important}#upd{font-size:12px;opacity:.7}
</style></head><body>
<button id="sbt" onclick="toggleSB()" title="Menú">☰</button>
<aside id="sb"><div class="sbh">🏢 <b>Mesa de memecoins</b></div>
<div class="sbs"><div id="fl" class="pill">…</div><div class="fn" id="fn"></div><div class="m" id="upd"></div>
<div class="ql"><a href="#" onclick="history_();return false">📜 Histórico</a><a href="/clasico">🗂 Vista clásica</a></div></div>
<div class="sbs"><div class="sbt">Información</div><a class="nav" href="#" onclick="proj();return false">📘 El proyecto</a></div>
<div class="sbs"><div class="sbt">Agentes</div><div id="navb"></div></div>
<div class="m" style="opacity:.5;padding:10px">Sin wallet · sin claves · sin firma</div></aside>
<div id="sbshade" onclick="toggleSB(false)"></div>
<div id="floor"><div class="grid" id="grid"></div></div>
<div id="modal"><div class="box"><span class="x" onclick="closeM()">✕</span><div id="mc"></div></div></div>
<div id="dshade" onclick="closeD()"></div><div id="drawer"></div>
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

const SC={escaneado:"#3fa7ff",aprobado:"#ffb02e",confirmado:"#2fd3c6",ejecutado:"#7bd148",cerrado:"#b48cff"};
const SAG={escaneado:"SEARCH",aprobado:"RISK",confirmado:"WHALE",ejecutado:"SNIPER",cerrado:"EXIT"};
const AGC=Object.fromEntries(AG.map(a=>[a[0],a]));AGC["BOT DESK"]=["BOT DESK","#5a6cff","search"];
let TOP={},FIL="todos",Q="";
const short=c=>c?c.slice(0,4)+"…"+c.slice(-4):"";
function hue(s){let h=0;for(const ch of String(s))h=(h*31+ch.charCodeAt(0))%360;return `hsl(${h} 65% 48%)`}
function rel(s){if(!s)return"";const d=(Date.now()-new Date(s))/1000;if(d<60)return"hace unos s";if(d<3600)return`hace ${d/60|0} min`;if(d<86400)return`hace ${d/3600|0} h`;return`hace ${d/86400|0} d`}
function copy(t,ev){ev&&ev.stopPropagation();(navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).catch(()=>{const a=document.createElement("textarea");a.value=t;document.body.appendChild(a);a.select();document.execCommand("copy");a.remove()});
 const d=document.createElement("div");d.className="toast";d.textContent="Contrato copiado";document.body.appendChild(d);setTimeout(()=>d.remove(),1400)}
const warnsFor=l=>(TOP.warnings||[]).filter(w=>w.includes(short(l.contract).slice(0,4))||w.includes(l.contract)||(l.symbol&&w.includes(l.symbol+" "+l.contract.slice(0,5))));
function card(l,i){const si=STAGES.indexOf(l.stage),c=SC[l.stage]||"#888",w=warnsFor(l);const pnl=l.pnl_sol??l.pnl;
 return `<div class="card" style="animation-delay:${i*25}ms" onclick="detail('${esc(l.lead_id)}')"><div class="ch"><div class="av" style="background:${hue(l.symbol)}">${esc((l.symbol||"?")[0])}</div>
 <div><div class="sym">${esc(l.symbol)}${w.length?' <span class="warn" title="Aviso">⚠</span>':''}</div><div class="lid">${esc(l.lead_id)}</div></div><span class="pillS" style="background:${c}">${esc(l.stage)}</span></div>
 <div class="fbar" style="--c:${c}">${STAGES.map((s,k)=>`<i class="${k<=si?"f":""}" title="${s}"></i>`).join("")}</div>
 <div class="row"><span class="ca">${short(l.contract)}</span><button class="cp" onclick="copy('${esc(l.contract)}',event)">⧉ copiar</button><span class="bd b-${esc(l.approval)}">${esc(l.approval)}</span>
 ${pnl!=null?`<span class="pnl ${pnl>=0?"pos":"neg"}">${pnl>=0?"+":""}${pnl} SOL</span>`:""}<span class="rt">${rel(l.updated_at)}</span></div></div>`}
function listView(title,sub,leads,withFilters){const f=leads.filter(l=>(FIL==="todos"||l.stage===FIL)&&(!Q||(l.symbol+" "+l.lead_id+" "+l.contract).toLowerCase().includes(Q.toLowerCase())));
 return `<div class="ops"><h2>${title}</h2><div class="sub">${sub}</div>${withFilters?`<input class="srch" placeholder="🔎 Buscar símbolo, lead o contrato…" value="${esc(Q)}" oninput="Q=this.value;rerender()">
 <div class="chips">${["todos",...STAGES].map(s=>`<span class="chip ${FIL===s?"on":""}" onclick="FIL='${s}';rerender()">${s} · ${s==="todos"?leads.length:leads.filter(l=>l.stage===s).length}</span>`).join("")}</div>`:""}
 <div class="cards">${f.map(card).join("")||'<div class="sub">Sin operaciones</div>'}</div></div>`}
let CUR=null;function rerender(){if(!CUR)return;const pos=document.querySelector(".srch")?.selectionStart;CUR();const s=document.querySelector(".srch");if(s&&pos!=null){s.focus();s.setSelectionRange(pos,pos)}}
ops=function(n){closeMenu();FIL="todos";Q="";CUR=()=>{const st=STAGE[n];const ls=LD.filter(l=>l.owner===n||l.stage===st||(l.history||[]).some(h=>h.by===n)).slice().reverse();
 const ac=ACT.filter(a=>a.agent===n).slice(-8).reverse();const [_,c]=AGC[n];
 openM(listView(`<span style="color:${c}">${n}</span> · últimas operaciones`,`${AGC[n]&&(S.agents||{})[n]?.role||""} · ${ls.length} leads`,ls,true)+
 `<div class="sec"><h4>Actividad reciente</h4>${ac.map(a=>`<div class="chk">• <span class="m" style="opacity:.6">${rel(a.ts)}</span> ${esc(a.lead_id||"")} ${esc(a.detail)}</div>`).join("")||'<div class="sub">Sin actividad</div>'}</div>`)};CUR()}
history_=function(){closeMenu();FIL="todos";Q="";CUR=()=>openM(listView("📜 Histórico de operaciones",STAGES.map(s=>`${s} ${LD.filter(l=>l.stage===s).length}`).join(" → "),LD.slice().reverse(),true));CUR()}
const _closeM=closeM;closeM=function(){CUR=null;_closeM()}
function mini(n){const a=AGC[n]||AGC["BOT DESK"];return n==="BOT DESK"?`<svg viewBox="0 0 120 120"><rect x="40" y="20" width="40" height="30" rx="10" fill="#5a6cff"/><path d="M42 20 l6-10 6 7 6-9 6 9 6-7 6 10z" fill="#ffd700"/><circle cx="53" cy="35" r="3" fill="#7ff"/><circle cx="67" cy="35" r="3" fill="#7ff"/></svg>`:bot(a[1],a[2]).replace('<svg viewBox="0 0 120 120">','<svg viewBox="20 0 80 90">')}
function detail(id){const l=LD.find(x=>x.lead_id===id);if(!l)return;const si=STAGES.indexOf(l.stage),w=warnsFor(l),ac=ACT.filter(a=>a.lead_id===id);
 const hist=Object.fromEntries((l.history||[]).map(h=>[h.stage,h]));const rc=l.risk_checks||{};
 const tl=STAGES.map((s,k)=>{const h=hist[s],ag=h?.by||SAG[s],c=(AGC[ag]||AGC["BOT DESK"])[1],notes=ac.filter(a=>a.action===s||a.agent===ag&&k<=si);
  return `<div class="ti ${k>si?"pend":""}" style="--c:${c};animation-delay:${k*60}ms"><div class="dot">${mini(ag)}</div><b style="color:${SC[s]}">${s}</b> <span class="m">· ${esc(ag)}</span>
  <div class="m">${h?new Date(h.at).toLocaleString("es-ES")+" · "+rel(h.at):"pendiente"}</div>${notes.filter(a=>a.action===s).map(a=>`<div class="n">${esc(a.detail)}</div>`).join("")}</div>`}).join("");
 const RL={mint_revoked:"Mint authority revocada",freeze_revoked:"Freeze authority revocada",lp_locked:"Liquidez bloqueada",top_holders_ok:"Top holders < 20%",honeypot_ok:"Honeypot test"};
 const rv=v=>v&&typeof v==="object"?(v.ok??v.pass??v.value):v,rd=v=>v&&typeof v==="object"?(v.detail||v.note||""):"";
 const checks=Array.isArray(rc)?rc.map(x=>[x.name||x.check||"check",rv(x),rd(x)]):Object.keys(rc).length?Object.entries(rc).map(([k,v])=>[RL[k]||k,rv(v),rd(v)]):Object.entries(RL).map(([k,t])=>[t,undefined,""]);
 const pnl=l.pnl_sol??l.pnl;
 document.getElementById("drawer").innerHTML=`<span class="xx" onclick="closeD()">✕</span><div class="dh"><div class="av" style="background:${hue(l.symbol)}">${esc((l.symbol||"?")[0])}</div><div><div class="big">${esc(l.symbol)}</div><div class="lid">${esc(l.lead_id)}</div></div></div>
 <div class="row" style="margin-top:10px"><span class="pillS" style="margin:0;background:${SC[l.stage]}">${esc(l.stage)}</span><span class="bd b-${esc(l.approval)}">aprobación: ${esc(l.approval)}</span>${pnl!=null?`<span class="pnl ${pnl>=0?"pos":"neg"}">PnL ${pnl>=0?"+":""}${pnl} SOL</span>`:'<span class="m" style="opacity:.6">sin PnL</span>'}</div>
 <div class="fbar" style="--c:${SC[l.stage]}">${STAGES.map((s,k)=>`<i class="${k<=si?"f":""}"></i>`).join("")}</div>
 ${w.length?`<div class="sec"><h4>⚠ Avisos</h4>${w.map(x=>`<div class="wbox">${esc(x)}</div>`).join("")}</div>`:""}
 <div class="sec"><h4>Contrato</h4><div class="full"><span style="flex:1">${esc(l.contract)}</span><button class="cp" onclick="copy('${esc(l.contract)}',event)">⧉ copiar</button></div>
 <div class="links"><a target="_blank" rel="noopener" href="https://solscan.io/token/${esc(l.contract)}">Solscan ↗</a><a target="_blank" rel="noopener" href="https://dexscreener.com/solana/${esc(l.contract)}">DexScreener ↗</a><a target="_blank" rel="noopener" href="https://www.geckoterminal.com/solana/tokens/${esc(l.contract)}">GeckoTerminal ↗</a></div></div>
 <div class="sec"><h4>Línea de tiempo</h4><div class="tl">${tl}</div></div>
 <div class="sec"><h4>Checks de riesgo (RISK)</h4>${checks.map(([t,v,d])=>`<div class="chk">${v===true||v==="ok"||v==="pass"?"✅":v===false||v==="fail"?"❌":"⏳"} ${esc(t)}${d?` <span class="m" style="opacity:.6">— ${esc(d)}</span>`:typeof v==="string"&&!["ok","pass","fail"].includes(v)?` <span class="m">${esc(v)}</span>`:""}</div>`).join("")}</div>
 ${l.reason?`<div class="sec"><h4>Motivo (SEARCH)</h4><div class="chk">${esc(l.reason)}</div></div>`:""}${l.source?`<div class="links"><a target="_blank" rel="noopener" href="${esc(l.source)}">Fuente ↗</a></div>`:""}<div class="sec"><h4>Detalles</h4><div class="chk">Responsable: <b>${esc(l.owner)}</b></div><div class="chk">Creado: ${new Date(l.created_at).toLocaleString("es-ES")}</div><div class="chk">Actualizado: ${new Date(l.updated_at).toLocaleString("es-ES")} (${rel(l.updated_at)})</div></div>
 <p class="m" style="opacity:.5;font-size:11px;margin-top:20px">Solo lectura. Ninguna firma ni wallet desde el panel.</p>`;
 document.getElementById("drawer").classList.add("open");document.getElementById("dshade").classList.add("open")}
function closeD(){document.getElementById("drawer").classList.remove("open");document.getElementById("dshade").classList.remove("open")}
document.addEventListener("keydown",e=>{if(e.key==="Escape"){closeD();closeM()}});
const _load=load;load=async function(){try{TOP=await j("/api/top10")}catch(e){}await _load();if(CUR&&document.activeElement?.className!=="srch")rerender()};
async function boot(){await load();const hs=decodeURIComponent(location.hash.slice(1));if(hs.startsWith("bot="))botP(hs.slice(4));else if(hs==="proj")proj();else if(hs==="hist")history_();else if(hs.startsWith("ops="))ops(hs.slice(4));else if(hs.startsWith("lead=")){history_();detail(hs.slice(5))}}

const INFO={
"BOT DESK":{t:"Jefe de Mesa",obs:"El funnel completo, state.json, leads.json y activity.json de toda la planta.",how:"Coordina el grupo Trading Floor, reparte trabajo, hace cumplir el protocolo y prepara el informe de las 21:00. Escribe en state.json (vía panel) y activity.json.",cad:"Continuo; informe diario a las 21:00.",does:"Enruta leads entre agentes, detecta fuentes caídas, eleva a Alberto la única decisión que necesita firma.",lim:"Nunca opera, nunca guarda claves, nunca firma. No cambia límites de riesgo sin Alberto."},
SEARCH:{t:"Descubrimiento",obs:"Pools nuevos y volumen en Solana (DexScreener, GeckoTerminal).",how:"Escanea, filtra por edad/liquidez/volumen/txs y crea leads con ID L-AAAAMMDD-NNN. Escribe leads.json (etapa escaneado) y activity.json.",cad:"Cada hora.",does:"Llena la parte alta del funnel con contrato completo, fuente y motivo.",lim:"No aprueba ni ejecuta nada. Nunca abrevia contratos."},
RISK:{t:"Auditoría de contratos",obs:"Mint/freeze authority, liquidez bloqueada, concentración de holders, honeypot.",how:"Revisa cada lead escaneado y escribe risk_checks en leads.json; mueve a aprobado o marca RECHAZADO. Registra en activity.json.",cad:"Cada 30 min.",does:"Filtra los rugs antes de que cuesten dinero.",lim:"No ejecuta ni firma. Un check dudoso = rechazo."},
WHALE:{t:"Flujo de ballenas",obs:"Movimientos de wallets grandes y smart money sobre los leads aprobados.",how:"Confirma (junto a SHILL) los aprobados y los mueve a confirmado. Escribe activity.json.",cad:"Cada hora.",does:"Aporta convicción on-chain.",lim:"Solo lectura on-chain. No opera."},
SHILL:{t:"Sentimiento social",obs:"X/Telegram: menciones, calidad de la comunidad, bots y shill pagado.",how:"Confirma con WHALE; anota señales en activity.json.",cad:"Cada hora.",does:"Distingue hype orgánico de humo.",lim:"No publica nada ni contacta a nadie. No opera."},
SNIPER:{t:"Ejecución",obs:"Solo leads confirmados con APPROVE de Alberto.",how:"Prepara la orden; la firma la hace Alberto en su wallet. Marca ejecutado en leads.json.",cad:"Solo cuando llega el APPROVE #id literal.",does:"Ejecuta con precisión lo aprobado.",lim:"Nunca firma sin el APPROVE literal de Alberto (no resúmenes, no paráfrasis). Nunca guarda claves."},
EXIT:{t:"Salidas",obs:"Posiciones abiertas: precio, objetivo y stop.",how:"Propone salidas y cierres; marca cerrado y PnL. Escribe activity.json solo si algo cambia.",cad:"Cada 15 min.",does:"Protege beneficios y limita pérdidas.",lim:"No abre posiciones. Cualquier firma pasa por Alberto."},
RUG:{t:"Vigilancia de rugs",obs:"Retiradas de liquidez, ventas del dev, cambios de autoridad en posiciones abiertas.",how:"Alerta al grupo y a Alberto; registra en activity.json.",cad:"Cada 15 min (silencio = todo igual).",does:"Salida rápida ante rug: la única acción pre-aprobada.",lim:"Nunca cierra una posición a solas fuera de la salida de emergencia pre-aprobada."}};
function miniNav(n){return `<span class="mini">${mini(n)}</span>`}
function buildNav(){document.getElementById("navb").innerHTML=["BOT DESK",...AG.map(a=>a[0])].map(n=>`<a class="nav" href="#" onclick="botP('${n}');return false">${miniNav(n)}<span>${n}<br><span class="m" style="opacity:.6;font-size:11px">${INFO[n].t}</span></span><span class="sd" id="sd-${n.replace(' ','_')}"></span></a>`).join("")}
function toggleSB(v){const c=v===undefined?!document.body.classList.contains("sbc"):!v;document.body.classList.toggle("sbc",c);localStorage.setItem("sbc",c?"1":"0")}
function proj(){openM(`<div class="doc"><h2>📘 El proyecto</h2><p>Mesa de trading de memecoins en Solana con 8 agentes especializados. Alberto fija el objetivo; BOT DESK (Jefe de Mesa) coordina; cada agente tiene un único rol. Este panel solo observa y pausa: <b>no tiene wallet, claves ni firma</b>.</p>
<h3>El funnel</h3><div class="fl2">${STAGES.map((s,i)=>`<span style="background:${SC[s]}">${s}</span>${i<4?"→":""}`).join("")}</div><p>SEARCH escanea → RISK aprueba → WHALE+SHILL confirman → SNIPER ejecuta (con APPROVE) → EXIT/RUG cierran.</p>
<h3>Protocolo de lead ID</h3><p><code>[L-AAAAMMDD-NNN] AGENTE → ETAPA | SÍMBOLO | CONTRATO COMPLETO | nota</code></p><p>ID único que nunca se reutiliza; el contrato siempre completo, nunca abreviado.</p>
<h3>Reglas de seguridad</h3><div class="rule">🔑 Nadie guarda ni pide claves privadas o frases semilla. Nunca.</div><div class="rule">✍️ Nada se firma sin el <b>APPROVE #id</b> literal de Alberto.</div><div class="rule">📉 Una pérdida diaria del 5% para la planta (HALT) automáticamente.</div>
<h3>Rutinas</h3><div class="rt2"><b>SEARCH</b><span>cada hora</span><b>RISK</b><span>cada 30 min</span><b>WHALE · SHILL</b><span>cada hora</span><b>EXIT · RUG</b><span>cada 15 min</span><b>BOT DESK</b><span>informe a las 21:00</span><b>SNIPER</b><span>solo con APPROVE</span></div>
<h3>Pausar y reanudar</h3><p>El estado vive en <code>state.json</code>. Antes de cada ejecución, cada agente lo lee y solo actúa si la planta está EN MARCHA y su estado es RUNNING. Desde aquí puedes pausar un bot (clic en él o en su ficha) o parar toda la planta (clic en el jefe → Parar todo). Los cambios en la web pública llegan al box en ≤30–60 s.</p></div>`)}
function botP(n){const a=(S.agents||{})[n]||{},I=INFO[n],p=a.status==="PAUSED",halt=S.floor!=="RUNNING";const ls=LD.filter(l=>l.owner===n||(l.history||[]).some(h=>h.by===n)).length,ac=ACT.filter(x=>x.agent===n).length;
 const c=(AGC[n]||AGC["BOT DESK"])[1];
 openM(`<div class="doc"><div class="bh"><span class="mini">${mini(n)}</span><div><h2 style="color:${c}">${n}</h2><div>${I.t}</div>
 <div class="row" style="margin-top:8px"><span class="bd" style="background:${p||halt?"#8b1e1e":"#1f6d3a"}">${p?"PAUSADO":halt?"PLANTA PARADA":"EN MARCHA"}</span><span class="m">${ls} leads · ${ac} actividades</span>
 ${n==="BOT DESK"?"":`<button class="btn ${p?"bgo":"bstop"}" onclick="agT('${n}',${p});closeM()">${p?"▶️ Reanudar":"⏸️ Parar"}</button>`}</div></div></div>
 <h3>👁 Qué observa</h3><p>${I.obs}</p><h3>⚙️ Cómo opera</h3><p>${I.how}</p><h3>⏱ Cadencia</h3><p>${I.cad}</p><h3>✅ Qué hace</h3><p>${I.does}</p><h3>⛔ Límites</h3><div class="rule">${I.lim}</div>
 ${n==="BOT DESK"?"":`<p><a href="#" style="color:#9fb0ff" onclick="ops('${n}');return false">Ver últimas operaciones →</a></p>`}</div>`)}
const _render=render;render=function(){_render();const halted=S.floor!=="RUNNING";
 document.getElementById("fn").innerHTML=STAGES.map(s=>`<span><i class="dotc" style="background:${SC[s]}"></i>${s}</span><b>${LD.filter(l=>l.stage===s).length}</b>`).join("");
 ["BOT DESK",...AG.map(a=>a[0])].forEach(n=>{const e=document.getElementById("sd-"+n.replace(" ","_"));if(e)e.style.background=((S.agents||{})[n]?.status==="RUNNING"&&!halted)?"#4ee08a":"#ff5b5b"})};
if(localStorage.getItem("sbc")==="1"||(localStorage.getItem("sbc")===null&&innerWidth<=800))document.body.classList.add("sbc");

build();buildNav();boot();setInterval(load,12000);
</script></body></html>
'''
def page_old():
    s,l,t=rd("state.json"),rd("leads.json"),rd("top10.json"); fl=s.get("floor","?")
    r=[f"<html><head><meta charset=utf-8><link rel=\"icon\" href=\"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🤖</text></svg>\"><link rel=\"apple-touch-icon\" href=\"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' fill='%231b1d2a'/><text y='.9em' x='5' font-size='80'>🤖</text></svg>\"><meta http-equiv=refresh content=15><title>Mesa</title><style>body{{font-family:sans-serif;background:#111;color:#eee;margin:20px}}table{{border-collapse:collapse;margin-bottom:20px}}td,th{{border:1px solid #444;padding:4px 8px}}.RUNNING{{color:#4c4}}.PAUSED,.HALTED{{color:#f55}}button{{padding:4px 10px}}code{{font-size:12px}}</style></head><body>",
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
