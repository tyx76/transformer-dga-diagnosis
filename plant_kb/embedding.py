"""Ollama embedding client used by the plant knowledge backend."""
import json
import urllib.request


def embed_texts(texts, model="bge-m3:latest", ollama_url="http://localhost:11434", batch_size=2):
    if not texts:
        return []
    vectors = []
    for start in range(0, len(texts), batch_size):
        vectors.extend(_embed_batch(texts[start:start + batch_size], model, ollama_url))
    return vectors


def _embed_batch(batch, model, ollama_url):
    try:
        req = urllib.request.Request(
            f"{ollama_url}/api/embed",
            data=json.dumps({"model": model, "input": batch}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return [_normalize(v) for v in payload["embeddings"]]
    except Exception:
        if len(batch) <= 1:
            raise
        middle = len(batch) // 2
        return _embed_batch(batch[:middle], model, ollama_url) + _embed_batch(batch[middle:], model, ollama_url)


def _normalize(vector):
    norm = sum(x * x for x in vector) ** 0.5 or 1.0
    return [float(x) / norm for x in vector]