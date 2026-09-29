#!/bin/bash

set -e

function start() {
  npm install
  npm run build
  nohup node dist/index.js &
  echo $! > server.pid
}

function stop() {
  if [ -f server.pid ]; then
    kill $(cat server.pid)
    rm server.pid
  fi
}

case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  *)
    echo "Usage: $0 {start|stop}"
    exit 1
esac