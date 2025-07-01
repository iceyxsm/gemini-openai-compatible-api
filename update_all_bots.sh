#!/bin/bash

TEMPLATE="bots/template_bot.py"
BOTS_DIR="bots"

for botfile in "$BOTS_DIR"/*.py; do
    if [[ "$botfile" != "$TEMPLATE" ]]; then
        cp "$TEMPLATE" "$botfile"
    fi
done

echo "All bots updated with the latest template."

# Restart all child bot systemd services
echo "Restarting all ggpt-bot-* services..."
sudo systemctl daemon-reload
for svc in /etc/systemd/system/ggpt-bot-*.service; do
    svcname=$(basename "$svc")
    sudo systemctl restart "$svcname"
    echo "Restarted $svcname"
done

echo "All child bot services restarted." 