"""Ollama embedding client used by the pure knowledge backend."""
import json
import urllib.request


def embed_texts(texts, model="bge-m3:latest", ollama_url="http://localhost:11434", batch_size=32):
    if not texts:
        return []
    vectors = []
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        req = urllib.request.Request(
            f"{ollama_url}/api/embed",
            data=json.dumps({"model": model, "input": batch}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
        vectors.extend(_normalize(v) for v in payload["embeddings"])
    return vectors


def _normalize(vector):
    norm = sum(x * x for x in vector) ** 0.5 or 1.0
    return [float(x) / norm for x in vector]