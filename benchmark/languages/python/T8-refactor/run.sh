#!/bin/bash
set -e
case "$1" in
  start)
    python3 -m venv venv
    ./venv/bin/pip install -r requirements.txt
    nohup ./venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8005 > app.log 2>&1 &
    echo $! > server.pid
    ;;
  stop)
    [ -f server.pid ] && kill "$(cat server.pid)" 2>/dev/null || true
    rm -f server.pid
    ;;
  *)
    echo "Usage: $0 {start|stop}"
    exit 1
    ;;
esac