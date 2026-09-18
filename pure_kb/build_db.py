"""Rebuild pure_kb/knowledge.db from the submitted JSONL."""
import argparse
from pathlib import Path

from .store import build_database

ROOT = Path(__file__).resolve().parent


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build the pure knowledge database")
    parser.add_argument("--jsonl", default=str(ROOT / "data" / "knowledge.jsonl"))
    parser.add_argument("--db", default=str(ROOT / "knowledge.db"))
    parser.add_argument("--model", default="bge-m3:latest")
    parser.add_argument("--ollama-url", default="http://localhost:11434")
    args = parser.parse_args(argv)
    result = build_database(args.jsonl, args.db, model=args.model, ollama_url=args.ollama_url)
    print(result)


if __name__ == "__main__":
    main()