#!/bin/bash
set -e
case "$1" in
  start)
    npm install
    npm run build
    nohup node dist/index.js > app.log 2>&1 &
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
