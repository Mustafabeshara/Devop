#!/bin/bash

# Start Xvfb
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99

# Start Fluxbox window manager
fluxbox &

# Start VNC server
x11vnc -forever -usepw -display :99 -rfbport 5900 &

# Start Selenium WebDriver
/opt/bin/entry_point.sh
