#!/usr/bin/env bash
# Start Chromium in Fullscreen Kiosk Mode for AI Fitness Coach
set -euo pipefail

# Disable screensaver and power management
xset s off || true
xset -dpms || true
xset s noblank || true

# Hide mouse cursor when idle
unclutter -idle 2 -root &

# Wait until backend is healthy
until curl -s http://localhost:5001/api/health >/dev/null 2>&1; do
    echo "[Kiosk] Waiting for AI Coach backend to be ready..."
    sleep 1
done

echo "[Kiosk] Launching Chromium Kiosk Display..."
sed -i 's/"exited_cleanly":false/"exited_cleanly":true/' ~/.config/chromium/Default/Preferences 2>/dev/null || true
sed -i 's/"exit_type":"Crashed"/"exit_type":"Normal"/' ~/.config/chromium/Default/Preferences 2>/dev/null || true

exec /usr/bin/chromium-browser \
    --kiosk \
    --no-first-run \
    --no-default-browser-check \
    --disable-translate \
    --disable-features=Translate \
    --disable-notifications \
    --disable-pinch \
    --overscroll-history-navigation=0 \
    --disable-session-crashed-bubble \
    --disable-infobars \
    --check-for-update-interval=31536000 \
    --touch-events=enabled \
    --enable-features=OverlayScrollbar \
    --autoplay-policy=no-user-gesture-required \
    http://localhost:5001
