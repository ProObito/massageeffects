# +++ Made By Obito [@i_killed_my_clan] +++

import random
import string
import asyncio
import aiohttp
import requests
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from bot import Bot
from config import SHORT_API, SHORT_URL, OWNER_ID
from database.database import obito
from helper_func import is_admin, is_banned

# Master Control States System
SHORTENER_STATE = {}
ADMIN_SETUP_STATE = {}

# ==================== 1. LEGACY UTILITIES ====================

def generate_random_alphanumeric():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(8))

def get_short(url):
    try:
        rget = requests.get(f"https://{SHORT_URL}/api?api={SHORT_API}&url={url}&alias={generate_random_alphanumeric()}")
        rjson = rget.json()
        if rjson.get("status") == "success" or rget.status_code == 200:
            return rjson["shortenedUrl"]
        else:
            return url
    except Exception:
        return url

async def get_dynamic_short_url(long_url: str) -> str:
    slots_active = []
    for i in range(1, 6):
        data = await obito.get_slot_settings(i)
        if data.get('url') and data.get('api'):
            slots_active.append(data)
            
    if not slots_active:
        settings = await obito.get_shortener_settings()
        url = settings.get('url')
        api = settings.get('api')
        if not url or not api:
            return get_short(long_url)
        slots_active.append({'url': url, 'api': api})
        
    node = slots_active[0]
    api_endpoint = f"https://{node['url']}/api?api={node['api']}&url={long_url}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_endpoint) as response:
                if response.status == 200:
                    res_data = await response.json()
                    if "shortenedUrl" in res_data:
                        return res_data["shortenedUrl"]
                    elif "link" in res_data:
                        return res_data["link"]
    except Exception:
        pass
    return long_url

async def get_shortener_keyboard():
    settings = await obito.get_shortener_settings()
    url = settings.get('url') or "Not Set ❌"
    mode = settings.get('mode') or "Token Mode"
    
    text = (
        f"🛠 <b>Sʜ6ʀᴛᴇɴᴇʀ C6ɴғɪɢᴜʀ6ᴛɪ6ɴ P6ɴᴇʟ</b>\n\n"
        f"🔗 <b>Global URL:</b> <code>{url}</code>\n"
        f"⚙️ <b>Moᴅᴇ:</b> <code>{mode}</code>\n\n"
        f"💬 <b>5-Sʟ6ᴛ R6ᴛ6ᴛɪ6ɴ Sᴛ6ᴛᴜs:</b>\n"
    )
    
    buttons = [
        [
            InlineKeyboardButton("➕ Add / Change Global", callback_data="set_short"),
            InlineKeyboardButton("🗑 Remove Global", callback_data="del_short")
        ]
    ]
    
    for i in range(1, 6):
        data = await obito.get_slot_settings(i)
        slot_status = f"<code>{data.get('url')}</code>" if data.get('url') else "<i>Not Set ❌</i>"
        text += f"▫️ <b>Slot {i}:</b> {slot_status}\n"
        
        buttons.append([
            InlineKeyboardButton(f"⚙️ Config Slot {i}", callback_data=f"manage_slot_{i}"),
            InlineKeyboardButton(f"🗑 Wipe {i}", callback_data=f"wipe_slot_{i}")
        ])
        
    text += f"\n⚙️ <b>BACKUP TEXT COMMANDS:</b>\n" \
            f"• <code>/setslot [1-5] domain | api</code>\n" \
            f"• <code>/wipeslot [1-5]</code>\n" \
            f"• <code>/checkslots</code>\n\n" \
            f"<blockquote>💡 Tip: Users rotate smoothly from Slot 1 to 5 dynamically.</blockquote>"
    
    buttons.append([InlineKeyboardButton(f"🔄 Mode: {mode}", callback_data=f"toggle_mode_{mode.replace(' ', '_')}")])
    buttons.append([InlineKeyboardButton("✖️ Close Menu", callback_data="close")])
    return text, InlineKeyboardMarkup(buttons)

# ==================== 2. TEXT SHORTCUT COMMAND HANDLERS ====================

@Bot.on_message(filters.command('shorten') & filters.private & is_admin)
async def shorten_dashboard_cmd(client: Client, message: Message):
    text, reply_markup = await get_shortener_keyboard()
    await message.reply_text(text, reply_markup=reply_markup)

@Bot.on_message(filters.command('checkslots') & filters.private & is_admin)
async def check_slots_text_cmd(client: Client, message: Message):
    text, _ = await get_shortener_keyboard()
    await message.reply_text(text)

@Bot.on_message(filters.command('wipeslot') & filters.private & is_admin)
async def wipeslot_text_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ <b>Usage:</b> <code>/wipeslot [1-5]</code>")
    
    slot_str = message.command[1]
    if not slot_str.isdigit() or not (1 <= int(slot_str) <= 5):
        return await message.reply_text("❌ <b>Error:</b> Slot number must be between 1 and 5.")
        
    slot_id = int(slot_str)
    await obito.remove_slot_settings(slot_id)
    await message.reply_text(f"✅ <b>Slot {slot_id} data completely wiped out!</b>")

@Bot.on_message(filters.command('setslot') & filters.private & is_admin)
async def setslot_text_cmd(client: Client, message: Message):
    if len(message.command) < 3:
        return await message.reply_text("❌ <b>Usage:</b> <code>/setslot [1-5] shortener_domain.com | api_key_here</code>")
        
    slot_str = message.command[1]
    if not slot_str.isdigit() or not (1 <= int(slot_str) <= 5):
        return await message.reply_text("❌ <b>Error:</b> Slot number must be between 1 and 5.")
        
    slot_id = int(slot_str)
    raw_payload = " ".join(message.command[2:])
    
    if " | " not in raw_payload:
        return await message.reply_text("❌ <b>Invalid format!</b> Use <code>|</code> divider to separate domain and api key.")
        
    try:
        url_part, api_part = raw_payload.split(" | ", 1)
        url_clean = url_part.strip().replace("https://", "").replace("http://", "").strip("/")
        api_clean = api_part.strip()
        
        await obito.update_slot_settings(slot_id, url_clean, api_clean)
        await message.reply_text(f"✅ <b>Slot {slot_id} configured successfully!</b>\n\n🌐 <b>Domain:</b> <code>{url_clean}</code>")
    except Exception as e:
        await message.reply_text(f"❌ <b>Error processing variables:</b> <code>{e}</code>")

# ==================== 3. COMPLETE INTERACTIVE CALLBACKS ====================

@Bot.on_callback_query(filters.regex(r"^(set_short|del_short|toggle_mode_|manage_slot_|wipe_slot_|abort_setup)"))
async def shortener_callback_handler(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    if not await is_admin(None, client, callback_query.message):
        return await callback_query.answer("⚠️ Only Bot Admins can control settings!", show_alert=True)

    if data == "del_short":
        await obito.remove_shortener()
        await callback_query.answer("🗑 Shortener settings wiped out!", show_alert=True)
        text, markup = await get_shortener_keyboard()
        return await callback_query.message.edit_text(text, reply_markup=markup)

    elif data.startswith("toggle_mode_"):
        current_raw = data.split("toggle_mode_")[1].replace("_", " ")
        await obito.toggle_shortener_mode(current_raw)
        await callback_query.answer("🔄 Shortener mode updated!")
        text, markup = await get_shortener_keyboard()
        return await callback_query.message.edit_text(text, reply_markup=markup)

    elif data == "set_short":
        SHORTENER_STATE[user_id] = True
        cancel_markup = InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Cancel Process", callback_data="cancel_short")]])
        await callback_query.message.edit_text(
            "📥 <b>Please send Shortener URL and API Key together.</b>\n\n"
            "<b>Format:</b> <code>shortener_domain.com | api_key_here</code>\n\n"
            "⚠️ <i>bot still waiting for your reply...</i>",
            reply_markup=cancel_markup
        )
        await callback_query.answer()

    elif data == "abort_setup":
        ADMIN_SETUP_STATE.pop(user_id, None)
        await callback_query.answer("❌ Slot Setup Cancelled!")
        text, markup = await get_shortener_keyboard()
        return await callback_query.message.edit_text(text, reply_markup=markup)

    elif data.startswith("wipe_slot_"):
        slot_id = int(data.split("wipe_slot_")[1])
        await obito.remove_slot_settings(slot_id)
        await callback_query.answer(f"🗑 Slot {slot_id} data cleared!", show_alert=True)
        text, markup = await get_shortener_keyboard()
        return await callback_query.message.edit_text(text, reply_markup=markup)

    elif data.startswith("manage_slot_"):
        slot_id = int(data.split("manage_slot_")[1])
        ADMIN_SETUP_STATE[user_id] = {"slot": slot_id, "step": "url"}
        await callback_query.answer("⚙️ Starting Slot Configuration...")
        
        await callback_query.message.edit_text(
            text=f"📥 <b>[Slot {slot_id} Configuration] - Step 1:</b>\n\n"
                 f"Please send the shortener <b>Domain URL</b> now.\n\n"
                 f"ℹ️ <i>Example: <code>gplinks.co</code> or <code>droplink.co</code></i>\n\n"
                 f"💬 <i>Send /cancel to terminate this process anytime.</i>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Cancel Process", callback_data="abort_setup")]])
        )

@Bot.on_callback_query(filters.regex("cancel_short"))
async def cancel_shortener_state(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    SHORTENER_STATE.pop(user_id, None)
    await callback_query.answer("Process Cancelled ✖️")
    text, markup = await get_shortener_keyboard()
    await callback_query.message.edit_text(text, reply_markup=markup)

# ==================== 4. STEP-BY-STEP INPUT TEXT INTERCEPTORS ====================

async def check_active_shorten_state(_, __, message: Message):
    if not message.from_user:
        return False
    return message.from_user.id in ADMIN_SETUP_STATE

@Bot.on_message(filters.private & filters.text & filters.create(check_active_shorten_state), group=-2)
async def process_shortener_input_steps(client: Client, message: Message):
    user_id = message.from_user.id
    input_text = message.text.strip()
    
    session = ADMIN_SETUP_STATE[user_id]
    slot_id = session["slot"]
    step = session["step"]
    
    if input_text.lower() == "/cancel":
        ADMIN_SETUP_STATE.pop(user_id, None)
        text, markup = await get_shortener_keyboard()
        await message.reply_text("✅ Setup canceled. Returned to dashboard panel.", reply_markup=markup)
        message.stop_propagation()
        return

    if step == "url":
        clean_url = input_text.replace("https://", "").replace("http://", "").strip("/")
        ADMIN_SETUP_STATE[user_id]["url"] = clean_url
        ADMIN_SETUP_STATE[user_id]["step"] = "api"
        
        await message.reply_text(
            f"📥 <b>[Slot {slot_id} Configuration] - Step 2:</b>\n\n"
            f"Domain recorded: <code>{clean_url}</code>\n"
            f"Now please send the corresponding <b>API Key token</b> string for this slot platform.\n\n"
            f"💬 <i>Send /cancel to terminate this process anytime.</i>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Cancel Process", callback_data="abort_setup")]])
        )
        message.stop_propagation()
        return
        
    elif step == "api":
        saved_url = session["url"]
        ADMIN_SETUP_STATE.pop(user_id, None)
        
        await obito.update_slot_settings(slot_id, saved_url, input_text)
        
        text, markup = await get_shortener_keyboard()
        await message.reply_text(
            f"✅ <b>Slot {slot_id} successfully linked and updated into rotation records!</b>",
            reply_markup=markup
        )
        message.stop_propagation()
        return

@Bot.on_message(filters.private & filters.text & ~filters.command([]), group=-1)
async def capture_shortener_input(client: Client, message: Message):
    user_id = message.from_user.id
    
    if not SHORTENER_STATE.get(user_id):
        return 

    SHORTENER_STATE.pop(user_id, None)
    
    if " | " not in message.text:
        await message.reply_text(
            "❌ <b>Invalid format! Processing aborted.</b>\n\n"
            "Run <code>/shorten</code> again to configure.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Restart Dashboard", callback_data="cancel_short")]])
        )
        message.stop_propagation()
        return
    
    try:
        url_part, api_part = message.text.split(" | ", 1)
        url_clean = url_part.strip().replace("https://", "").replace("http://", "").strip("/")
        api_clean = api_part.strip()
        
        await obito.update_shortener(url_clean, api_clean)
        
        text, markup = await get_shortener_keyboard()
        await message.reply_text("✅ <b>Shortener settings updated successfully!</b>", reply_markup=markup)
        
    except Exception as e:
        await message.reply_text(f"❌ <b>Internal Error:</b> <code>{e}</code>")
        
    message.stop_propagation()
        
