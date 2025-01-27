#!/bin/bash

# Start Xvfb
Xvfb :99 -screen 0 1280x1024x16 &
export DISPLAY=:99

# Start fluxbox window manager
fluxbox &

# Start x11vnc
x11vnc -forever -usepw -display :99 &

# Start noVNC
/usr/share/novnc/utils/launch.sh --vnc localhost:5900 --listen 6080 &

# Start the FastAPI server
python3 api.py