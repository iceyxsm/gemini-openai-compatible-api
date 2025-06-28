#!/bin/bash
set -e

if [ $# -lt 3 ]; then
  echo "Usage: $0 <bot_name> <bot_token> <bot_id>"
  exit 1
fi

BOT_NAME="$1"
BOT_TOKEN="$2"
BOT_ID="$3"
BACKEND_URL="http://127.0.0.1:8000/v1/chat/completions"
SUPABASE_URL=$(grep SUPABASE_URL .env | cut -d '=' -f2-)
SUPABASE_SERVICE_KEY=$(grep SUPABASE_SERVICE_KEY .env | cut -d '=' -f2-)

BOT_DIR="bots/$BOT_NAME"
mkdir -p "$BOT_DIR"
cp bots/template_bot.py "$BOT_DIR/bot.py"

cat > "$BOT_DIR/.env" <<EOL
BOT_TOKEN=$BOT_TOKEN
BOT_ID=$BOT_ID
BACKEND_URL=$BACKEND_URL
SUPABASE_URL=$SUPABASE_URL
SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY
EOL

sudo tee /etc/systemd/system/ggpt-bot-$BOT_NAME.service > /dev/null <<EOL
[Unit]
Description=GGPT Dynamic Bot: $BOT_NAME
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)/$BOT_DIR
EnvironmentFile=$(pwd)/$BOT_DIR/.env
ExecStart=$(pwd)/.venv/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

sudo systemctl daemon-reload
sudo systemctl enable ggpt-bot-$BOT_NAME.service
sudo systemctl restart ggpt-bot-$BOT_NAME.service

echo "Bot $BOT_NAME deployed and running as a systemd service." 