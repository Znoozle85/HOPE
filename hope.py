"""HOPE Kern (Python) — Schritt 1: Ingest + Graph + IQ + Persistenz.

Python 3.10+, keine Fremd-Abhängigkeiten. Zustand liegt als JSON in
hope_state.json. Aufrufe:
    python3 hope.py               interaktiv (exit = Ende)
    python3 hope.py datei.txt     verarbeitet Textdatei(en), danach Pass + Anzeige
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

STATE_FILE = "hope_state.json"

ARTIKEL = re.compile(r"^(?:der|die|das|den|dem|des|ein|eine|einen|einem|eines)\s+", re.I)
DEF_RE = re.compile(r"^\s*(.+?)\s*(?:=|:=)\s*(.+?)\s*$")
FUNK_RE = re.compile(r"^\s*(.+?)\s+ist (?:eine?|ein) Funktion von\s+(.+?)\s*$", re.I)
ABH_RE = re.compile(r"^\s*(.+?)\s+hängt ab von\s+(.+?)\s*$", re.I)
FOLGT_RE = re.compile(r"^\s*(.+?)\s+(?:folgt (?:auf|aus)|kommt vor|steht vor)\s+(.+?)\s*$", re.I)


def lade(pfad=STATE_FILE):
    try:
        with open(pfad, encoding="utf-8") as f:
            s = json.load(f)
    except FileNotFoundError:
        s = {}
    s.setdefault("knoten", {})
    s.setdefault("kanten", [])
    s.setdefault("ereignisse", [])
    s.setdefault("passes", 0)
    return s


def speichere(s, pfad=STATE_FILE):
    with open(pfad, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    print(f"gespeichert -> {pfad}")


def norm(t):
    t = t.replace("\u00a8", "\u0308")
    return unicodedata.normalize("NFC", t)


def name_ok(n):
    if not isinstance(n, str):
        return None
    n = re.sub(r"\(.*?\)", "", n)
    n = ARTIKEL.sub("", n)
    n = norm(n).strip().strip(".,:;")
    if not n or len(n) < 2 or n.isdigit():
        return None
    if not re.match(r"[A-Za-zÄÖÜäöüß0-9]", n[0]):
        return None
    return n


def knoten(s, name, definition=None):
    n = name_ok(name)
    if not n:
        return None
    if n in s["knoten"]:
        if definition and not s["knoten"][n].get("def"):
            s["knoten"][n]["def"] = definition
        return n
    s["knoten"][n] = {"def": definition}
    return n


def kante(s, a, b, typ):
    a, b = name_ok(a), name_ok(b)
    if not a or not b or a == b:
        return
    k = {"a": a, "b": b, "t": typ}
    if k not in s["kanten"]:
        s["kanten"].append(k)


def ingest(s, text, quelle="eingabe"):
    text = norm(text)
    folge = []
    for zeile in text.splitlines():
        zeile = zeile.strip()
        if not zeile:
            continue
        m = DEF_RE.match(zeile)
        if m:
            a = name_ok(m.group(1))
            if a:
                knoten(s, a, definition=m.group(2).strip()[:300])
            continue
        m = FUNK_RE.match(zeile)
        if m:
            a, b = name_ok(m.group(1)), name_ok(m.group(2))
            if a and b:
                knoten(s, a)
                knoten(s, b)
                kante(s, a, b, "txt")
            continue
        m = ABH_RE.match(zeile)
        if m:
            a = name_ok(m.group(1))
            if a:
                knoten(s, a)
                for b in re.split(r",| und ", m.group(2)):
                    if bn := name_ok(b):
                        knoten(s, bn)
                        kante(s, a, bn, "txt")
            continue
        m = FOLGT_RE.match(zeile)
        if m:
            a, b = name_ok(m.group(1)), name_ok(m.group(2))
            if a and b:
                knoten(s, a)
                knoten(s, b)
                kante(s, a, b, "folgt")
            continue
        if zeile.endswith(":") and len(zeile) < 120:
            a = name_ok(zeile[:-1])
            if a:
                knoten(s, a)
                if folge and folge[-1] != a:
                    kante(s, folge[-1], a, "folgt")
                folge.append(a)


def passe(s):
    s["passes"] += 1
    for name in list(s["knoten"]):
        g = norm(name).strip().strip(".,:;")
        if g != name and g in s["knoten"]:
            for k in s["kanten"]:
                if k["a"] == name:
                    k["a"] = g
                if k["b"] == name:
                    k["b"] = g
            del s["knoten"][name]
            s["ereignisse"].append({"art": "dedup", "von": name, "zu": g})
    s["kanten"] = [k for k in s["kanten"] if k["a"] != k["b"]]
    s["kanten"] = sorted({json.dumps(k, ensure_ascii=False) for k in s["kanten"]})
    s["kanten"] = [json.loads(x) for x in s["kanten"]]


def _folgt_kanten(s):
    return [(k["a"], k["b"]) for k in s["kanten"] if k["t"] == "folgt"]


def _komponenten(kanten):
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for a, b in kanten:
        union(a, b)
    gr = {}
    for x in parent:
        gr[find(x)] = gr.get(find(x), 0) + 1
    return sum(1 for n in gr.values() if n >= 2)


def _zyklen(kanten):
    g = {}
    for a, b in kanten:
        g.setdefault(a, set()).add(b)
    z = 0
    seen = set()

    def dfs(u, stack):
        nonlocal z
        if u in stack:
            z += 1
            return
        if u in seen:
            return
        seen.add(u)
        stack.add(u)
        for v in g.get(u, ()):
            dfs(v, stack)
        stack.discard(u)

    for u in g:
        dfs(u, set())
    return z


def metrik(s):
    n = len(s["knoten"])
    e = len(s["kanten"])
    fl = _folgt_kanten(s)
    ch = _komponenten(fl)
    zyk = _zyklen(fl)
    belegt = set()
    for k in s["kanten"]:
        belegt.add(k["a"])
        belegt.add(k["b"])
    off = sum(1 for name in s["knoten"] if name not in belegt)
    iq = 100 * (1 + n / 250) * (1 + e / 400) * (1 + ch / 30) * (1 + zyk / 25) * (1 + off / 80) / (1 + off / 60)
    return {"n": n, "e": e, "ch": ch, "zyk": zyk, "off": off, "iq": round(iq, 1)}


def zeige(s):
    m = metrik(s)
    print(
        f"Knoten {m['n']} | Kanten {m['e']} | Ketten {m['ch']} | "
        f"Zyklen {m['zyk']} | Unruhe {m['off']} | IQ {m['iq']} | Pässe {s['passes']}"
    )


def main(argv):
    s = lade()
    if argv:
        for p in argv:
            t = Path(p).read_text(encoding="utf-8")
            ingest(s, t, quelle=p)
            s["ereignisse"].append({"art": "ingest", "quelle": p})
    else:
        print("HOPE Kern — Schritt 1. 'exit' beendet.")
        while True:
            z = input("> ")
            if z.strip().lower() in ("exit", "quit", "ende"):
                break
            ingest(s, z, quelle="eingabe")
            s["ereignisse"].append({"art": "ingest", "quelle": "eingabe"})
            zeige(s)
    passe(s)
    zeige(s)
    speichere(s)


if __name__ == "__main__":
    main(sys.argv[1:])
