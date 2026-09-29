#!/bin/bash

function start() {
    go mod tidy
    go build -o app
    ./app &
    echo $! > server.pid
    return 0
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
        ;;
esac