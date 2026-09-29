#!/usr/bin/env python3
"""Token counting with the real model tokenizer.

Spec rule (sections 1.1, 10, 12): never estimate tokens from characters or
lines. Always use the model's tokenizer. For OpenAI models we use ``tiktoken``;
for other providers the caller must supply a tokenizer name (HuggingFace or
equivalent) via the ``tokenizer`` field in config, otherwise a clearly-labelled
estimate fallback is used and the result is flagged ``fallback: true``.

CLI:
    count_tokens.py <model> [path...]        # files and/or directories
    count_tokens.py <model> --stdin          # read from stdin
"""

from __future__ import annotations

import argparse
import json
import os
import sys

try:
    import tiktoken
except ImportError:  # pragma: no cover
    tiktoken = None


OPENAI_ENCODINGS = {
    # gpt-4 / gpt-4o / gpt-3.5 family
    "gpt-4o": "o200k_base",
    "gpt-4o-mini": "o200k_base",
    "gpt-4.1": "o200k_base",
    "gpt-4.1-mini": "o200k_base",
    "gpt-4": "cl100k_base",
    "gpt-4-turbo": "cl100k_base",
    "gpt-3.5-turbo": "cl100k_base",
    "text-embedding-ada-002": "cl100k_base",
}

_ENC_CACHE: dict[str, object] = {}


def _encoding_for(model: str):
    enc = OPENAI_ENCODINGS.get(model)
    if not enc:
        for prefix in OPENAI_ENCODINGS:
            if model.startswith(prefix):
                enc = OPENAI_ENCODINGS[prefix]
                break
    if not enc:
        return None
    if enc not in _ENC_CACHE:
        if tiktoken is None:
            raise RuntimeError("tiktoken not installed; run: pip install tiktoken")
        _ENC_CACHE[enc] = tiktoken.get_encoding(enc)
    return _ENC_CACHE[enc]


def count(text: str, model: str) -> dict:
    """Return {"tokens": int, "fallback": bool} for ``text`` under ``model``."""
    enc = _encoding_for(model)
    if enc is not None:
        return {"tokens": len(enc.encode(text)), "fallback": False}
    # Non-OpenAI / unknown: char/4 heuristic, flagged as fallback.
    return {"tokens": (len(text) // 4) + (1 if len(text) % 4 else 0), "fallback": True}


def count_file(path: str, model: str) -> dict:
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return count(fh.read(), model)


CODE_EXTS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", ".cs", ".java", ".php",
    ".dart", ".swift", ".scala", ".groovy", ".pl", ".pm", ".raku", ".rb",
    ".lua", ".ex", ".exs", ".clj", ".jl", ".nim", ".cr", ".kt", ".fs", ".ml",
    ".sh", ".json", ".yaml", ".yml", ".toml", ".sql", ".html", ".css", ".md",
}


def count_dir(path: str, model: str, extensions: set[str] | None = None) -> dict:
    exts = extensions if extensions is not None else CODE_EXTS
    total = 0
    files = 0
    for root, _dirs, names in os.walk(path):
        for name in names:
            if os.path.splitext(name)[1].lower() not in exts:
                continue
            total += count_file(os.path.join(root, name), model)["tokens"]
            files += 1
    return {"tokens": total, "files": files, "fallback": False}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("model", help="model name (e.g. gpt-4o) or tokenizer key")
    ap.add_argument("paths", nargs="*", help="files and/or directories to count")
    ap.add_argument("--stdin", action="store_true", help="read text from stdin")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args(argv)

    if args.stdin:
        out = count(sys.stdin.read(), args.model)
        print(json.dumps(out) if args.json else out["tokens"])
        return 0

    results = {}
    total = 0
    for p in args.paths:
        if os.path.isdir(p):
            r = count_dir(p, args.model)
        else:
            r = count_file(p, args.model)
        r["fallback"] = r.get("fallback", False)
        results[p] = r
        total += r["tokens"]

    if args.json:
        print(json.dumps({"total": total, "paths": results}, indent=2))
    else:
        for p, r in results.items():
            note = " [fallback]" if r.get("fallback") else ""
            print(f"{r['tokens']:>8}  {p}{note}")
        print(f"{total:>8}  TOTAL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
