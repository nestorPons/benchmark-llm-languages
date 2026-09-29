#!/usr/bin/env python3
"""Build/run/stop orchestration for a generated implementation.

Contract: each implementation provides a ``run.sh`` in its workdir.

- ``run.sh start``: build/install dependencies if needed, start the HTTP
  service in the background on port 8005, write its PID to ``server.pid``,
  and return 0.
- ``run.sh stop``:  stop the process from ``server.pid`` and remove the file.

For CLI tasks ``run.sh`` forwards subcommands and no service is managed here.

CLI:
    orchestrate.py start --workdir <dir> [--port 8005]
    orchestrate.py stop  --workdir <dir>
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path


def run(cmd: list[str], cwd: str | Path, timeout: int, logfile: str = "run.log") -> tuple[int, str, str]:
    """Run ``cmd`` redirecting stdout/stderr to a log file.

    Using a file (not pipes) so that backgrounded children (servers started by
    ``run.sh start``) don't keep the pipe open and block the caller forever.
    """
    cwd = Path(cwd)
    cwd.mkdir(parents=True, exist_ok=True)
    log = cwd / logfile
    with open(log, "w", encoding="utf-8") as fh:
        p = subprocess.Popen(cmd, cwd=str(cwd), stdout=fh, stderr=subprocess.STDOUT)
        try:
            p.wait(timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait()
            return -1, "", f"timeout after {timeout}s"
    try:
        out = log.read_text(encoding="utf-8", errors="replace")
    except OSError:
        out = ""
    return p.returncode, out, out


def _port_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def has_http_steps(checks: dict) -> bool:
    """True if any acceptance step is HTTP (i.e. a service must be running)."""
    return any("command" not in s for s in checks.get("steps", []))


def needs_service(checks_path: str | Path) -> bool:
    try:
        with open(checks_path, "r", encoding="utf-8") as fh:
            return has_http_steps(json.load(fh))
    except (OSError, json.JSONDecodeError):
        return True


def start_service(workdir: str | Path, port: int = 8005,
                  build_timeout: int = 600, ready_timeout: int = 300) -> tuple[bool, str]:
    workdir = Path(workdir)
    if not (workdir / "run.sh").exists():
        return False, "run.sh not found in workdir"
    rc, out, err = run(["bash", "run.sh", "start"], workdir, build_timeout, "run.start.log")
    if rc != 0:
        return False, (err or out or "run.sh start failed")[-1500:].strip()
    deadline = time.time() + ready_timeout
    while time.time() < deadline:
        if _port_open("127.0.0.1", port):
            return True, ""
        time.sleep(1)
    return True, "warning: port not open (acceptance will retry)"


def _kill_if_alive(pid: int) -> None:
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.kill(pid, 0)
        except OSError:
            return
        try:
            os.kill(pid, sig)
        except OSError:
            return
        time.sleep(0.5)


def stop_service(workdir: str | Path, timeout: int = 30, port: int = 8005) -> tuple[bool, str]:
    workdir = Path(workdir)
    if not (workdir / "run.sh").exists():
        return True, ""
    pidfile = workdir / "server.pid"
    pid = None
    if pidfile.exists():
        try:
            pid = int(pidfile.read_text().strip())
        except ValueError:
            pid = None
    rc, out, err = run(["bash", "run.sh", "stop"], workdir, timeout, "run.stop.log")
    if pid is not None:
        _kill_if_alive(pid)
    # Fallback: kill any process still listening on the port (catches children
    # spawned by `go run`, `uvicorn --reload` workers, `npm`/`node`, etc.).
    try:
        subprocess.run(["fuser", "-k", f"{port}/tcp"], capture_output=True, timeout=10)
    except Exception:
        pass
    return rc == 0, (err or out)[-1500:].strip() if rc != 0 else ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start")
    s.add_argument("--workdir", required=True)
    s.add_argument("--port", type=int, default=8005)
    s.add_argument("--build-timeout", type=int, default=600)
    s.add_argument("--ready-timeout", type=int, default=300)
    t = sub.add_parser("stop")
    t.add_argument("--workdir", required=True)
    t.add_argument("--timeout", type=int, default=30)
    t.add_argument("--port", type=int, default=8005)
    args = ap.parse_args(argv)

    if args.cmd == "start":
        ok, msg = start_service(args.workdir, args.port, args.build_timeout, args.ready_timeout)
    else:
        ok, msg = stop_service(args.workdir, args.timeout, args.port)
    print(("OK " if ok else "ERROR ") + (msg or ""))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
