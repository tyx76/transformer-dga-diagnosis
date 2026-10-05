#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""性能基准测试：测量启动、检索、生成、内存和各知识库加载阶段。

该脚本不修改检索、生成或校验逻辑，只通过计时包装器调用现有函数，
并把结果写入 docs/03_检索与排序/性能基准测试.md。
"""

from __future__ import annotations

import argparse
import ctypes
import functools
import gc
import importlib
import json
import os
import pickle
import sqlite3
import subprocess
import sys
import threading
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

OUTPUT_DEFAULT = PROJECT_ROOT / "docs" / "03_检索与排序" / "性能基准测试.md"
QUESTIONS = (
    "汽轮机振动",
    "锅炉过热器A侧二级减温水调节门内漏",
)
IMPORT_TARGETS = (
    ("retrieval", "vector_kb.retrieval"),
    ("bm25_retriever", "vector_kb.bm25_retriever"),
    ("hybrid_retriever", "vector_kb.hybrid_retriever"),
    ("intent_classifier", "vector_kb.intent_classifier"),
    ("intent_router", "vector_kb.intent_router"),
    ("retrieval_router", "vector_kb.retrieval_router"),
    ("query_expander", "vector_kb.query_expander"),
    ("rrf_fusion", "vector_kb.rrf_fusion"),
    ("generation", "vector_kb.generation"),
    ("citation_verifier", "vector_kb.citation_verifier"),
)
FIRST_STAGE_ORDER = (
    "意图分类",
    "意图路由",
    "向量检索",
    "查询扩展",
    "BM25检索",
    "RRF融合",
    "正文重排",
    "生成",
    "引用校验",
)

if sys.platform == "win32":
    class _PROCESS_MEMORY_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("cb", ctypes.c_ulong),
            ("PageFaultCount", ctypes.c_ulong),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        ]


def _child_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("KB_BACKEND", "plant_kb")
    env.setdefault("USE_ROUTER", "true")
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def _process_memory_bytes() -> int | None:
    """Return the process working set when available."""
    if sys.platform == "win32":
        try:
            counters = _PROCESS_MEMORY_COUNTERS()
            counters.cb = ctypes.sizeof(counters)
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            psapi = ctypes.WinDLL("psapi", use_last_error=True)
            kernel32.GetCurrentProcess.argtypes = []
            kernel32.GetCurrentProcess.restype = ctypes.c_void_p
            psapi.GetProcessMemoryInfo.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(_PROCESS_MEMORY_COUNTERS),
                ctypes.c_ulong,
            ]
            psapi.GetProcessMemoryInfo.restype = ctypes.c_bool
            handle = kernel32.GetCurrentProcess()
            ok = psapi.GetProcessMemoryInfo(
                handle,
                ctypes.byref(counters),
                counters.cb,
            )
            if ok and counters.WorkingSetSize:
                return int(counters.WorkingSetSize)
        except Exception:
            pass
    try:
        import resource  # type: ignore

        value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        return value if sys.platform == "darwin" else value * 1024
    except Exception:
        return None


def _mb(value: int | None) -> str:
    if value is None:
        return "N/A"
    return f"{value / (1024 * 1024):.2f} MB"


def _seconds(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value:.3f}s"


def _file_size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except OSError:
        return None


def measure_startup(timeout: float = 120.0) -> dict[str, Any]:
    """Measure a child main.py process until its interactive prompt is ready."""
    command = [sys.executable, str(PROJECT_ROOT / "main.py")]
    started = time.perf_counter()
    proc: subprocess.Popen[str] | None = None
    lines: list[str] = []
    ready = threading.Event()

    try:
        proc = subprocess.Popen(
            command,
            cwd=str(PROJECT_ROOT),
            env=_child_env(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )

        def read_output() -> None:
            assert proc is not None and proc.stdout is not None
            buffer: list[str] = []
            while True:
                char = proc.stdout.read(1)
                if not char:
                    break
                buffer.append(char)
                current = "".join(buffer)
                if "请输入问题" in current:
                    prompt = current.strip()
                    if prompt:
                        lines.append(prompt.replace("\r", "").replace("\n", " "))
                    ready.set()
                    break
                if char in ("\r", "\n"):
                    line = current.strip()
                    if line:
                        lines.append(line)
                    buffer.clear()

        threading.Thread(target=read_output, daemon=True).start()
        deadline = started + timeout
        while not ready.is_set() and time.perf_counter() < deadline:
            if proc.poll() is not None:
                break
            time.sleep(0.05)

        if ready.is_set():
            elapsed = time.perf_counter() - started
            if proc.stdin is not None:
                proc.stdin.write("exit\n")
                proc.stdin.flush()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
            return {
                "seconds": elapsed,
                "error": None,
                "output_tail": lines[-20:],
            }

        error = f"未在 {timeout:.0f}s 内检测到交互提示"
        if proc.poll() is not None:
            error = f"main.py 提前退出，returncode={proc.returncode}"
        return {"seconds": None, "error": error, "output_tail": lines[-20:]}
    except Exception as exc:
        return {
            "seconds": None,
            "error": f"{type(exc).__name__}: {exc}",
            "output_tail": lines[-20:],
        }
    finally:
        if proc is not None and proc.poll() is None:
            try:
                proc.kill()
            except Exception:
                pass


def measure_import(module_name: str, timeout: float = 180.0) -> dict[str, Any]:
    """Measure a cold import in an isolated child process."""
    code = (
        "import json, time; "
        "start=time.perf_counter(); "
        f"import {module_name}; "
        "print(json.dumps({'seconds': time.perf_counter()-start}))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(PROJECT_ROOT),
        env=_child_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if result.returncode != 0:
        return {
            "seconds": None,
            "error": (result.stderr or result.stdout or "").strip()[-800:],
        }
    for line in reversed((result.stdout or "").splitlines()):
        try:
            value = json.loads(line)
        except Exception:
            continue
        if isinstance(value, dict) and isinstance(value.get("seconds"), (int, float)):
            return {"seconds": float(value["seconds"]), "error": None}
    return {"seconds": None, "error": "import child produced no timing payload"}


class StageRecorder:
    def __init__(self) -> None:
        self.samples: dict[str, list[float]] = defaultdict(list)

    def clear(self) -> None:
        self.samples.clear()

    def record(self, stage: str, seconds: float) -> None:
        self.samples[stage].append(float(seconds))

    def measure(self, stage: str, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        started = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            self.record(stage, time.perf_counter() - started)

    def one(self, stage: str) -> float | None:
        values = self.samples.get(stage) or []
        return values[0] if values else None

    def first_values(self) -> dict[str, float | None]:
        return {stage: self.one(stage) for stage in FIRST_STAGE_ORDER}


def _install_stage_hooks(modules: dict[str, Any], recorder: StageRecorder):
    specs = (
        ("retrieval_router", "classify_intent", "意图分类"),
        ("retrieval_router", "route_intent", "意图路由"),
        ("hybrid_retriever", "retrieve", "向量检索"),
        ("hybrid_retriever", "expand_query", "查询扩展"),
        ("hybrid_retriever", "bm25_retrieve", "BM25检索"),
        ("hybrid_retriever", "rrf_fusion", "RRF融合"),
        ("hybrid_retriever", "prioritize_results", "正文重排"),
    )
    originals = []
    for module_key, attribute, stage in specs:
        module = modules[module_key]
        original = getattr(module, attribute)

        @functools.wraps(original)
        def wrapper(*args: Any, _original=original, _stage=stage, **kwargs: Any) -> Any:
            return recorder.measure(_stage, _original, *args, **kwargs)

        setattr(module, attribute, wrapper)
        originals.append((module, attribute, original))
    return originals


def _restore_stage_hooks(originals: list[tuple[Any, str, Any]]) -> None:
    for module, attribute, original in originals:
        setattr(module, attribute, original)


def run_query(
    question: str,
    modules: dict[str, Any],
    recorder: StageRecorder,
    skip_generation: bool,
) -> dict[str, Any]:
    recorder.clear()
    started = time.perf_counter()
    errors: list[str] = []
    result: dict[str, Any] = {}
    chunks: list[dict[str, Any]] = []

    try:
        result = modules["retrieval_router"].route_and_retrieve(
            question,
            top_k=5,
            shadow=True,
        )
        chunks = result.get("chunks") or []
    except Exception as exc:
        errors.append(f"检索失败：{type(exc).__name__}: {exc}")

    answer = ""
    if chunks and not skip_generation:
        try:
            answer = recorder.measure(
                "生成",
                modules["generation"].generate,
                question,
                chunks,
            )
        except Exception as exc:
            errors.append(f"生成失败：{type(exc).__name__}: {exc}")
    elif not chunks:
        recorder.record("生成", 0.0)
    else:
        recorder.record("生成", 0.0)
        errors.append("生成阶段已按参数跳过")

    verification: dict[str, Any] = {}
    try:
        if answer:
            verification = recorder.measure(
                "引用校验",
                modules["citation_verifier"].verify_citations,
                answer,
                chunks,
            )
        else:
            recorder.record("引用校验", 0.0)
    except Exception as exc:
        errors.append(f"引用校验失败：{type(exc).__name__}: {exc}")

    total = time.perf_counter() - started
    return {
        "question": question,
        "total": total,
        "stages": recorder.first_values(),
        "chunks": len(chunks),
        "answer_chars": len(str(answer or "")),
        "intent": result.get("intent") if isinstance(result, dict) else None,
        "route": result.get("route") if isinstance(result, dict) else None,
        "source": result.get("source") if isinstance(result, dict) else None,
        "errors": errors,
        "verification": verification,
    }


def measure_bm25_standalone(modules: dict[str, Any]) -> dict[str, Any]:
    bm25 = modules["bm25_retriever"]
    hybrid = modules["hybrid_retriever"]
    backend = hybrid._backend_name()
    config = hybrid._resolve_config(backend)
    index_path = Path(config["bm25_index"])
    corpus_path = Path(config["bm25_corpus"])

    if hasattr(bm25, "_INDEX_CACHE"):
        bm25._INDEX_CACHE = None
    gc.collect()

    payload: dict[str, Any] | None = None
    documents: list[dict[str, Any]] | None = None
    index: Any = None
    try:
        started = time.perf_counter()
        with index_path.open("rb") as stream:
            payload = pickle.load(stream)
        pickle_seconds = time.perf_counter() - started

        started = time.perf_counter()
        if isinstance(payload, dict) and payload.get("version") == bm25.PLANT_BM25_V2_VERSION:
            documents, index = bm25.load_plant_bm25_v2(payload, (corpus_path,))
        else:
            # Fallback for legacy payloads: this still measures initialization.
            documents = list(payload.get("documents") or [])
            if not documents:
                raise ValueError(f"未知或空的 BM25 payload: {type(payload).__name__}")
            index = payload.get("bm25")
        init_seconds = time.perf_counter() - started
        return {
            "pickle_seconds": pickle_seconds,
            "init_seconds": init_seconds,
            "version": payload.get("version") if isinstance(payload, dict) else None,
            "documents": len(documents or []),
            "index_path": index_path,
            "corpus_path": corpus_path,
            "error": None,
        }
    except Exception as exc:
        return {
            "pickle_seconds": None,
            "init_seconds": None,
            "version": payload.get("version") if isinstance(payload, dict) else None,
            "documents": len(documents or []),
            "index_path": index_path,
            "corpus_path": corpus_path,
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        del payload, documents, index
        gc.collect()


def measure_vector_standalone(modules: dict[str, Any]) -> dict[str, Any]:
    retrieval = modules["retrieval"]
    hybrid = modules["hybrid_retriever"]
    backend = hybrid._backend_name()
    config = hybrid._resolve_config(backend)
    db_path = Path(config["vector_db"])
    con: sqlite3.Connection | None = None
    records: list[dict[str, Any]] | None = None
    try:
        started = time.perf_counter()
        con = sqlite3.connect(str(db_path))
        con.row_factory = sqlite3.Row
        connect_seconds = time.perf_counter() - started

        started = time.perf_counter()
        schema = retrieval._detect_schema(con, db_path)
        schema_seconds = time.perf_counter() - started

        started = time.perf_counter()
        records = retrieval._load_vectors(con, schema)
        load_seconds = time.perf_counter() - started
        return {
            "connect_seconds": connect_seconds,
            "schema_seconds": schema_seconds,
            "load_seconds": load_seconds,
            "schema": schema,
            "records": len(records),
            "db_path": db_path,
            "error": None,
        }
    except Exception as exc:
        return {
            "connect_seconds": None,
            "schema_seconds": None,
            "load_seconds": None,
            "schema": None,
            "records": len(records or []),
            "db_path": db_path,
            "error": f"{type(exc).__name__}: {exc}",
        }
    finally:
        if con is not None:
            con.close()
        del records
        gc.collect()


def _markdown_table(headers: tuple[str, ...], rows: list[tuple[Any, ...]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def _stage_rows(stages: dict[str, float | None]) -> list[tuple[str, str]]:
    rows = []
    for stage in FIRST_STAGE_ORDER:
        rows.append((stage, _seconds(stages.get(stage))))
    return rows


def _component_times(
    startup: dict[str, Any],
    imports: dict[str, dict[str, Any]],
    first: dict[str, Any],
    second: dict[str, Any],
    bm25_test: dict[str, Any],
    vector_test: dict[str, Any],
) -> dict[str, float]:
    values: dict[str, float] = {}
    if startup.get("seconds") is not None:
        values["进程启动到可输入"] = float(startup["seconds"])
    for label, item in imports.items():
        if item.get("seconds") is not None:
            values[f"import {label}"] = float(item["seconds"])
    for stage in FIRST_STAGE_ORDER:
        value = first.get("stages", {}).get(stage)
        if value is not None:
            values[f"首次查询-{stage}"] = float(value)
    for stage in FIRST_STAGE_ORDER:
        value = second.get("stages", {}).get(stage)
        if value is not None and second.get("stages", {}).get(stage) != 0.0:
            values[f"第二次查询-{stage}"] = float(value)
    if bm25_test.get("pickle_seconds") is not None:
        values["BM25 pickle.load"] = float(bm25_test["pickle_seconds"])
    if bm25_test.get("init_seconds") is not None:
        values["BM25 初始化"] = float(bm25_test["init_seconds"])
    if vector_test.get("connect_seconds") is not None:
        values["向量库 connect"] = float(vector_test["connect_seconds"])
    if vector_test.get("load_seconds") is not None:
        values["向量库 load_vectors"] = float(vector_test["load_seconds"])
    return values


def build_plain_output(
    startup: dict[str, Any],
    imports: dict[str, dict[str, Any]],
    first: dict[str, Any],
    second: dict[str, Any],
    memory: dict[str, int | None],
    bm25_test: dict[str, Any],
    vector_test: dict[str, Any],
    top_three: list[tuple[str, float]],
    bottleneck: str,
) -> str:
    lines = [
        "=== 启动耗时 ===",
        f"总启动: {_seconds(startup.get('seconds'))}",
    ]
    for label, item in imports.items():
        suffix = f" ({item.get('error')})" if item.get("error") else ""
        lines.append(f"  - import {label}: {_seconds(item.get('seconds'))}{suffix}")

    lines += [
        "",
        f"=== 首次查询：{QUESTIONS[0]} ===",
    ]
    for stage, value in _stage_rows(first.get("stages") or {}):
        lines.append(f"{stage}: {value}")
    lines.append(f"总耗时: {_seconds(first.get('total'))}")
    if first.get("errors"):
        lines.append("异常: " + "；".join(first["errors"]))

    lines += [
        "",
        f"=== 第二次查询：{QUESTIONS[1]} ===",
    ]
    for stage, value in _stage_rows(second.get("stages") or {}):
        lines.append(f"{stage}: {value}")
    lines.append(f"总耗时: {_seconds(second.get('total'))}")
    if first.get("total") is not None and second.get("total") is not None:
        delta = float(first["total"]) - float(second["total"])
        direction = "快了" if delta >= 0 else "慢了"
        lines.append(f"（对比首次：{direction} {abs(delta):.3f}s）")
    if second.get("errors"):
        lines.append("异常: " + "；".join(second["errors"]))

    lines += [
        "",
        "=== 内存占用 ===",
        f"脚本进程启动后: {_mb(memory.get('baseline'))}",
        f"模块导入后: {_mb(memory.get('after_imports'))}",
        f"首次查询后: {_mb(memory.get('after_first'))}",
        f"第二次查询后: {_mb(memory.get('after_second'))}",
        "",
        "=== 单独测试 ===",
        f"BM25 pickle.load: {_seconds(bm25_test.get('pickle_seconds'))}",
        f"BM25 初始化: {_seconds(bm25_test.get('init_seconds'))}",
        f"向量库 connect: {_seconds(vector_test.get('connect_seconds'))}",
        f"向量库 schema 探测: {_seconds(vector_test.get('schema_seconds'))}",
        f"向量库 load_vectors: {_seconds(vector_test.get('load_seconds'))}",
        "",
        "=== 最大的三个耗时项 ===",
    ]
    for rank, (name, seconds) in enumerate(top_three, start=1):
        lines.append(f"{rank}. {name}: {_seconds(seconds)}")
    lines.append(f"性能基准测试完成，瓶颈在{bottleneck}")
    return "\n".join(lines)


def build_markdown(
    plain_output: str,
    startup: dict[str, Any],
    imports: dict[str, dict[str, Any]],
    first: dict[str, Any],
    second: dict[str, Any],
    memory: dict[str, int | None],
    bm25_test: dict[str, Any],
    vector_test: dict[str, Any],
    component_times: dict[str, float],
    top_three: list[tuple[str, float]],
    bottleneck: str,
) -> str:
    backend = os.getenv("KB_BACKEND", "plant_kb")
    files = [
        ("BM25 索引", Path(bm25_test.get("index_path") or "")),
        ("向量库", Path(vector_test.get("db_path") or "")),
        ("JSONL 语料", Path(bm25_test.get("corpus_path") or "")),
    ]
    file_rows = []
    for label, path in files:
        size = _file_size(path) if path else None
        file_rows.append((label, str(path), _mb(size)))

    import_rows = [
        (f"import {label}", _seconds(item.get("seconds")), item.get("error") or "")
        for label, item in imports.items()
    ]
    later_rows = [
        ("BM25 pickle.load", _seconds(bm25_test.get("pickle_seconds")), bm25_test.get("error") or ""),
        ("BM25 初始化", _seconds(bm25_test.get("init_seconds")), bm25_test.get("error") or ""),
        ("向量库 connect", _seconds(vector_test.get("connect_seconds")), vector_test.get("error") or ""),
        ("向量库 schema 探测", _seconds(vector_test.get("schema_seconds")), vector_test.get("error") or ""),
        ("向量库 load_vectors", _seconds(vector_test.get("load_seconds")), vector_test.get("error") or ""),
    ]
    bm25_cold = (bm25_test.get("pickle_seconds") or 0.0) + (bm25_test.get("init_seconds") or 0.0)
    vector_cold = (
        (vector_test.get("connect_seconds") or 0.0)
        + (vector_test.get("schema_seconds") or 0.0)
        + (vector_test.get("load_seconds") or 0.0)
    )
    first_generation = first.get("stages", {}).get("生成") or 0.0
    if "BM25" in bottleneck:
        bottleneck_analysis = (
            f"BM25 首次检索占主导；单独测得 pickle.load "
            f"{bm25_test.get('pickle_seconds', 0.0):.3f}s、初始化 "
            f"{bm25_test.get('init_seconds', 0.0):.3f}s，二者合计 {bm25_cold:.3f}s。"
            "第二次查询命中缓存后，BM25阶段明显下降。"
        )
    elif "向量库" in bottleneck:
        bottleneck_analysis = (
            f"向量库加载链路耗时较高，单独测得 connect + schema + load_vectors "
            f"合计 {vector_cold:.3f}s。"
        )
    elif "生成" in bottleneck:
        bottleneck_analysis = (
            f"生成阶段耗时 {first_generation:.3f}s，瓶颈主要来自外部 DeepSeek API "
            "网络和服务响应。"
        )
    else:
        bottleneck_analysis = (
            f"当前最大单项为 {bottleneck}，需要结合首次/第二次差异判断是否为冷加载或缓存问题。"
        )
    all_errors = []
    for item in (first, second):
        all_errors.extend(item.get("errors") or [])
    if bm25_test.get("error"):
        all_errors.append("BM25 单独测试：" + bm25_test["error"])
    if vector_test.get("error"):
        all_errors.append("向量库单独测试：" + vector_test["error"])

    lines = [
        "# 性能基准测试",
        "",
        f"> 测试日期：{time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"> 后端：`KB_BACKEND={backend}`，`USE_ROUTER={os.getenv('USE_ROUTER', 'true')}`",
        "> 本报告由 `scripts/profile_performance.py` 生成；测试只测量，不修改检索、生成或校验逻辑。",
        "",
        "## 1. 被测文件规模",
        "",
        _markdown_table(("文件", "路径", "大小"), file_rows),
        "",
        "## 2. 启动耗时",
        "",
        _markdown_table(("指标", "耗时", "异常"), [("进程启动到可输入", _seconds(startup.get("seconds")), startup.get("error") or "")]),
        "",
        "### 模块冷导入",
        "",
        _markdown_table(("模块", "耗时", "异常"), import_rows),
        "",
        "## 3. 首次查询",
        "",
        f"问题：`{QUESTIONS[0]}`",
        "",
        _markdown_table(("阶段", "耗时"), _stage_rows(first.get("stages") or {})),
        "",
        _markdown_table(
            ("指标", "结果"),
            [
                ("端到端总耗时", _seconds(first.get("total"))),
                ("命中 chunks", str(first.get("chunks"))),
                ("回答长度", str(first.get("answer_chars"))),
                ("意图", json.dumps(first.get("intent"), ensure_ascii=False)),
                ("检索入口", str(first.get("source"))),
            ],
        ),
        "",
        "## 4. 第二次查询",
        "",
        f"问题：`{QUESTIONS[1]}`",
        "",
        _markdown_table(("阶段", "耗时"), _stage_rows(second.get("stages") or {})),
        "",
        _markdown_table(
            ("指标", "结果"),
            [
                ("端到端总耗时", _seconds(second.get("total"))),
                ("首次与第二次差值", _seconds((first.get("total") or 0.0) - (second.get("total") or 0.0))),
                ("命中 chunks", str(second.get("chunks"))),
                ("回答长度", str(second.get("answer_chars"))),
                ("意图", json.dumps(second.get("intent"), ensure_ascii=False)),
                ("检索入口", str(second.get("source"))),
            ],
        ),
        "",
        "## 5. 内存占用",
        "",
        _markdown_table(
            ("时点", "Working Set"),
            [
                ("脚本进程启动后", _mb(memory.get("baseline"))),
                ("模块导入后", _mb(memory.get("after_imports"))),
                ("首次查询后", _mb(memory.get("after_first"))),
                ("第二次查询后", _mb(memory.get("after_second"))),
            ],
        ),
        "",
        "## 6. 单独加载测试",
        "",
        _markdown_table(("测试项", "耗时", "异常"), later_rows),
        "",
        "## 7. 耗时排行",
        "",
        _markdown_table(
            ("排名", "项目", "耗时"),
            [(index, name, _seconds(seconds)) for index, (name, seconds) in enumerate(top_three, start=1)],
        ),
        "",
        "## 8. 初步判断",
        "",
        f"当前完整测量中最大的单项为 **{bottleneck}**。",

        bottleneck_analysis,
        "",
        "判断规则：",
        "",
        "- 若 `BM25 初始化` 或 `BM25 pickle.load` 很高，瓶颈主要在 BM25 索引结构和文件加载。",
        "- 若 `向量库 load_vectors` 很高，瓶颈主要在 SQLite BLOB 反序列化和 Python 列表/向量对象构造。",
        "- 若 `生成` 很高，瓶颈主要在外部 DeepSeek API 网络和目标服务响应，不是本地索引。",
        "- 若首次查询明显高于第二次，说明首次冷加载/缓存未命中占主导。",
        "",
        "## 9. 原始输出",
        "",
        "```text",
        plain_output,
        "```",
    ]
    if all_errors:
        lines += [
            "",
            "## 10. 异常与说明",
            "",
        ]
        lines.extend(f"- {item}" for item in all_errors)
    return "\n".join(lines) + "\n"


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="测量项目启动、检索、生成和知识库加载性能")
    parser.add_argument("--output", default=str(OUTPUT_DEFAULT), help="Markdown 报告输出路径")
    parser.add_argument("--skip-generation", action="store_true", help="跳过 DeepSeek 生成，仅测量本地检索链路")
    parser.add_argument("--startup-timeout", type=float, default=120.0, help="启动探测超时秒数")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    os.environ.setdefault("KB_BACKEND", "plant_kb")
    os.environ.setdefault("USE_ROUTER", "true")

    memory: dict[str, int | None] = {"baseline": _process_memory_bytes()}

    startup = measure_startup(timeout=args.startup_timeout)
    imports = {label: measure_import(module_name) for label, module_name in IMPORT_TARGETS}

    modules: dict[str, Any] = {}
    for label, module_name in IMPORT_TARGETS:
        modules[label] = importlib.import_module(module_name)
    memory["after_imports"] = _process_memory_bytes()

    recorder = StageRecorder()
    hooks = _install_stage_hooks(modules, recorder)
    try:
        first = run_query(QUESTIONS[0], modules, recorder, args.skip_generation)
        memory["after_first"] = _process_memory_bytes()
        second = run_query(QUESTIONS[1], modules, recorder, args.skip_generation)
        memory["after_second"] = _process_memory_bytes()
    finally:
        _restore_stage_hooks(hooks)

    bm25_test = measure_bm25_standalone(modules)
    vector_test = measure_vector_standalone(modules)

    components = _component_times(startup, imports, first, second, bm25_test, vector_test)
    top_three = sorted(components.items(), key=lambda item: item[1], reverse=True)[:3]
    bottleneck = top_three[0][0] if top_three else "未知"

    plain_output = build_plain_output(
        startup,
        imports,
        first,
        second,
        memory,
        bm25_test,
        vector_test,
        top_three,
        bottleneck,
    )
    markdown = build_markdown(
        plain_output,
        startup,
        imports,
        first,
        second,
        memory,
        bm25_test,
        vector_test,
        components,
        top_three,
        bottleneck,
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(plain_output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())