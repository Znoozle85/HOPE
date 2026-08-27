import math

def text_entropy(text: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not text:
        return 0.0
    freq = {}
    for char in text:
        freq[char] = freq.get(char, 0) + 1
    entropy = 0.0
    for count in freq.values():
        p = count / len(text)
        entropy -= p * math.log2(p)
    return entropy

def metrik(s):
    # Calculate graph metrics from structure s
    definitions = [node.get("def", "") for node in s["knoten"].values()]
    entropies = [text_entropy(defn) for defn in definitions if defn]
    avg_entropy = sum(entropies) / len(entropies) if entropies else 0.0
    return {
        "n": len(s.get("knoten", {})),  # nodes
        "e": len(s.get("kanten", [])),  # edges
        "ch": len(s.get("chains", [])),  # chains
        "zyk": len(s.get("cycles", [])),  # cycles
        "off": s.get("offset", 0),  # unrest/offset
        "iq": s.get("iq", 0),  # IQ score
        "entropy": round(avg_entropy, 2)
    }

def zeige(s):
    """Display formatted metrics."""
    m = metrik(s)
    print(
        f"Knoten {m['n']} | Kanten {m['e']} | Ketten {m['ch']} | "
        f"Zyklen {m['zyk']} | Unruhe {m['off']} | IQ {m['iq']} | "
        f"Entropie {m['entropy']} | Pässe {s.get('passes', 0)}"
    )
