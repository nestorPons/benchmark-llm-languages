#!/bin/bash

set -e

case "$1" in
  start)
    if [ ! -d "venv" ]; then
      python3 -m venv venv
      source venv/bin/activate
      pip install fastapi[all] sqlalchemy pyjwt
    fi
    source venv/bin/activate
    uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload &
    echo $! > server.pid
    ;;
  stop)
    if [ -f server.pid ]; then
      kill $(cat server.pid)
      rm server.pid
    fi
    ;;
  *)
    echo "Usage: $0 {start|stop}"
    exit 1
    ;;
esac