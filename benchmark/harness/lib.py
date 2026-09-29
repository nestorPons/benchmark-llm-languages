#!/usr/bin/env python3
"""Shared helpers for the benchmark harness.

Contains: config loading, LLM chat client (OpenAI-compatible), code extraction
from model output, cost calculation, and a small framework registry.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import requests

from count_tokens import count, count_dir

ROOT = Path(__file__).resolve().parent.parent


def load_env(path: str | Path | None = None) -> None:
    """Load KEY=VALUE pairs from a .env file into os.environ (no override).

    Searches, in order: explicit ``path``, project root ``.env``, ``benchmark/.env``.
    """
    candidates = [Path(path)] if path else [ROOT.parent / ".env", ROOT / ".env"]
    for c in candidates:
        if not c.exists():
            continue
        for line in c.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        break


def load_config(path: str | Path | None = None) -> dict:
    load_env()
    if path is None:
        env = os.environ.get("BENCH_CONFIG")
        path = env or ROOT / "config.json"
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


class ChatClient:
    """Minimal OpenAI-compatible chat completions client via requests."""

    def __init__(self, model_cfg: dict):
        self.name = model_cfg["name"]
        self.base_url = model_cfg.get("api_base", "https://api.openai.com/v1").rstrip("/")
        key_env = model_cfg.get("api_key_env", "OPENAI_API_KEY")
        self.api_key = os.environ.get(key_env, "")
        self.temperature = model_cfg.get("temperature", 0.0)
        self.max_tokens = model_cfg.get("max_tokens", 8192)
        self.timeout = model_cfg.get("timeout_s", 300)

    def chat(self, messages: list[dict], seed: int | None = None) -> dict:
        payload = {
            "model": self.name,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        if seed is not None:
            payload["seed"] = seed
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        last_exc = None
        for attempt in range(1, 4):
            try:
                r = requests.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=self.timeout,
                )
                r.raise_for_status()
                data = r.json()
                msg = data["choices"][0]["message"]
                return {
                    "content": msg.get("content") or "",
                    "usage": data.get("usage") or {},
                }
            except (requests.ConnectionError, requests.Timeout) as e:
                last_exc = e
                time.sleep(2 * attempt)
        raise last_exc


LANG_EXT = {
    "python": ".py", "typescript": ".ts", "javascript": ".js", "go": ".go",
    "rust": ".rs", "csharp": ".cs", "java": ".java", "php": ".php",
    "dart": ".dart", "swift": ".swift", "scala": ".scala", "groovy": ".groovy",
    "perl": ".pl", "raku": ".raku", "ruby": ".rb", "lua": ".lua",
    "elixir": ".ex", "clojure": ".clj", "julia": ".jl", "nim": ".nim",
    "crystal": ".cr", "kotlin": ".kt", "fsharp": ".fs", "ocaml": ".ml",
    "json": ".json", "yaml": ".yml", "sql": ".sql", "sh": ".sh",
    "html": ".html", "css": ".css", "toml": ".toml", "md": ".md",
}

_PATH_RE = re.compile(r"[\w./\\-]+\.\w+")


def _parse_fence_info(info: str) -> str | None:
    """Derive a file path from a fence info string, if any.

    Supports ``lang path/to/file.ext`` and ``filename=path/to/file.ext``.
    Returns None when no path is present (caller falls back to a generated name).
    """
    if not info:
        return None
    m = re.search(r"filename\s*=\s*(\S+)", info)
    if m:
        return m.group(1)
    toks = info.split()
    for t in toks:
        if t.startswith(("filename=", "path=")):
            continue
        if _PATH_RE.fullmatch(t) and "." in t:
            return t
    return None


def extract_files(content: str, fallback_lang: str = "") -> dict[str, str]:
    """Parse model output into {filepath: code}.

    Accepts fenced code blocks with a path in the fence info
    (e.g. ```python app/main.py) or ``### FILE: path`` markers.
    """
    files: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []
    in_fence = False

    for raw in content.splitlines():
        line = raw.rstrip("\n")
        if line.startswith("```"):
            if not in_fence:
                info = line[3:].strip()
                path = _parse_fence_info(info)
                lang = info.split()[0] if info else fallback_lang
                current = path or _default_name(lang, fallback_lang, files)
                buf = []
                in_fence = True
            else:
                if current:
                    files.setdefault(current, "\n".join(buf))
                current = None
                in_fence = False
            continue

        m = re.match(r"^###\s*FILE:\s*(.+)$", line)
        if m and not in_fence:
            if current and buf:
                files.setdefault(current, "\n".join(buf))
            current = m.group(1).strip()
            buf = []
            continue

        if current is not None:
            buf.append(line)

    if current and buf:
        files.setdefault(current, "\n".join(buf))
    return files


def _default_name(lang: str, fallback_lang: str, files: dict[str, str]) -> str:
    ext = LANG_EXT.get(lang) or LANG_EXT.get(fallback_lang, ".txt")
    name = f"main{ext}"
    i = 1
    while name in files:
        i += 1
        name = f"main{i}{ext}"
    return name


def write_files(files: dict[str, str], workdir: Path) -> list[str]:
    workdir.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for rel, code in files.items():
        rel = rel.replace("\\", "/").lstrip("/")
        dest = (workdir / rel).resolve()
        if not str(dest).startswith(str(workdir.resolve()) + os.sep) and dest != workdir.resolve():
            raise ValueError(f"Path escapes workdir: {rel}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(code, encoding="utf-8")
        written.append(rel)
    return written


def cost_usd(input_tokens: int, output_tokens: int, model_cfg: dict) -> float:
    in_price = model_cfg.get("input_price_per_1k", 0.0)
    out_price = model_cfg.get("output_price_per_1k", 0.0)
    return input_tokens / 1000.0 * in_price + output_tokens / 1000.0 * out_price


def project_tokens(path: str | Path, model: str) -> int:
    return count_dir(str(path), model)["tokens"]


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")
