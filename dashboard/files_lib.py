# Recolecta archivos permitidos para sync (misma allowlist que server.py)
import os,re,sys,datetime
def _lib():
    src=open(os.path.join(os.path.dirname(__file__),"server.py")).read()
    a=src.index("# ---- Archivos"); b=src.index("e=html.escape",a)
    g={"os":os,"datetime":datetime,"MEM":False,"STORE":{}}; exec(src[a:b],g); return g
def collect():
    g=_lib(); out={}
    for x in g["f_list_disk"]():
        y=g["f_get"](x["path"])
        if y: out[x["path"]]=y
    return out
