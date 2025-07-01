#!/bin/bash

TEMPLATE="bots/template_bot.py"
BOTS_DIR="bots"
RESTARTED_BOTS=()

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
    RESTARTED_BOTS+=("$svcname")
done

echo ""
echo "All child bot services restarted:"
for name in "${RESTARTED_BOTS[@]}"; do
    echo " - $name"
done 