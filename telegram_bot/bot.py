import os
import sys
import psutil
import subprocess
import tempfile
import requests
import base64


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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, use_edit=False):
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
        keyboard.append([InlineKeyboardButton("Restart Services", callback_data="restart_services")])
        keyboard.append([InlineKeyboardButton("Update & Restart", callback_data="update_and_restart")])
    text = "Welcome to the Gemini API Admin Panel. Choose an option:"
    if use_edit and hasattr(update, 'callback_query') and update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

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
        await start(update, context, use_edit=True)
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
        msg = "Gemini API Keys:\n" + "\n".join([
            f"{k['name']} ({k['region']}, {k.get('model_name', '?')}) - {'Active' if k['active'] else 'Inactive'}" for k in keys
        ])
        keyboard = []
        for k in keys:
            label = f"{k['name']} ({k['region']}, {k.get('model_name', '?')})"
            revoke_btn = InlineKeyboardButton("Revoke", callback_data=f"confirm_del_gemini_{k['id']}")
            keyboard.append([InlineKeyboardButton(label, callback_data="noop"), revoke_btn])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu_gemini")])
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data.startswith("confirm_del_gemini_"):
        key_id = query.data[len("confirm_del_gemini_"):]
        # Find key info for display
        keys = list_keys()
        k = next((x for x in keys if str(x['id']) == key_id), None)
        if not k:
            await query.edit_message_text("Key not found.")
            return
        label = f"{k['name']} ({k['region']}, {k.get('model_name', '?')})"
        keyboard = [
            [InlineKeyboardButton("Confirm", callback_data=f"del_gemini_{key_id}"), InlineKeyboardButton("Back", callback_data="list_gemini_keys")]
        ]
        await query.edit_message_text(f"Are you sure you want to revoke this Gemini key?\n<b>{label}</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data.startswith("del_gemini_"):
        key_id = query.data[len("del_gemini_"):]
        remove_key(key_id)
        await query.edit_message_text("Gemini key revoked.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="list_gemini_keys")]]))
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
        msg = "User API Keys:\n" + "\n".join([
            f"{k['user_label']} ({k['key'][:6]}...) - {'Active' if k['active'] else 'Revoked'}" for k in keys
        ])
        keyboard = []
        for k in keys:
            label = f"{k['user_label']} ({k['key'][:6]}...)"
            revoke_btn = InlineKeyboardButton("Revoke", callback_data=f"confirm_del_user_{k['id']}")
            status = '✅' if k['active'] else '❌'
            keyboard.append([InlineKeyboardButton(f"{label} {status}", callback_data="noop"), revoke_btn])
        keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="menu_user")])
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data.startswith("confirm_del_user_"):
        key_id = query.data[len("confirm_del_user_"):]
        # Find key info for display
        keys = list_user_api_keys()
        k = next((x for x in keys if str(x['id']) == key_id), None)
        if not k:
            await query.edit_message_text("Key not found.")
            return
        label = f"{k['user_label']} ({k['key'][:6]}...)"
        keyboard = [
            [InlineKeyboardButton("Confirm", callback_data=f"del_user_{key_id}"), InlineKeyboardButton("Back", callback_data="list_user_keys")]
        ]
        await query.edit_message_text(f"Are you sure you want to revoke this user API key?\n<b>{label}</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
    elif query.data.startswith("del_user_"):
        key_id = query.data[len("del_user_"):]
        revoke_user_api_key(key_id)
        await query.edit_message_text("User API key revoked.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="list_user_keys")]]))
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
    elif query.data == "restart_services":
        if user_id != SUPERADMIN_TELEGRAM_ID:
            await query.edit_message_text("Only the owner can restart services.")
            return
        await query.edit_message_text("Restarting all services...")
        with tempfile.NamedTemporaryFile(delete=False, mode="w+b", suffix=".txt") as logf:
            try:
                for svc in ["ggpt-backend", "ggpt-telegram-bot", "ggpt-rq-worker"]:
                    proc = subprocess.run(["sudo", "systemctl", "restart", svc], stdout=logf, stderr=logf)
                logf.flush()
                await query.edit_message_text("✅ All services restarted. Sending log...")
            except Exception as e:
                logf.write(str(e).encode())
                logf.flush()
                await query.edit_message_text(f"❌ Failed to restart services: {e}\nSending log...")
            await context.bot.send_document(chat_id=query.message.chat_id, document=open(logf.name, "rb"), filename="restart_log.txt")
        os.unlink(logf.name)
    elif query.data == "update_and_restart":
        if user_id != SUPERADMIN_TELEGRAM_ID:
            await query.edit_message_text("Only the owner can update and restart.")
            return
        await query.edit_message_text("Updating code, installing dependencies, and restarting all services...")
        with tempfile.NamedTemporaryFile(delete=False, mode="w+b", suffix=".txt") as logf:
            try:
                proc = subprocess.run(["git", "pull", "origin", "main"], stdout=logf, stderr=logf)
                logf.flush()
                logf.seek(0)
                log_content = logf.read().decode(errors="ignore")
                if "Your local changes to the following files would be overwritten by merge" in log_content:
                    await query.edit_message_text(
                        "❌ Update failed: Uncommitted changes detected. Please commit or stash your changes, or use Force Update to discard them.",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("Force Update (Discard Local Changes)", callback_data="force_update_and_restart")],
                            [InlineKeyboardButton("⬅️ Back", callback_data="main_menu")]
                        ])
                    )
                    await context.bot.send_document(chat_id=query.message.chat_id, document=open(logf.name, "rb"), filename="update_log.txt")
                    os.unlink(logf.name)
                    return
                proc = subprocess.run([".venv/bin/pip", "install", "-r", "requirements.txt"], stdout=logf, stderr=logf)
                for svc in ["ggpt-backend", "ggpt-telegram-bot", "ggpt-rq-worker"]:
                    proc = subprocess.run(["sudo", "systemctl", "restart", svc], stdout=logf, stderr=logf)
                logf.flush()
                await query.edit_message_text("✅ Update complete. All services restarted. Sending log...")
                await context.bot.send_document(chat_id=query.message.chat_id, document=open(logf.name, "rb"), filename="update_log.txt")
                os.unlink(logf.name)
                # Show main menu automatically after successful update
                await start(update, context, use_edit=True)
                return
            except Exception as e:
                logf.write(str(e).encode())
                logf.flush()
                await query.edit_message_text(f"❌ Update or restart failed: {e}\nSending log...")
            await context.bot.send_document(chat_id=query.message.chat_id, document=open(logf.name, "rb"), filename="update_log.txt")
        os.unlink(logf.name)
        # Show main menu automatically
        await start(update, context, use_edit=True)
        return
    elif query.data == "force_update_and_restart":
        if user_id != SUPERADMIN_TELEGRAM_ID:
            await query.edit_message_text("Only the owner can force update and restart.")
            return
        await query.edit_message_text("Force updating: discarding local changes, pulling latest code, and restarting all services...")
        with tempfile.NamedTemporaryFile(delete=False, mode="w+b", suffix=".txt") as logf:
            try:
                proc = subprocess.run(["git", "reset", "--hard", "HEAD"], stdout=logf, stderr=logf)
                proc = subprocess.run(["git", "pull", "origin", "main"], stdout=logf, stderr=logf)
                proc = subprocess.run([".venv/bin/pip", "install", "-r", "requirements.txt"], stdout=logf, stderr=logf)
                for svc in ["ggpt-backend", "ggpt-telegram-bot", "ggpt-rq-worker"]:
                    proc = subprocess.run(["sudo", "systemctl", "restart", svc], stdout=logf, stderr=logf)
                logf.flush()
                await query.edit_message_text("✅ Force update complete. All services restarted. Sending log...")
            except Exception as e:
                logf.write(str(e).encode())
                logf.flush()
                await query.edit_message_text(f"❌ Force update or restart failed: {e}\nSending log...")
            await context.bot.send_document(chat_id=query.message.chat_id, document=open(logf.name, "rb"), filename="force_update_log.txt")
        os.unlink(logf.name)
        # Show main menu automatically
        await start(update, context, use_edit=True)
        return
    elif query.data and query.data.startswith("select_gemini_model|"):
        idx = int(query.data.split("|", 1)[1])
        models = context.user_data.get('pending_gemini_models', [])
        if idx < 0 or idx >= len(models):
            await query.edit_message_text("Model not found. Please try again.")
            return
        model = models[idx]
        # Show model details and Confirm/Back buttons
        details = f"<b>{model.get('displayName', model['name'])}</b>\n"
        details += f"<code>{model['name']}</code>\n\n"
        details += model.get('description', '') + "\n\n"
        details += f"Input tokens: {model.get('inputTokenLimit', '?')}\nOutput tokens: {model.get('outputTokenLimit', '?')}\n"
        details += f"Supported: {', '.join(model.get('supportedGenerationMethods', []))}"
        keyboard = [
            [InlineKeyboardButton("Confirm", callback_data=f"confirm_gemini_model|{idx}")],
            [InlineKeyboardButton("Back", callback_data="back_gemini_model_select")]
        ]
        await query.edit_message_text(details, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
        return
    if query.data and query.data.startswith("confirm_gemini_model|"):
        idx = int(query.data.split("|", 1)[1])
        api_key = context.user_data.get('pending_gemini_key')
        models = context.user_data.get('pending_gemini_models', [])
        if not api_key or idx < 0 or idx >= len(models):
            await query.edit_message_text("No API key in progress or model not found. Please try again.")
            return
        model = models[idx]
        existing_keys = list_keys()
        name = f"gemini_key{len(existing_keys) + 1}"
        region = "global"
        add_key(name, region, api_key, model['name'])
        await query.edit_message_text(f"✅ Gemini API key added as {name} with model {model['name']}.")
        context.user_data.pop('pending_gemini_key', None)
        context.user_data.pop('pending_gemini_models', None)
        context.user_data['add_gemini_key'] = False
        # Show main menu automatically
        await start(update, context, use_edit=True)
        return
    if query.data == "back_gemini_model_select":
        models = context.user_data.get('pending_gemini_models', [])
        keyboard = [[InlineKeyboardButton(m['displayName'], callback_data=f"select_gemini_model|{i}")] for i, m in enumerate(models)]
        await query.edit_message_text(
            "Select a Gemini model for this API key:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    elif query.data and query.data.startswith("test_user_api_key|"):
        api_key = query.data.split("|", 1)[1]
        context.user_data['test_chat_api_key'] = api_key
        await query.edit_message_text(
            "You are now in test chat mode for this API key.\nSend messages to test the key.\nSend /exc to exit chatbot mode.",
            reply_markup=None
        )
        return

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not (is_admin(user_id) or user_id == str(SUPERADMIN_TELEGRAM_ID)):
        return
    if context.user_data.get('add_gemini_key'):
        try:
            api_key = update.message.text.strip()
            if api_key.lower() == '/cancel':
                context.user_data['add_gemini_key'] = False
                context.user_data.pop('pending_gemini_key', None)
                await update.message.reply_text("❌ Gemini API key addition cancelled.")
                return
            # List available models for this key
            models_url = "https://generativelanguage.googleapis.com/v1/models"
            test_params = {"key": api_key}
            resp = requests.get(models_url, params=test_params, timeout=10)
            if resp.status_code != 200:
                await update.message.reply_text(f"❌ Invalid Gemini API key or quota exceeded. Status: {resp.status_code}\n{resp.text}\n\nPlease send a valid Gemini API key, or /cancel to stop.")
                context.user_data['add_gemini_key'] = True
                return
            all_models = resp.json().get("models", [])
            # Only show models that support generateContent and do NOT require image input
            def is_text_only(model):
                # If the model's input modalities include 'image', skip it
                # Some models may have 'inputModalities' or similar field
                if 'inputModalities' in model and 'image' in model['inputModalities']:
                    return False
                # Some models may have 'supportedGenerationMethods' only
                # If the model name or displayName contains 'vision', skip it
                if 'vision' in model.get('name', '').lower() or 'vision' in model.get('displayName', '').lower():
                    return False
                return 'generateContent' in model.get('supportedGenerationMethods', [])
            models = [m for m in all_models if is_text_only(m)]
            if not models:
                await update.message.reply_text("❌ No usable text-only models found for this API key.\nPlease send a valid Gemini API key, or /cancel to stop.")
                context.user_data['add_gemini_key'] = True
                return
            context.user_data['pending_gemini_key'] = api_key
            context.user_data['pending_gemini_models'] = models
            keyboard = [[InlineKeyboardButton(m['displayName'], callback_data=f"select_gemini_model|{i}")] for i, m in enumerate(models)]
            await update.message.reply_text(
                "Select a Gemini model for this API key:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            await update.message.reply_text(f"Error: {e}\nJust send the API key, or /cancel to stop.")
            context.user_data['add_gemini_key'] = True
        return
    elif context.user_data.get('create_user_key'):
        try:
            user_label = update.message.text.strip()
            api_key = create_user_api_key(user_label)
            if api_key:
                msg = f"User API key created for '<b>{user_label}</b>':\n<code>{api_key}</code>\n\nTap the button below to copy again or test the key."
                keyboard = [
                    [InlineKeyboardButton("Copy", callback_data=f"copy_user_api_key|{api_key}"),
                     InlineKeyboardButton("Test Chat", callback_data=f"test_user_api_key|{api_key}")]
                ]
                await update.message.reply_text(msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(keyboard))
            else:
                await update.message.reply_text("Failed to create user API key.")
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")
        context.user_data['create_user_key'] = False
        # Do not show main menu here; let user choose next action (copy/test chat)
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

    # Handler for Copy button
    if query.data and query.data.startswith("copy_user_api_key|"):
        api_key = query.data.split("|", 1)[1]
        msg = f"<code>{api_key}</code>\n\nLong press to copy."
        await query.answer("Key copied!", show_alert=False)
        await query.edit_message_text(msg, parse_mode='HTML', reply_markup=None)
        return

    # Chatbot mode handler
    if context.user_data.get('test_chat_api_key'):
        if update.message.text.strip() == '/exc':
            context.user_data.pop('test_chat_api_key', None)
            await update.message.reply_text("Exited chatbot mode.")
            await start(update, context)
            return
        # Send message to backend using the test API key
        api_key = context.user_data['test_chat_api_key']
        # Example: send to backend (replace with your actual backend call)
        try:
            resp = requests.post(
                "http://localhost:8000/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"messages": [{"role": "user", "content": update.message.text}]}
            )
            if resp.status_code == 200:
                data = resp.json()
                reply = data['choices'][0]['message']['content']
                await update.message.reply_text(reply)
            else:
                await update.message.reply_text(f"API error: {resp.text}")
        except Exception as e:
            await update.message.reply_text(f"Request failed: {e}")
        return

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop('add_gemini_key', None)
    context.user_data.pop('pending_gemini_key', None)
    await update.message.reply_text("❌ Gemini API key addition cancelled.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.run_polling() 
