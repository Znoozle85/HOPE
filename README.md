# HOPE

Mobile learning companion. Two local models, one balance.

- **SmolLM3-3B** *(fast player)* — ingest, segmentation, pattern/marker detection, notes.
- **Apriel-1.5-15b-Thinker** *(rare compiler)* — meaning, open questions, derivations; on demand only.
- Optional cloud assistant for post-processing; never the controller.

The graph stays human-auditable; automation supplements, never replaces.

## Core (hope.py)

Python 3.10+, no dependencies. Step 1: ingest (definitions, relationships,
headings → nodes + follow-edges), normalization (Umlauts), a merge pass,
structural IQ metric, JSON persistence (`hope_state.json`).

```
python3 hope.py               interactive
python3 hope.py file.txt      ingest a text file, then one pass + report
```

## Tafel (hope_ui.py)

Local web surface for the core. Stdlib only (`http.server`), no dependencies.

```
python3 hope_ui.py            board on http://127.0.0.1:8033
python3 hope_ui.py 8123       custom port
```

Shows IQ + breakdown (nodes/edges/chains/cycles/unrest), ingests text,
runs passes, saves, and draws the graph as SVG (unbound nodes orange),
with an auto-pass every 60 s.

## Roadmap (concept, CONCEPT.md)
Step 2: acronym / named-term detection, autonomous pass (frontier bridges,
transitive deduction, cycles → open questions).

## License
Apache-2.0 — see LICENSE.
