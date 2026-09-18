#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shadow/gray retrieval rollout policy for main.ask()."""

from __future__ import annotations

import hashlib
import logging
import os
import threading
import time

from vector_kb.hybrid_retriever import hybrid_retrieve
from vector_kb.retrieval_router import route_and_retrieve

LOGGER = logging.getLogger(__name__)


def _mode() -> str:
    return os.getenv("RETRIEVAL_MODE", "shadow").strip().lower()


def _gray_rate() -> float:
    try:
        value = float(os.getenv("RETRIEVAL_GRAY_RATE", "0.1"))
    except (TypeError, ValueError):
        value = 0.1
    return max(0.0, min(1.0, value))


def _selected_for_gray(question: str) -> bool:
    digest = hashlib.sha256(question.encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) % 10_000
    return bucket < int(_gray_rate() * 10_000)


def _log_shadow(question: str, a_results: list[dict], started: float) -> None:
    try:
        bundle = route_and_retrieve(question, top_k=5, shadow=True)
        LOGGER.info(
            "retrieval shadow: question=%s intent=%s source=%s a=%s b=%s kb=%s elapsed_ms=%.2f",
            question,
            bundle.get("intent", {}).get("intent"),
            bundle.get("source"),
            [item.get("clause") for item in a_results],
            [item.get("clause") for item in bundle.get("chunks", [])],
            [item.get("clause") for item in bundle.get("kb_top5", [])],
            (time.perf_counter() - started) * 1000,
        )
    except Exception as exc:
        LOGGER.warning("retrieval shadow failed: %s", exc)


def retrieve_for_main(question: str, top_k: int = 5, trace=None) -> list[dict]:
    """Return production retrieval results according to rollout configuration.

    RETRIEVAL_MODE:
    - ``hybrid``: A path only.
    - ``shadow``: A path is returned; B path runs in a background thread.
    - ``gray``: deterministic question-hash rollout to B, with A fallback.
    - ``kb``: B path only, with A fallback.
    """
    mode = _mode()
    started = time.perf_counter()

    if mode == "kb":
        try:
            return route_and_retrieve(question, top_k=top_k, shadow=False, trace=trace)["chunks"]
        except Exception as exc:
            LOGGER.warning("kb mode failed, falling back to hybrid: %s", exc)
            return hybrid_retrieve(question, top_k=top_k, trace=trace)

    if mode == "gray" and _selected_for_gray(question):
        try:
            return route_and_retrieve(question, top_k=top_k, shadow=False, trace=trace)["chunks"]
        except Exception as exc:
            LOGGER.warning("gray kb path failed, falling back to hybrid: %s", exc)
            return hybrid_retrieve(question, top_k=top_k, trace=trace)

    results = hybrid_retrieve(question, top_k=top_k, trace=trace)

    if mode == "shadow":
        threading.Thread(
            target=_log_shadow,
            args=(question, results, started),
            daemon=True,
            name="retrieval-shadow",
        ).start()

    return results


__all__ = ["retrieve_for_main"]