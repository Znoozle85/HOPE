"""HOPE Tafel (Python) — Schritt 3: lokale Web-Oberfläche zum Kern.

Nur Standardbibliothek (http.server). Nutzt die Funktionen aus hope.py.
Aufruf:
    python3 hope_ui.py              Tafel auf http://127.0.0.1:8033
    python3 hope_ui.py 8123         anderer Port

Die Seite zeigt IQ + Zerlegung, nimmt Text entgegen (Einspeisen), führt
einen Pass aus, speichert und zeichnet den Graph (SVG, Unruhe orange).
"""

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from hope import lade, ingest, passe, metrik

STATE_FILE = "hope_state.json"
STATE = lade()

PAGE = """<!doctype html><html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HOPE — Tafel</title>
<style>
 body{margin:0;font-family:system-ui,sans-serif;background:#10141c;color:#dfe6ee}
 .wrap{max-width:900px;margin:0 auto;padding:14px}
 h1{font-size:1.1rem;margin:0 0 4px}
 .sub{color:#8b98a9;font-size:.8rem;margin-bottom:10px}
 .stats{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
 .st{background:#1a2230;border:1px solid #2c3a4f;border-radius:6px;padding:6px 10px;font-size:.85rem}
 .st b{display:block;font-size:1.1rem;color:#7fd0a0}
 textarea{width:100%;box-sizing:border-box;height:90px;background:#0d1117;color:#dfe6ee;border:1px solid #2c3a4f;border-radius:6px;padding:8px;font-family:ui-monospace,monospace;font-size:.85rem}
 .btn{background:#1f6f4a;color:#fff;border:0;border-radius:6px;padding:8px 14px;font-size:.9rem;margin:6px 6px 0 0;cursor:pointer}
 .btn.sec{background:#2c3a4f}
 #svgCtn{background:#0d1117;border:1px solid #2c3a4f;border-radius:8px;margin-top:10px;min-height:340px;overflow:auto}
 svg{display:block;margin:auto}
 .unb{color:#e8b054}
</style></head><body><div class="wrap">
<h1>HOPE — Tafel</h1><div class="sub">Apache-2.0 · Kern + Oberfläche · lokal</div>
<div class="stats" id="stats"></div>
<textarea id="txt" placeholder="Text einspeisen: Definitionen (X = ...), Beziehungen (X hängt ab von ..., X folgt auf ...), Überschriften mit Doppelpunkt ..."></textarea><br>
<button class="btn" onclick="act('ingest')">Einspeisen</button>
<button class="btn sec" onclick="act('pass')">Pass</button>
<button class="btn sec" onclick="act('save')">Speichern</button>
<span id="status" style="margin-left:8px;font-size:.8rem;color:#8b98a9"></span>
<div id="svgCtn"><svg id="g"></svg></div>
<div class="sub" style="margin-top:8px" id="unb"></div>
</div>
<script>
async function act(a){
 let body={act:a};
 if(a==='ingest') body.text=document.getElementById('txt').value;
 let r=await fetch('/api',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
 let d=await r.json(); draw(d); document.getElementById('status').textContent='ok';
}
function draw(d){
 let m=d.m; document.getElementById('stats').innerHTML=
  ['n|Knoten','e|Kanten','ch|Ketten','zyk|Zyklen','off|Unruhe','iq|IQ','p|Pässe']
  .map(k=>{let p=k.split('|');return '<div class="st"><b>'+m[p[0]]+'</b>'+p[1]+'</div>'}).join('');
 let nodes=d.nodes, edges=d.edges;
 let svg=document.getElementById('g'); svg.setAttribute('width',700); svg.setAttribute('height',460);
 let W=640,H=400,cx=W/2+30,cy=H/2+20,R=Math.max(70,Math.min(180,nodes.length*28));
 let pos={};
 nodes.forEach(function(n,i){let a=i/nodes.length*2*Math.PI;pos[n]={x:cx+Math.cos(a)*R,y:cy+Math.sin(a)*R}});
 let s='';
 edges.forEach(function(e){let p1=pos[e.a],p2=pos[e.b];if(!p1||!p2)return;
  s+='<line x1="'+p1.x+'" y1="'+p1.y+'" x2="'+p2.x+'" y2="'+p2.y+'" stroke="'+(e.t==='folgt'?'#6ab0e8':'#8a7fb0')+'" stroke-width="1"/>';});
 nodes.forEach(function(n){let p=pos[n],unb=d.unb.indexOf(n)>=0;
  s+='<circle cx="'+p.x+'" cy="'+p.y+'" r="9" fill="'+(unb?'#e8b054':'#1f6f4a')+'" stroke="#dfe6ee" stroke-width="1"/>';
  s+='<text x="'+(p.x+13)+'" y="'+(p.y+4)+'" font-size="11" fill="#dfe6ee">'+n+'</text>';});
 svg.innerHTML=s;
 document.getElementById('unb').textContent = d.unb.length? 'Unruhe / ungebunden: '+d.unb.join(' · '):'';
}
act('pass'); setInterval(function(){act('pass')},60000);
</script></body></html>"""


def _quiet_save():
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(STATE, f, ensure_ascii=False, indent=1)


def antwort():
    m = metrik(STATE)
    m["p"] = STATE["passes"]
    unb = [n for n in STATE["knoten"]
           if not any(k["a"] == n or k["b"] == n for k in STATE["kanten"])]
    return {
        "m": m,
        "nodes": sorted(STATE["knoten"]),
        "edges": [{"a": k["a"], "b": k["b"], "t": k["t"]} for k in STATE["kanten"]],
        "unb": unb,
    }


class H(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, code, ctype, payload):
        data = payload.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        self._send(200, "text/html; charset=utf-8", PAGE)

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n) or b"{}")
            act = body.get("act", "")
            if act == "ingest":
                ingest(STATE, body.get("text", ""))
                STATE["ereignisse"].append({"art": "ingest", "quelle": "tafel"})
                _quiet_save()
            elif act == "pass":
                passe(STATE)
                _quiet_save()
            elif act == "save":
                _quiet_save()
            out = json.dumps(antwort(), ensure_ascii=False)
            self._send(200, "application/json; charset=utf-8", out)
        except Exception as exc:
            out = json.dumps({"fehler": str(exc)}, ensure_ascii=False)
            self._send(500, "application/json; charset=utf-8", out)


def main():
    global STATE
    port = 8033
    if sys.argv[1:]:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    STATE = lade()
    print(f"HOPE-Tafel läuft auf http://127.0.0.1:{port}  (Strg+C beendet)")
    HTTPServer(("127.0.0.1", port), H).serve_forever()


if __name__ == "__main__":
    main()
