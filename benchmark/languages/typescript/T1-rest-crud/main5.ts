# run.sh
#!/bin/bash

set -e

function start() {
  cd app
  npm install
  npx prisma migrate deploy
  nohup npm start & echo $! > server.pid
  cd ..
}

function stop() {
  if [ -f app/server.pid ]; then
    kill $(cat app/server.pid) && rm app/server.pid
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