import os
import sys
import psutil
import subprocess


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
)
from supabase_client import (
    list_keys, add_key, remove_key,
    create_user_api_key, list_user_api_keys, revoke_user_api_key,
    list_admins, add_admin, remove_admin, is_admin,
    create_bot, list_bots
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
SUPERADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not (is_admin(user_id) or user_id == str(SUPERADMIN_TELEGRAM_ID)):
        first_name = update.effective_user.first_name
        await update.message.reply_text(f"hi {first_name}\nid: {user_id}\nyou are not auth")
        return
    keyboard = [
        [InlineKeyboardButton("Gemini API Key Management", callback_data="menu_gemini")],
        [InlineKeyboardButton("User API Key Management", callback_data="menu_user")],
        [InlineKeyboardButton("Bots", callback_data="menu_bots")],
        [InlineKeyboardButton("VPS Resources", callback_data="vps_resources")],
        [InlineKeyboardButton("Admins", callback_data="menu_admins")],
    ]
    if user_id == SUPERADMIN_TELEGRAM_ID:
        keyboard.append([InlineKeyboardButton("Update Server", callback_data="update_server")])
    await update.message.reply_text(
        "Welcome to the Gemini API Admin Panel. Choose an option:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    if not (is_admin(user_id) or user_id == str(SUPERADMIN_TELEGRAM_ID)):
        await query.edit_message_text("Unauthorized.")
        return
    # Helper to clear user state
    def clear_user_state():
        context.user_data.clear()
    # Main menu navigation
    if query.data == "menu_gemini":
        clear_user_state()
        keyboard = [
            [InlineKeyboardButton("Add Gemini API Key", callback_data="add_gemini_key")],
            [InlineKeyboardButton("Remove Gemini API Key", callback_data="remove_gemini_key")],
            [InlineKeyboardButton("List Gemini API Keys", callback_data="list_gemini_keys")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")],
        ]
        await query.edit_message_text("Gemini API Key Management:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "menu_user":
        clear_user_state()
        keyboard = [
            [InlineKeyboardButton("Create User API Key", callback_data="create_user_key")],
            [InlineKeyboardButton("Revoke User API Key", callback_data="revoke_user_key")],
            [InlineKeyboardButton("List User API Keys", callback_data="list_user_keys")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")],
        ]
        await query.edit_message_text("User API Key Management:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "menu_bots":
        clear_user_state()
        keyboard = [
            [InlineKeyboardButton("Create Bot", callback_data="create_bot")],
            [InlineKeyboardButton("List Bots", callback_data="list_bots")],
            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")],
        ]
        await query.edit_message_text("Bots Management:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "main_menu":
        clear_user_state()
        try:
            await start(update, context)
        except Exception:
            await query.message.reply_text("Welcome to the Gemini API Admin Panel. Choose an option:")
    elif query.data == "vps_resources":
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        msg = (
            f"<b>VPS Resources</b>\n"
            f"CPU Usage: {cpu}%\n"
            f"RAM Usage: {mem.percent}% ({mem.used // (1024**2)}MB/{mem.total // (1024**2)}MB)\n"
            f"Disk Usage: {disk.percent}% ({disk.used // (1024**3)}GB/{disk.total // (1024**3)}GB)"
        )
        try:
            await query.edit_message_text(
                msg,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Reload", callback_data="reload_vps_resources")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
                ])
            )
        except Exception:
            await query.message.reply_text(msg)
    elif query.data == "reload_vps_resources":
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        msg = (
            f"<b>VPS Resources</b>\n"
            f"CPU Usage: {cpu}%\n"
            f"RAM Usage: {mem.percent}% ({mem.used // (1024**2)}MB/{mem.total // (1024**2)}MB)\n"
            f"Disk Usage: {disk.percent}% ({disk.used // (1024**3)}GB/{disk.total // (1024**3)}GB)"
        )
        try:
            await query.edit_message_text(
                msg,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Reload", callback_data="reload_vps_resources")],
                    [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
                ])
            )
        except Exception:
            await query.message.reply_text(msg)
    elif query.data == "menu_admins":
        clear_user_state()
        admins = list_admins()
        admin_list = "\n".join([str(a) for a in admins]) or "No admins set."
        can_manage = user_id == SUPERADMIN_TELEGRAM_ID
        keyboard = []
        if can_manage:
            keyboard.append([InlineKeyboardButton("Add Admin", callback_data="add_admin")])
            if admins:
                keyboard.append([InlineKeyboardButton("Remove Admin", callback_data="remove_admin")])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="main_menu")])
        await query.edit_message_text(
            f"<b>Admins</b>\nCurrent admins:\n{admin_list}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif query.data == "add_admin":
        if user_id != SUPERADMIN_TELEGRAM_ID:
            await query.edit_message_text("Only the superadmin can add admins.")
            return
        context.user_data['add_admin'] = True
        await query.edit_message_text("Send the Telegram ID of the new admin:")
    elif query.data == "remove_admin":
        if user_id != SUPERADMIN_TELEGRAM_ID:
            await query.edit_message_text("Only the superadmin can remove admins.")
            return
        admins = list_admins()
        keyboard = [[InlineKeyboardButton(str(a), callback_data=f"del_admin_{a}")] for a in admins if str(a) != SUPERADMIN_TELEGRAM_ID]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu_admins")])
        await query.edit_message_text("Select an admin to remove:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data.startswith("del_admin_"):
        if user_id != SUPERADMIN_TELEGRAM_ID:
            await query.edit_message_text("Only the superadmin can remove admins.")
            return
        admin_id = query.data[len("del_admin_"):]
        remove_admin(admin_id)
        await query.edit_message_text("Admin removed.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="menu_admins")]]))
    # Gemini API Key flows
    elif query.data == "add_gemini_key":
        context.user_data['add_gemini_key'] = True
        await query.edit_message_text("Send the new Gemini API key:")
    elif query.data == "remove_gemini_key":
        keys = list_keys()
        if not keys:
            await query.edit_message_text("No Gemini keys to remove.")
            return
        keyboard = [[InlineKeyboardButton(f"{k['name']} ({k['region']})", callback_data=f"del_gemini_{k['id']}")] for k in keys]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu_gemini")])
        await query.edit_message_text("Select a Gemini key to remove:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "list_gemini_keys":
        keys = list_keys()
        if not keys:
            await query.edit_message_text("No Gemini API keys found.")
            return
        msg = "Gemini API Keys:\n" + "\n".join([f"{k['name']} ({k['region']}) - {'Active' if k['active'] else 'Inactive'}" for k in keys])
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="menu_gemini")]]))
    elif query.data.startswith("del_gemini_"):
        key_id = query.data[len("del_gemini_"):]
        remove_key(key_id)
        await query.edit_message_text("Gemini key removed.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="menu_gemini")]]))
    # User API Key flows
    elif query.data == "create_user_key":
        context.user_data['create_user_key'] = True
        await query.edit_message_text("Send a label for the new user API key (e.g. customer name or email):")
    elif query.data == "revoke_user_key":
        keys = list_user_api_keys()
        if not keys:
            await query.edit_message_text("No user API keys to revoke.")
            return
        keyboard = [[InlineKeyboardButton(f"{k['user_label']} ({k['key'][:6]}...) {'✅' if k['active'] else '❌'}", callback_data=f"del_user_{k['id']}")] for k in keys if k['active']]
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu_user")])
        await query.edit_message_text("Select a user API key to revoke:", reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data == "list_user_keys":
        keys = list_user_api_keys()
        if not keys:
            await query.edit_message_text("No user API keys found.")
            return
        msg = "User API Keys:\n" + "\n".join([f"{k['user_label']} ({k['key'][:6]}...) - {'Active' if k['active'] else 'Revoked'}" for k in keys])
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="menu_user")]]))
    elif query.data.startswith("del_user_"):
        key_id = query.data[len("del_user_"):]
        revoke_user_api_key(key_id)
        await query.edit_message_text("User API key revoked.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="menu_user")]]))
    elif query.data == "create_bot":
        context.user_data['create_bot'] = True
        context.user_data['bot_creation'] = {}
        await query.edit_message_text("Send the bot name:")
    elif query.data == "list_bots":
        bots = list_bots()
        if not bots:
            msg = "No bots registered."
        else:
            msg = "<b>Registered Bots</b>\n" + "\n".join([f"{b['name']} ({b['status']})" for b in bots])
        await query.edit_message_text(msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="menu_bots")]]))
    elif query.data == "update_server":
        if user_id != SUPERADMIN_TELEGRAM_ID:
            await query.edit_message_text("Only the owner can update the server.")
            return
        await query.edit_message_text("Updating server... This may take a minute.")
        try:
            # Pull latest code
            subprocess.run(["git", "pull", "origin", "main"], check=True)
            # Update dependencies
            subprocess.run([".venv/bin/pip", "install", "-r", "requirements.txt"], check=True)
            # Restart all services
            subprocess.run(["sudo", "systemctl", "restart", "ggpt-backend"], check=True)
            subprocess.run(["sudo", "systemctl", "restart", "ggpt-telegram-bot"], check=True)
            subprocess.run(["sudo", "systemctl", "restart", "ggpt-rq-worker"], check=True)
            await query.edit_message_text("✅ Server updated and all services restarted.")
        except Exception as e:
            await query.edit_message_text(f"❌ Update failed: {e}")

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not (is_admin(user_id) or user_id == str(SUPERADMIN_TELEGRAM_ID)):
        return
    if context.user_data.get('add_gemini_key'):
        try:
            api_key = update.message.text.strip()
            existing_keys = list_keys()
            name = f"gemini_key{len(existing_keys) + 1}"
            region = "global"
            add_key(name, region, api_key)
            await update.message.reply_text(f"Gemini API key added as {name}.")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}\nJust send the API key.")
        context.user_data['add_gemini_key'] = False
        await start(update, context)
    elif context.user_data.get('create_user_key'):
        try:
            user_label = update.message.text.strip()
            api_key = create_user_api_key(user_label)
            if api_key:
                await update.message.reply_text(f"User API key created for '{user_label}':\n{api_key}")
            else:
                await update.message.reply_text("Failed to create user API key.")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")
        context.user_data['create_user_key'] = False
        await start(update, context)
    elif context.user_data.get('add_admin'):
        if user_id != SUPERADMIN_TELEGRAM_ID:
            await update.message.reply_text("Only the superadmin can add admins.")
            return
        try:
            new_admin_id = update.message.text.strip()
            add_admin(new_admin_id)
            await update.message.reply_text(f"Admin {new_admin_id} added.")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")
        context.user_data['add_admin'] = False
        await start(update, context)
    elif context.user_data.get('create_bot'):
        bot_creation = context.user_data.get('bot_creation', {})
        if 'name' not in bot_creation:
            bot_creation['name'] = update.message.text.strip()
            context.user_data['bot_creation'] = bot_creation
            await update.message.reply_text("Send the bot token:")
        elif 'token' not in bot_creation:
            bot_creation['token'] = update.message.text.strip()
            context.user_data['bot_creation'] = bot_creation
            await update.message.reply_text("(Optional) Send a base prompt for the bot, or type 'skip' to leave blank:")
        else:
            base_prompt = update.message.text.strip()
            if base_prompt.lower() == 'skip':
                base_prompt = None
            bot_creation['base_prompt'] = base_prompt
            res, api_key = create_bot(bot_creation['name'], bot_creation['token'], base_prompt)
            # Get the new bot's id
            bot_id = res.data[0]['id'] if hasattr(res, 'data') and res.data else None
            await update.message.reply_text(f"Bot '{bot_creation['name']}' registered.\nAPI Key: {api_key}\nDeploying bot...")
            # Deploy the bot as a systemd service
            if bot_id:
                try:
                    subprocess.run([
                        './setup/deploy_new_bot.sh',
                        bot_creation['name'],
                        bot_creation['token'],
                        bot_id
                    ], check=True)
                    await update.message.reply_text(f"Bot '{bot_creation['name']}' deployed and running.")
                except Exception as e:
                    await update.message.reply_text(f"Bot registered, but deployment failed: {e}")
            else:
                await update.message.reply_text("Bot registered, but could not retrieve bot ID for deployment.")
            context.user_data['create_bot'] = False
            context.user_data['bot_creation'] = {}
            await start(update, context)

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling() 
