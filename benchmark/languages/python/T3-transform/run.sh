#!/bin/bash

set -e

case "$1" in
    start)
        python3 -m venv venv
        source venv/bin/activate
        pip install fastapi[all] pandas
        uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload &
        echo $! > server.pid
        ;;
    stop)
        if [ -f server.pid ]; then
            kill $(cat server.pid) && rm server.pid
        else
            echo "Server not running."
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop}"
        exit 1
        ;;
esac