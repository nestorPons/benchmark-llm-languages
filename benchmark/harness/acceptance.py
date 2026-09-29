#!/usr/bin/env python3
"""Language-agnostic acceptance runner.

Runs the checks in ``checks.json`` against an implementation. Checks are either
HTTP (default) or command (CLI). They are identical for every language.

Step types
----------
HTTP step (no ``command`` key):
  method, path, headers, json/body, expect_status (int or list),
  expect_json (subset match), json_path (dot path), save, retries,
  retry_delay_s, timeout.

Command step (``command`` key present):
  command (string or list; supports {var} substitution), cwd, env,
  expect_exit (int or list, default 0), expect_stdout_contains (str or list),
  expect_stdout_json (subset match on stdout parsed as JSON), json_path, save,
  timeout.

Top-level:
  port, startup_retries, startup_delay_s, steps.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

import requests


def _substitute(template, variables):
    if isinstance(template, str):
        return re.sub(r"\{(\w+)\}", lambda m: str(variables.get(m.group(1), m.group(0))), template)
    if isinstance(template, list):
        return [_substitute(v, variables) for v in template]
    if isinstance(template, dict):
        return {k: _substitute(v, variables) for k, v in template.items()}
    return template


def _get_path(obj, path):
    for part in path.split("."):
        if obj is None:
            return None
        if isinstance(obj, list) and part.isdigit():
            obj = obj[int(part)] if int(part) < len(obj) else None
        elif isinstance(obj, dict):
            obj = obj.get(part)
        else:
            return None
    return obj


def _partial_match(expected, actual):
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return False
        return all(_partial_match(v, actual.get(k)) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(expected) == len(actual) and all(
            _partial_match(e, a) for e, a in zip(expected, actual))
    return expected == actual


def _status_ok(actual, expected):
    if expected is None:
        return True
    if isinstance(expected, list):
        return actual in expected
    return actual == expected


def _attempt_http(step, variables, base_url):
    """One HTTP attempt. Returns (ok, rec)."""
    method = step.get("method", "GET").upper()
    path = _substitute(step.get("path", "/"), variables)
    headers = _substitute(step.get("headers", {}), variables)
    url = base_url.rstrip("/") + path
    kwargs = {"headers": headers, "timeout": step.get("timeout", 30)}
    if "json" in step:
        kwargs["json"] = _substitute(step["json"], variables)
    elif "body" in step:
        kwargs["data"] = _substitute(step["body"], variables)

    rec = {}
    resp = requests.request(method, url, **kwargs)
    rec["status"] = resp.status_code
    body = None
    try:
        body = resp.json()
    except ValueError:
        rec["body"] = resp.text[:500]

    status_ok = _status_ok(resp.status_code, step.get("expect_status"))
    body_ok = True
    if status_ok:
        if "expect_json" in step and not _partial_match(step["expect_json"], body):
            body_ok = False
            rec["error"] = f"body mismatch: {body}"
    else:
        rec["error"] = f"status {resp.status_code}, expected {step.get('expect_status')}"
        if body is not None:
            rec["body"] = str(body)[:300]

    rec["ok"] = status_ok and body_ok

    if rec["ok"] and step.get("json_path") and body is not None:
        paths = step["json_path"] if isinstance(step["json_path"], list) else [step["json_path"]]
        val = None
        for p in paths:
            val = _get_path(body, p)
            if val is not None:
                break
        if val is None and step.get("save"):
            rec["ok"] = False
            rec["error"] = f"json_path {paths!r} not found"
        if step.get("save"):
            variables[step["save"]] = val

    return bool(rec.get("ok")), rec


def _attempt_command(step, variables, workdir):
    """One command attempt. Returns (ok, rec)."""
    command = _substitute(step["command"], variables)
    cwd = step.get("cwd") or workdir
    env = dict(os.environ)
    env.update(step.get("env", {}))
    try:
        proc = subprocess.run(
            command, shell=isinstance(command, str), cwd=cwd, env=env,
            capture_output=True, text=True, timeout=step.get("timeout", 60),
        )
    except subprocess.TimeoutExpired:
        return False, {"error": "command timed out"}
    rec = {"exit": proc.returncode, "stdout": proc.stdout[:500], "stderr": proc.stderr[:500]}

    expected_exit = step.get("expect_exit", 0)
    if not _status_ok(proc.returncode, expected_exit):
        rec["error"] = f"exit {proc.returncode}, expected {expected_exit}"
        return False, rec

    if step.get("expect_stdout_contains"):
        need = step["expect_stdout_contains"]
        need = [need] if isinstance(need, str) else need
        missing = [n for n in need if n not in proc.stdout]
        if missing:
            rec["error"] = f"stdout missing {missing}"
            return False, rec

    if step.get("expect_stdout_json"):
        try:
            parsed = json.loads(proc.stdout)
        except json.JSONDecodeError:
            rec["error"] = f"stdout is not JSON: {proc.stdout[:200]}"
            return False, rec
        if not _partial_match(step["expect_stdout_json"], parsed):
            rec["error"] = f"stdout JSON mismatch: {proc.stdout[:200]}"
            return False, rec
        if step.get("json_path") or step.get("save"):
            val = _get_path(parsed, step.get("json_path", ""))
            if val is None and step.get("save"):
                rec["error"] = f"json_path {step.get('json_path')!r} not found"
                return False, rec
            if step.get("save"):
                variables[step["save"]] = val

    rec["ok"] = True
    return True, rec


def run(checks: dict, base_url: str = "", workdir: str = "") -> tuple[bool, list[dict]]:
    port = checks.get("port", 8005)
    if not base_url:
        base_url = f"http://127.0.0.1:{port}"
    workdir = workdir or os.getcwd()

    steps = checks.get("steps", [])
    has_http = any("command" not in s for s in steps)

    results: list[dict] = []
    ok = True

    if has_http:
        retries = checks.get("startup_retries", 0)
        for i in range(retries):
            try:
                requests.get(base_url, timeout=2)
                break
            except requests.RequestException:
                if i == retries - 1:
                    results.append({"name": "startup", "ok": False, "error": "service did not start"})
                    return False, results
                time.sleep(checks.get("startup_delay_s", 1.0))

    variables: dict[str, object] = {}

    for step in steps:
        name = step.get("name", step.get("path", step.get("command", "?")))
        attempts = step.get("retries", 1)
        delay = step.get("retry_delay_s", 0.5)
        rec = {"name": name, "ok": False}
        for a in range(attempts):
            try:
                if "command" in step:
                    passed, rec = _attempt_command(step, variables, workdir)
                else:
                    passed, rec = _attempt_http(step, variables, base_url)
            except requests.RequestException as e:
                passed, rec = False, {"name": name, "ok": False, "error": str(e)}
            rec["name"] = name
            if passed:
                break
            if a < attempts - 1:
                time.sleep(delay)
        results.append(rec)
        if not rec.get("ok"):
            ok = False

    return ok, results


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--checks", required=True, help="path to checks.json")
    ap.add_argument("--base-url", default="", help="override base URL")
    ap.add_argument("--workdir", default="", help="working dir for command steps")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args(argv)

    with open(args.checks, "r", encoding="utf-8") as fh:
        checks = json.load(fh)

    ok, results = run(checks, args.base_url, args.workdir)

    if args.json:
        print(json.dumps({"passed": ok, "steps": results}, indent=2))
    else:
        for r in results:
            mark = "PASS" if r.get("ok") else "FAIL"
            extra = f" -> {r.get('error')}" if not r.get("ok") else ""
            print(f"[{mark}] {r['name']}{extra}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
