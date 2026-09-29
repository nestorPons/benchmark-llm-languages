#!/usr/bin/env python3
"""Benchmark harness: LLM-assisted development loop.

For each (model, task, language, repetition) it:
  1. renders the neutral task prompt,
  2. calls the model and extracts the generated files,
  3. runs the external HTTP acceptance tests,
  4. feeds errors back for correction until green or max_iterations,
  5. counts tokens/cost and writes a result JSON.

Usage:
    run_llm.py [--config config.json] [--model NAME] [--task T1-rest-crud]
               [--language python] [--reps N] [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from lib import (
    ChatClient,
    ROOT,
    cost_usd,
    extract_files,
    load_config,
    now_iso,
    project_tokens,
    write_files,
)
from count_tokens import count
from orchestrate import needs_service, start_service, stop_service

HARNESS = ROOT / "harness"
LANGUAGES = ROOT / "languages"
TASKS = ROOT / "tasks"
RESULTS = ROOT / "results" / "raw"

DEFAULT_SYSTEM = (
    "You are an expert software developer. Produce complete, idiomatic, runnable "
    "code for the task in the specified language and framework. Output every file "
    "as a fenced code block with the file path in the fence info, for example:\n"
    "```python app/main.py\n<code>\n```\n"
    "Also produce a run.sh (bash) entrypoint. For an HTTP service, run.sh start "
    "must set up a self-contained environment first (for example: Python -> "
    "create a venv and pip install -r requirements.txt; Node.js -> npm install; "
    "Go -> go mod tidy then go build), then start the service in the background "
    "on port 8005, write its PID to server.pid, and return 0; run.sh stop must "
    "stop that process and remove server.pid. Do not assume packages are "
    "pre-installed. For a CLI program, run.sh must forward its subcommands "
    "(e.g. init/add/list) to the program. A README.md is optional. "
    "Do not add commentary outside code blocks."
)


def render_prompt(template: str, lang: str, framework: str, runtime: str) -> str:
    return (
        template
        .replace("{language}", lang)
        .replace("{framework}", framework)
        .replace("{runtime}", runtime)
    )


def framework_for(cfg: dict, lang: str, task: str) -> str:
    langs = {l["name"]: l for l in cfg.get("languages", [])}
    info = langs.get(lang, {})
    return info.get("framework", info.get("default_framework", "std"))


def runtime_for(cfg: dict, lang: str) -> str:
    langs = {l["name"]: l for l in cfg.get("languages", [])}
    return langs.get(lang, {}).get("runtime", "")


def run_acceptance(task: str, lang: str) -> tuple[bool, list[dict]]:
    checks = TASKS / task / "acceptance" / "checks.json"
    workdir = LANGUAGES / lang / task
    cmd = [
        sys.executable, str(HARNESS / "acceptance.py"),
        "--checks", str(checks), "--workdir", str(workdir), "--json",
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return False, [{"name": "acceptance", "ok": False, "error": "timeout"}]
    try:
        data = json.loads(out.stdout)
        return bool(data.get("passed")), data.get("steps", [])
    except (json.JSONDecodeError, AttributeError):
        return False, [{"name": "acceptance", "ok": False, "error": out.stderr or out.stdout}]


def _step_line(s: dict) -> str:
    msg = str(s.get("error") or s.get("status") or "")
    body = s.get("body")
    if body:
        msg += f" (response body: {body})"
    return f"- {s.get('name')}: {msg}"


def _build_logs(workdir, tail: int = 2000) -> str:
    out = ""
    for name in ("run.start.log", "run.stop.log"):
        p = workdir / name
        if p.exists():
            try:
                txt = p.read_text(encoding="utf-8", errors="replace").strip()
            except OSError:
                continue
            if txt:
                out += f"\n{name} (tail):\n{txt[-tail:]}\n"
    return out


def run_single(cfg: dict, client: ChatClient, model_cfg: dict, task: str,
               lang: str, framework: str, prompt: str, rep: int, seed: int) -> dict:
    max_iter = cfg.get("max_iterations", 10)
    system = cfg.get("system_prompt", DEFAULT_SYSTEM)
    workdir = LANGUAGES / lang / task

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt},
    ]

    in_tokens_total = 0
    out_tokens_total = 0
    in_per_iter: list[int] = []
    out_per_iter: list[int] = []
    start = time.time()
    passed = False
    iterations = 0
    files_written: list[str] = []
    last_steps: list[dict] = []

    service = needs_service(TASKS / task / "acceptance" / "checks.json")

    for it in range(1, max_iter + 1):
        iterations = it
        resp = client.chat(messages, seed=seed)
        usage = resp["usage"]
        in_tok = int(usage.get("prompt_tokens") or count(messages[-1]["content"], model_cfg["name"])["tokens"])
        out_tok = int(usage.get("completion_tokens") or count(resp["content"], model_cfg["name"])["tokens"])
        in_tokens_total += in_tok
        out_tokens_total += out_tok
        in_per_iter.append(in_tok)
        out_per_iter.append(out_tok)

        content = resp["content"]
        files = extract_files(content, fallback_lang=lang)
        try:
            files_written = write_files(files, workdir)
        except ValueError as e:
            last_steps = [{"name": "write", "ok": False, "error": str(e)}]
        else:
            if service:
                stop_service(workdir)
                started, start_msg = start_service(workdir)
                if not started:
                    last_steps = [{"name": "build/start", "ok": False, "error": start_msg}]
                else:
                    passed, last_steps = run_acceptance(task, lang)
                    stop_service(workdir)
            else:
                passed, last_steps = run_acceptance(task, lang)

        if passed:
            break

        error_report = "\n".join(_step_line(s) for s in last_steps if not s.get("ok")) or "unknown failure"
        if service:
            error_report += _build_logs(workdir)
        messages.append({"role": "assistant", "content": content})
        messages.append({
            "role": "user",
            "content": f"Your solution failed the acceptance tests. Fix it.\nFailures:\n{error_report}",
        })

    if service:
        try:
            stop_service(workdir)
        except Exception:
            pass

    elapsed = time.time() - start
    model_name = model_cfg["name"]
    project_tok = project_tokens(workdir, model_name) if files_written else 0

    return {
        "model": model_name,
        "task": task,
        "language": lang,
        "framework": framework,
        "repetition": rep,
        "seed": seed,
        "passed": passed,
        "pass_at_1": passed and iterations == 1,
        "iterations": iterations,
        "input_tokens_total": in_tokens_total,
        "output_tokens_total": out_tokens_total,
        "input_tokens_per_iteration": in_per_iter,
        "output_tokens_per_iteration": out_per_iter,
        "cost_usd": cost_usd(in_tokens_total, out_tokens_total, model_cfg),
        "time_to_green_s": round(elapsed, 2),
        "files_written": files_written,
        "project_tokens_final": project_tok,
        "last_steps": last_steps,
        "timestamp": now_iso(),
    }


def load_base_files(task: str, lang: str) -> dict[str, str]:
    base_dir = TASKS / task / "base" / lang
    if not base_dir.exists():
        return {}
    files: dict[str, str] = {}
    for p in sorted(base_dir.rglob("*")):
        if p.is_file():
            files[str(p.relative_to(base_dir))] = p.read_text(encoding="utf-8", errors="replace")
    return files


def format_base_context(files: dict[str, str]) -> str:
    parts = ["The existing project files are included below. Modify only what is necessary.\n"]
    for path, content in files.items():
        parts.append(f"### FILE: {path}\n```\n{content}\n```\n")
    return "\n".join(parts)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default=None)
    ap.add_argument("--model", default=None)
    ap.add_argument("--task", default=None)
    ap.add_argument("--language", default=None)
    ap.add_argument("--reps", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true", help="render prompts only, no API calls")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    models = cfg.get("models", [])
    if args.model:
        models = [m for m in models if m["name"] == args.model]
    tasks = cfg.get("tasks", []) if not args.task else [args.task]
    languages = cfg.get("languages", []) if not args.language else [{"name": args.language, "framework": "std"}]
    reps = args.reps or cfg.get("repetitions", 5)
    base_seed = cfg.get("seed", 1234)

    for model_cfg in models:
        client = ChatClient(model_cfg)
        for task in tasks:
            prompt_tpl = (TASKS / task / "prompt.md").read_text(encoding="utf-8")
            for lng in languages:
                lang = lng["name"] if isinstance(lng, dict) else lng
                framework = framework_for(cfg, lang, task)
                runtime = runtime_for(cfg, lang)
                prompt = render_prompt(prompt_tpl, lang, framework, runtime)
                base_files = load_base_files(task, lang)
                workdir = LANGUAGES / lang / task
                if base_files:
                    import shutil
                    if workdir.exists():
                        shutil.rmtree(workdir)
                    for rel, content in base_files.items():
                        dest = workdir / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        dest.write_text(content, encoding="utf-8")
                    prompt = prompt + "\n\n" + format_base_context(base_files)
                if args.dry_run:
                    print(f"[dry-run] {model_cfg['name']} {task} {lang} ({framework})")
                    continue
                for rep in range(1, reps + 1):
                    seed = base_seed + rep
                    result = run_single(cfg, client, model_cfg, task, lang,
                                        framework, prompt, rep, seed)
                    out_dir = RESULTS / model_cfg["name"] / task / lang
                    out_dir.mkdir(parents=True, exist_ok=True)
                    out_file = out_dir / f"rep{rep:02d}.json"
                    out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
                    status = "PASS" if result["passed"] else "FAIL"
                    print(f"[{status}] {model_cfg['name']} {task} {lang} "
                          f"rep{rep} iters={result['iterations']} "
                          f"in={result['input_tokens_total']} out={result['output_tokens_total']} "
                          f"cost=${result['cost_usd']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
