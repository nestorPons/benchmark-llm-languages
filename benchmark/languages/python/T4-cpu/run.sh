#!/bin/bash

set -e

case "$1" in
    start)
        python3 -m venv venv
        source venv/bin/activate
        pip install Flask
        python app/main.py & echo $! > server.pid
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