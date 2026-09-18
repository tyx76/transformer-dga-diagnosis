#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQLite 向量库存储层：负责连接数据库和初始化表结构。"""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_DEFAULT = ROOT / "knowledge.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    filename TEXT NOT NULL,
    sha256 TEXT NOT NULL UNIQUE,
    content_type TEXT,
    size_bytes INTEGER NOT NULL DEFAULT 0,
    char_count INTEGER NOT NULL DEFAULT 0,
    chunk_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'ready',
    collection TEXT NOT NULL DEFAULT 'reference',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    meta TEXT NOT NULL DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    text TEXT NOT NULL,
    char_start INTEGER,
    char_end INTEGER,
    vector BLOB NOT NULL,
    dim INTEGER NOT NULL,
    meta TEXT NOT NULL DEFAULT '{}',
    UNIQUE(document_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_documents_collection ON documents(collection);
CREATE INDEX IF NOT EXISTS idx_documents_sha ON documents(sha256);
"""


def connect(db_path):
    """连接 SQLite，并确保表结构已经创建。"""
    con = sqlite3.connect(str(db_path))
    con.executescript(SCHEMA)
    con.commit()
    return con