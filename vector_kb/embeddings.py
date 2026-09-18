#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ollama embedding 接口：把文本转换为可用于检索的向量。"""

import json
import urllib.request

OLLAMA = "http://localhost:11434"
MODEL = "bge-m3:latest"
DIM = 1024


def l2norm(vec):
    """返回 L2 归一化后的向量。"""
    s = sum(x * x for x in vec) ** 0.5 or 1.0
    return [x / s for x in vec]


def embed(texts):
    """调用 Ollama：优先 /api/embed（批量），失败回退 /api/embeddings（单条）。"""
    body = json.dumps({"model": MODEL, "input": texts}).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA}/api/embed",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            data = json.loads(r.read().decode("utf-8"))
        return [l2norm(v) for v in data["embeddings"]]
    except Exception:
        out = []
        for text in texts:
            body = json.dumps({"model": MODEL, "prompt": text}).encode("utf-8")
            req = urllib.request.Request(
                f"{OLLAMA}/api/embeddings",
                data=body,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as r:
                data = json.loads(r.read().decode("utf-8"))
            out.append(l2norm(data["embedding"]))
        return out