"""Smoke tests for the pure knowledge backend.

Requires knowledge.db and Ollama bge-m3 for vector searches.
"""
from .api import exact_lookup, list_domains, search, stats


def main():
    domains = list_domains()
    for required in ("dga", "oil_temp", "safety", "equipment", "dp", "cases"):
        assert required in domains, f"missing domain: {required}"

    dga = search("乙炔超标", domains=["dga"], top_k=5)
    assert dga and all(item["domain"] == "dga" for item in dga)

    oil = search("油温过高 冷却 负载", domains=["oil_temp"], top_k=5)
    assert oil and all(item["domain"] == "oil_temp" for item in oil)

    safety = search("立即停运 安全操作", domains=["safety"], top_k=5)
    assert safety and all(item["domain"] == "safety" for item in safety)

    filtered = search(
        "注意值", domains=["dga"], filters={"doc_id": "DL/T 722-2014"}, top_k=5
    )
    assert filtered and all(item["doc_id"] == "DL/T 722-2014" for item in filtered)

    exact = exact_lookup(
        {"doc_id": "DL/T 722-2014", "clause": "9.3.1"}, domains=["dga"]
    )
    assert exact and "9.3.1" in exact[0]["id"], exact[:1]

    # search remains vector-only and must not silently switch to exact lookup.
    vector_only = search("DL/T 722 第9.3.1条", domains=["dga"], top_k=5)
    assert vector_only and all(item["retrieval_method"] == "vector" for item in vector_only)

    report = stats()
    assert report["bad_vectors"] == 0
    print("SMOKE_OK", report)


if __name__ == "__main__":
    main()