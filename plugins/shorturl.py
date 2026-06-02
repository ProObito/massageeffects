import random
import string
import asyncio
import aiohttp
import requests
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import SHORT_API, SHORT_URL
from database.database import obito
from helper_func import is_admin

# State tracker dictionary
SHORTENER_STATE = {}

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
    settings = await obito.get_shortener_settings()
    url = settings.get('url')
    api = settings.get('api')
    
    if not url or not api:
        return get_short(long_url)
        
    api_endpoint = f"https://{url}/api?api={api}&url={long_url}"
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
        f"🔗 <b>URL:</b> <code>{url}</code>\n"
        f"⚙️ <b>Moᴅᴇ:</b> <code>{mode}</code>\n\n"
        f"<blockquote>💡 <i>Tip: 1-Time Mode transfers users instantly, Token Mode gives 24h keys.</i></blockquote>"
    )
    
    buttons = [
        [
            InlineKeyboardButton("➕ Add / Change ", callback_data="set_short"),
            InlineKeyboardButton("🗑 Remove ", callback_data="del_short")
        ],
        [
            InlineKeyboardButton(f"🔄 Mode: {mode}", callback_data=f"toggle_mode_{mode.replace(' ', '_')}")
        ],
        [
            InlineKeyboardButton("✖️ Close", callback_data="close")
        ]
    ]
    return text, InlineKeyboardMarkup(buttons)

@Client.on_message(filters.command('shorten') & filters.private & is_admin)
async def shorten_dashboard_cmd(client: Client, message: Message):
    text, reply_markup = await get_shortener_keyboard()
    await message.reply_text(text, reply_markup=reply_markup)

@Client.on_callback_query(filters.regex(r"^(set_short|del_short|toggle_mode_)"))
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

@Client.on_callback_query(filters.regex("cancel_short"))
async def cancel_shortener_state(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    SHORTENER_STATE.pop(user_id, None)
    await callback_query.answer("Process Cancelled ✖️")
    text, markup = await get_shortener_keyboard()
    await callback_query.message.edit_text(text, reply_markup=markup)

# High priority interceptor (group=-1) taaki channel_post se pehle trigger ho
@Client.on_message(filters.private & filters.text & ~filters.command([]), group=-1)
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
        message.stop_propagation() # Yahin rok do, link_post par nahi jayega
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
