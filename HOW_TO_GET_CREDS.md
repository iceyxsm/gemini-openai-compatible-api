# How to Get All Required Credentials

This guide explains how to obtain all the credentials needed to set up and run this project.

---

## 1. Gemini API Key (Google Generative Language API)

**Purpose:** Powers the AI backend (chat completions, etc.)

### Steps:
1. Go to the [Google AI Studio](https://aistudio.google.com/app/apikey) and sign in with your Google account.
2. Click **Create API Key**.
3. Copy the generated API key (it will look like `AIza...`).
4. In the Telegram admin bot, go to **Gemini API Key Management** and add your key (just paste the key when prompted).

**Note:**
- You only need the API key, not the project ID or anything else.
- The backend uses the endpoint: `https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent`

---

## 2. Supabase Credentials

**Purpose:** Used for database, admin/user management, and API key storage.

### Steps:
1. Go to [Supabase](https://supabase.com/) and sign in or create an account.
2. Create a new project (or use an existing one).
3. In your project dashboard, go to **Project Settings > API**.
4. Copy the following:
   - **Project ID** (e.g., `xdhpetpttwrddrfmgjhg`)
   - **Project URL** (e.g., `https://xdhpetpttwrddrfmgjhg.supabase.co`)
   - **Service Role Key** (long JWT string, used as the "Supabase Service Key")
5. During setup, you will be prompted for the **Project ID** and **Service Role Key**. The setup script will construct the URL for you.

**Warning:**
- Never share your Service Role Key publicly. It has admin access to your database.

---

## 3. Telegram Bot Token

**Purpose:** Allows the project to run a Telegram bot for admin and user interaction.

### Steps:
1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
2. Start a chat and send `/newbot`.
3. Follow the prompts to set a name and username for your bot.
4. Copy the **bot token** provided (it will look like `123456789:ABCdefGhIJKlmNoPQRstuVwxyZ`).
5. Use this token when prompted during setup.

---

## 4. Telegram Admin User ID

**Purpose:** Restricts admin access to your Telegram user.

### Steps:
1. In Telegram, search for [@userinfobot](https://t.me/userinfobot) and start it.
2. Send `/start` and it will reply with your numeric **user ID**.
3. Use this ID as the **Admin Telegram ID** during setup.

---

## 5. Optional: Let's Encrypt Email

**Purpose:** For SSL certificate renewal notifications.

### Steps:
- Use any valid email address you control.

---

## Summary Table

| Credential                | Where to Get It                                      | Where to Use It                |
|---------------------------|------------------------------------------------------|---------------------------------|
| Gemini API Key            | Google AI Studio                                     | Add via bot (Gemini Key Mgmt)   |
| Supabase Project ID       | Supabase Project Settings > API                      | Setup script prompt             |
| Supabase Service Key      | Supabase Project Settings > API                      | Setup script prompt             |
| Telegram Bot Token        | @BotFather on Telegram                               | Setup script prompt             |
| Admin Telegram ID         | @userinfobot on Telegram                             | Setup script prompt             |
| Let's Encrypt Email       | Any email you control                                | Setup script prompt             |

---

**If you have any issues, check the README or ask for help!** 