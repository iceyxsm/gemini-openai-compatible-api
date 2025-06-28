#!/bin/bash
set -e

# 1. Prompt for all secrets
read -p "Enter your domain or subdomain (e.g., api.example.com): " DOMAIN
read -p "Enter your Supabase URL: " SUPABASE_URL
read -p "Enter your Supabase Service Key: " SUPABASE_SERVICE_KEY
read -p "Enter your Telegram Bot Token: " TELEGRAM_BOT_TOKEN
read -p "Enter your Admin Telegram ID: " ADMIN_TELEGRAM_ID
read -p "Enter default regions (comma-separated, default: us-central1,us-west4,europe-west3): " DEFAULT_REGIONS
DEFAULT_REGIONS=${DEFAULT_REGIONS:-us-central1,us-west4,europe-west3}
read -p "Enter rate limit per region (default: 60): " RATE_LIMIT_PER_REGION
RATE_LIMIT_PER_REGION=${RATE_LIMIT_PER_REGION:-60}
read -p "Enable search grounding? (true/false, default: true): " USE_SEARCH_GROUNDING
USE_SEARCH_GROUNDING=${USE_SEARCH_GROUNDING:-true}

# 2. Write .env file
envfile=".env"
echo "SUPABASE_URL=$SUPABASE_URL" > $envfile
echo "SUPABASE_SERVICE_KEY=$SUPABASE_SERVICE_KEY" >> $envfile
echo "TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN" >> $envfile
echo "ADMIN_TELEGRAM_ID=$ADMIN_TELEGRAM_ID" >> $envfile
echo "DEFAULT_REGIONS=$DEFAULT_REGIONS" >> $envfile
echo "RATE_LIMIT_PER_REGION=$RATE_LIMIT_PER_REGION" >> $envfile
echo "USE_SEARCH_GROUNDING=$USE_SEARCH_GROUNDING" >> $envfile
echo "REDIS_URL=redis://localhost:6379/0" >> $envfile

# 3. Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx redis-server

# 4. Start and enable Redis
sudo systemctl enable redis-server
sudo systemctl restart redis-server

# 5. Set up Python venv and install requirements
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# 6. Render and install Nginx config
template="setup/nginx.conf.template"
nginx_conf="/etc/nginx/sites-available/$DOMAIN"
sudo cp $template $nginx_conf
tmpfile=$(mktemp)
sed "s/{{DOMAIN}}/$DOMAIN/g" $template > $tmpfile
sudo mv $tmpfile $nginx_conf
sudo ln -sf $nginx_conf /etc/nginx/sites-enabled/$DOMAIN
sudo rm -f /etc/nginx/sites-enabled/default

# 7. Obtain SSL cert with Certbot
echo "Obtaining SSL certificate for $DOMAIN..."
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m admin@$DOMAIN

# 8. Create systemd service for backend
sudo tee /etc/systemd/system/ggpt-backend.service > /dev/null <<EOL
[Unit]
Description=GGPT Backend Service
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
EnvironmentFile=$(pwd)/.env
ExecStart=$(pwd)/.venv/bin/gunicorn -k uvicorn.workers.UvicornWorker backend.main:app --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# 9. Create systemd service for Telegram bot
sudo tee /etc/systemd/system/ggpt-telegram-bot.service > /dev/null <<EOL
[Unit]
Description=GGPT Telegram Bot Service
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
EnvironmentFile=$(pwd)/.env
ExecStart=$(pwd)/.venv/bin/python3 telegram_bot/bot.py
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# 10. Create systemd service for RQ worker (Gemini queue)
sudo tee /etc/systemd/system/ggpt-rq-worker.service > /dev/null <<EOL
[Unit]
Description=GGPT RQ Worker (Gemini Queue)
After=network.target

[Service]
User=$USER
WorkingDirectory=$(pwd)
EnvironmentFile=$(pwd)/.env
ExecStart=$(pwd)/.venv/bin/rq worker gemini_requests
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# 11. Reload and enable services
sudo systemctl daemon-reload
sudo systemctl enable ggpt-backend.service
sudo systemctl enable ggpt-telegram-bot.service
sudo systemctl enable ggpt-rq-worker.service
sudo systemctl restart ggpt-backend.service
sudo systemctl restart ggpt-telegram-bot.service
sudo systemctl restart ggpt-rq-worker.service
sudo systemctl restart nginx

# 12. Make all shell scripts executable
chmod +x setup/setup.sh
chmod +x setup/deploy_new_bot.sh
chmod +x send_daily_usage_report.py

echo "\nSetup complete!"
echo "Your API is available at: https://$DOMAIN/v1/chat/completions"
echo "Telegram admin bot is running."
echo "RQ worker and Redis are running for Gemini queue."
echo "All services are managed by systemd."
echo "You can check logs with:"
echo "  sudo journalctl -u ggpt-backend -f"
echo "  sudo journalctl -u ggpt-telegram-bot -f"
echo "  sudo journalctl -u ggpt-rq-worker -f"
echo "  sudo journalctl -u redis-server -f"
echo "\nTo enable daily usage reports, add this to your crontab (crontab -e):"
echo "0 0 * * * cd $(pwd) && .venv/bin/python3 send_daily_usage_report.py" 