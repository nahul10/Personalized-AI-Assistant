# backend/ingest_simple.py
r"""
CLI to ingest files into the vector store.

Usage (PowerShell):

    # Use forward slashes or quotes to avoid backslash-u issues on Windows
    python -m backend.ingest_simple "artifacts/uploads/Delhi tickets.pdf" --doc-id delhi

You can pass files or directories. Directories will be scanned for supported types.
"""

from pathlib import Path
import argparse
from .retriever import add_documents  # uses your existing ingestion pipeline


SUPPORTED_EXTS = {".pdf", ".txt", ".md", ".csv", ".docx"}


def collect_files(items):
    files = []
    for item in items:
        p = Path(item)
        if p.is_dir():
            for f in p.rglob("*"):
                if f.is_file() and f.suffix.lower() in SUPPORTED_EXTS:
                    files.append(str(f))
        elif p.is_file() and p.suffix.lower() in SUPPORTED_EXTS:
            files.append(str(p))
    return files


def main():
    ap = argparse.ArgumentParser(description="Ingest files into the vector store")
    ap.add_argument("paths", nargs="+", help="Files or directories to ingest")
    ap.add_argument("--doc-id", dest="doc_id", default=None, help="Optional logical doc id")
    args = ap.parse_args()

    files = collect_files(args.paths)
    if not files:
        print("No files found to ingest (supported: .pdf .txt .md .csv .docx).")
        return

    added = add_documents(files, doc_id=args.doc_id)
    print(f"Added {added} chunks from {len(files)} file(s).")


if __name__ == "__main__":
    main()
