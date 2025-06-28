# Gemini-Powered OpenAI-Compatible API Service

## Overview
This project is a production-ready, OpenAI-compatible API platform powered by Google Gemini. It allows you to:
- Offer an OpenAI-style API (like ChatGPT) to your users, but powered by Gemini under the hood
- Manage user-facing API keys, Gemini backend keys, and dynamic Telegram bots from a secure admin panel
- Deploy and manage multiple smart Telegram bots, each with its own context and API key
- Monitor server resources and receive daily usage reports automatically
- Scale easily with robust automation, rate limiting, and distributed queuing

**Main use cases:**
- Build your own OpenAI-style API service for customers, teams, or internal use
- Deploy custom Telegram bots that use Gemini for chat, support, or automation
- Manage all API keys, bots, and resources from a single, secure Telegram admin interface

---

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [API (for your users)](#api-for-your-users)
  - [Admin Bot (Telegram)](#admin-bot-telegram)
- [How To: Setup & Keys](#how-to-setup--keys)
- [Example: Using the API with Python](#example-using-the-api-with-python)
- [Security & Scaling](#security--scaling)
- [Troubleshooting](#troubleshooting)
- [Telegram Bot Commands](#telegram-bot-commands)

---

## Features
- OpenAI-compatible API endpoints (`/v1/chat/completions`)
- Powered by Google Gemini (all completions use Gemini under the hood)
- Multi-model support (accepts any model name for compatibility)
- User-facing API keys (for your customers, managed via Telegram bot)
- Gemini API key rotation and distributed rate limiting (Redis/RQ)
- Telegram admin panel:
  - Gemini API Key Management (add/remove/list backend keys)
  - User API Key Management (create/revoke/list user API keys)
  - Dynamic Bot Management (create/list Telegram bots, each with its own API key and optional base prompt)
  - VPS Resource Monitoring (CPU, RAM, disk usage)
  - Admin Management (add/remove/list admins; only owner can manage admins)
- Fully automated setup (Nginx, SSL, Redis, systemd, etc.)
- One-click bot deployment (each bot is an isolated systemd service)
- Daily usage reports sent to the owner via Telegram
- Supabase for all persistent state (keys, users, usage logs, bots)

---

## Installation

**1. Clone the repository:**
```bash
git clone https://github.com/iceyxsm/gemini-openai-compatible-api.git
cd gemini-openai-compatible-api/setup/
```

**2. Run the setup script:**
```bash
sudo bash setup.sh
```
- Follow the prompts to enter your domain, Supabase keys, Telegram bot token, admin Telegram ID, and other info.
- The script will install all dependencies, set up Nginx, SSL, Redis, systemd services, and make all scripts executable.

**3. Set up Supabase schema:**
- Open the SQL editor in your Supabase project.
- Copy and run the contents of `supabase/schema.sql` to create all required tables.

**4. (Optional) Enable daily usage reports:**
- Add this line to your crontab (`crontab -e`):
  ```
  0 0 * * * cd $(pwd) && .venv/bin/python3 send_daily_usage_report.py
  ```

---

## Usage

### API (for your users)
- **Base URL:**
  ```
  https://<your-domain-or-subdomain>/v1/chat/completions
  ```
- **Authentication:**
  - Every request must include an API key:
    ```
    Authorization: Bearer <user-api-key>
    ```
- **Request Format:**
  - Follows OpenAI `/v1/chat/completions` spec:
    ```json
    {
      "model": "gpt-4",  // or "gemini-pro", etc. (all routed to Gemini)
      "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me a joke."}
      ],
      "temperature": 0.7,
      "max_tokens": 512
    }
    ```
- **Response Format:**
  - Matches OpenAI's response:
    ```json
    {
      "id": "chatcmpl-xxxx",
      "object": "chat.completion",
      "created": 1710000000,
      "model": "gpt-4",
      "choices": [
        {
          "index": 0,
          "message": {"role": "assistant", "content": "Why did the chicken cross the road? ..."},
          "finish_reason": "stop"
        }
      ],
      "usage": {
        "prompt_tokens": 12,
        "completion_tokens": 16,
        "total_tokens": 28
      }
    }
    ```
- **Supported Models:**
  - Any model name is accepted for compatibility, but all completions are powered by Gemini.

### Admin Bot (Telegram)
- **Main Menu:**
  - Gemini API Key Management
  - User API Key Management
  - Bots (create/list Telegram bots, each with their own API key and optional base prompt)
  - VPS Resources
  - Admins (only owner can add/remove admins)
- **Bot Creation:**
  - Enter name, token, and (optionally) a base prompt for a "super bot."
  - The system auto-generates a user API key for the bot and deploys it as a systemd service.
  - Each bot is isolated and uses its own API key and base prompt.
- **Resource Monitoring:**
  - View real-time CPU, RAM, and disk usage from the Telegram bot.
- **Daily Usage Reports:**
  - Owner receives a daily usage summary via Telegram at midnight.

---

## How To: Setup & Keys

### 1. Prerequisites
- A VPS (Ubuntu/Debian recommended)
- A domain or subdomain pointed to your VPS (update DNS A record)
- [Supabase](https://supabase.com/) account and project
- [Telegram](https://core.telegram.org/bots) account to create a bot for admin panel
- Google Gemini API keys (from Google Cloud Console)

### 2. Get Your Keys
- **Supabase URL & Service Key:**
  - Go to your Supabase project > Project Settings > API
  - Copy the `Project URL` and `Service Role` key
- **Telegram Bot Token:**
  - Talk to [@BotFather](https://t.me/BotFather) on Telegram
  - Create a new bot and copy the token
- **Admin Telegram ID:**
  - Use [@userinfobot](https://t.me/userinfobot) to get your Telegram user ID
- **Gemini API Keys:**
  - Go to [Google Cloud Console](https://console.cloud.google.com/)
  - Enable Gemini API and create API keys for your project

### 3. Supabase Schema
- Open the SQL editor in your Supabase project
- Run the contents of `supabase/schema.sql` to create all required tables

### 4. Setup
- SSH into your VPS
- Clone this repo and `cd` into it
- Run the setup script:
  ```bash
  ./setup/setup.sh
  ```
- Follow the prompts to enter your domain, keys, and other info
- The script will:
  - Install all dependencies
  - Set up Python venv and requirements
  - Configure Nginx, SSL, Redis, and systemd services
  - Make all scripts executable
  - Print a cron line for daily usage reports (add it to your crontab)

### 5. Using the Admin Bot
- Start a chat with your admin Telegram bot
- Use the menu to manage API keys, bots, admins, and view resources
- To create a new bot:
  - Click "Bots" > "Create Bot"
  - Enter the name, token, and (optionally) a base prompt
  - The bot will be deployed and ready to use

### 6. Using the API
- Give your users their API keys (created via the admin bot)
- They can use any OpenAI-compatible client or SDK
- All completions are powered by Gemini, but the API is OpenAI-compatible

---

## Example: Using the API with Python
```python
import requests

API_KEY = 'your-user-api-key'
url = 'https://yourdomain.com/v1/chat/completions'
headers = {'Authorization': f'Bearer {API_KEY}'}
payload = {
    'model': 'gpt-4',
    'messages': [
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'Tell me a joke.'}
    ]
}
response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

---

## Security & Scaling
- All sensitive operations use `sudo` where required
- Rate limiting and queuing are handled via Redis and RQ
- All services are managed by systemd for reliability
- Only the owner can add/remove admins; all admins can use the bot

---

## Troubleshooting
- Check logs with:
  ```
  sudo journalctl -u ggpt-backend -f
  sudo journalctl -u ggpt-telegram-bot -f
  sudo journalctl -u ggpt-rq-worker -f
  sudo journalctl -u redis-server -f
  sudo journalctl -u ggpt-bot-<botname> -f
  ```
- Ensure your domain's DNS is set up before running the setup script
- For any issues, restart services with `sudo systemctl restart <service-name>`

---

## Telegram Bot Commands

The admin Telegram bot is fully button-driven, but you can also use these commands:

| Command/Button            | Description |
|---------------------------|-------------|
| /start                    | Show the main admin menu |
| Gemini API Key Management | Add, remove, or list Gemini (backend) API keys |
| User API Key Management   | Create, revoke, or list user-facing API keys |
| Bots                      | Create new Telegram bots, list all bots |
| Create Bot                | Register a new bot (name, token, optional base prompt) |
| List Bots                 | Show all registered bots |
| VPS Resources             | Show current CPU, RAM, and disk usage |
| Admins                    | List all admins (only owner can add/remove) |
| Add Admin                 | (Owner only) Add a new admin by Telegram ID |
| Remove Admin              | (Owner only) Remove an admin |
| Update Server              | (Owner only) Pull latest code, update dependencies, and restart all services (uses sudo) |

**All actions are available via buttons in the bot's menu. Only the owner can manage admins and update the server.**

---

**You are now ready to launch, scale, and manage your own Gemini-powered, OpenAI-compatible API platform!** 
