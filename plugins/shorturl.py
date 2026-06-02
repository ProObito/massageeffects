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

# ==================== 1. EXISTING STATIC SHORTENER (UPAR KI SIDE) ====================

def generate_random_alphanumeric():
    """Generate a random 8-letter alphanumeric string."""
    characters = string.ascii_letters + string.digits
    random_chars = ''.join(random.choice(characters) for _ in range(8))
    return random_chars

def get_short(url):
    """Purana static config shortener logic code"""
    try:
        rget = requests.get(f"https://{SHORT_URL}/api?api={SHORT_API}&url={url}&alias={generate_random_alphanumeric()}")
        rjson = rget.json()
        if rjson.get("status") == "success" or rget.status_code == 200:
            return rjson["shortenedUrl"]
        else:
            return url
    except Exception:
        return url


# ==================== 2. NEW DYNAMIC INTERACTIVE SHORTENER LOGIC ====================

async def get_dynamic_short_url(long_url: str) -> str:
    """Database se settings read karke runtime link short karne wala system"""
    settings = await obito.get_shortener_settings()
    url = settings.get('url')
    api = settings.get('api')
    
    if not url or not api:
        # Agar bot par koi shortener set nahi hai, toh fallback karke config.py wala use karega
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


# ==================== 3. INLINE PANEL KEYBOARD LAYOUT ====================

async def get_shortener_keyboard():
    settings = await obito.get_shortener_settings()
    url = settings.get('url') or "Not Set ❌"
    mode = settings.get('mode') or "Token Mode"
    
    text = (
        f"🛠 **Sʜᴏʀᴛᴇɴᴇʀ C0ɴғɪɢᴜʀᴀᴛɪᴏɴ Pᴀɴᴇʟ**\n\n"
        f"🔗 **URL:** `{url}`\n"
        f"⚙️ **M0ᴅᴇ:** `{mode}`\n\n"
        f"💡 _Tip: 1-Time Mode transfers users instantly, Token Mode gives 24h access._"
    )
    
    buttons = [
        [
            InlineKeyboardButton("➕ Add / Change Shortener", callback_data="set_short"),
            InlineKeyboardButton("🗑 Remove Shortener", callback_data="del_short")
        ],
        [
            InlineKeyboardButton(f"🔄 Mode: {mode}", callback_data=f"toggle_mode_{mode.replace(' ', '_')}")
        ],
        [
            InlineKeyboardButton("✖️ Close Panel", callback_data="close")
        ]
    ]
    return text, InlineKeyboardMarkup(buttons)


# ==================== 4. COMMAND & CALLBACK HANDLERS ====================

@Client.on_message(filters.command('shorten') & filters.private & is_admin)
async def shorten_dashboard_cmd(client: Client, message: Message):
    text, reply_markup = await get_shortener_keyboard()
    await message.reply_text(text, reply_markup=reply_markup)


@Client.on_callback_query(filters.regex(r"^(set_short|del_short|toggle_mode_)"))
async def shortener_callback_handler(client: Client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    
    # Permission Validation
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
        await callback_query.answer("🔄 Shortener operational mode updated!")
        text, markup = await get_shortener_keyboard()
        return await callback_query.message.edit_text(text, reply_markup=markup)

    elif data == "set_short":
        await callback_query.message.delete()
        
        ask_msg = await client.send_message(
            chat_id=user_id,
            text="📥 **Please send Shortener URL and API Key together.**\n\n"
                 "**Format:** `shortener_domain.com | api_key_here`"
        )
        
        try:
            # Listening to user response text via pyromod
            response: Message = await client.listen.message(chat_id=user_id, filters=filters.text, timeout=60)
            if " | " not in response.text:
                return await response.reply_text("❌ **Invalid format! Action aborted.** Run `/shorten` again.")
            
            url_part, api_part = response.text.split(" | ", 1)
            url_clean = url_part.strip().replace("https://", "").replace("http://", "").strip("/")
            api_clean = api_part.strip()
            
            await obito.update_shortener(url_clean, api_clean)
            
            text, markup = await get_shortener_keyboard()
            await response.reply_text("✅ **Shortener configuration successfully saved!**", reply_markup=markup)
            
        except asyncio.TimeoutError:
            await client.send_message(chat_id=user_id, text="⚠️ **Timeout exceeded! Session expired.**")
        
