# +++ Made By Obito [@i_killed_my_clan] +++

import asyncio
from pyrogram import filters, Client
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

from bot import Bot
from config import ADMINS, CHANNEL_ID, DISABLE_CHANNEL_BUTTON
from helper_func import encode

# Global commands list jise skip karna hai jab admins normal content forward karein
command_list = [
    'start', 'users', 'broadcast', 'batch', 'flink', 'genlink', 'help', 'cmd', 
    'info', 'add_fsub', 'fsub_chnl', 'restart', 'del_fsub', 'add_admins', 
    'del_admins', 'admin_list', 'cancel', 'auto_del', 'forcesub', 'files', 
    'add_banuser', 'del_banuser', 'banuser_list', 'status', 'req_fsub',
    'add_premium', 'commands', 'help_cmd', 'remove_premium', 'list_premium', 'my_plan', 'shorten', 'premium'
]

@Bot.on_message(filters.private & filters.user(ADMINS) & ~filters.command(command_list))
async def channel_post(client: Client, message: Message):
    reply_text = await message.reply_text("Please Wait...!", quote = True)
    try:
        post_message = await message.copy(chat_id = client.db_channel.id, disable_notification=True)
    except FloodWait as e:
        await asyncio.sleep(e.x)
        post_message = await message.copy(chat_id = client.db_channel.id, disable_notification=True)
    except Exception as e:
        print(e)
        await reply_text.edit_text("Something went Wrong..!")
        return
        
    converted_id = post_message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.me.username}?start={base64_string}"

    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("📫 ʏᴏᴜʀ ᴜʀʟ", url=f'https://telegram.me/share/url?url={link}')]])

    await reply_text.edit(f"<b>Here is your link</b>\n\n{link}", reply_markup=reply_markup, disable_web_page_preview = True)

    if not DISABLE_CHANNEL_BUTTON:
        try:
            await post_message.edit_reply_markup(reply_markup)
        except Exception:
            pass

@Bot.on_message(filters.channel & filters.incoming & filters.chat(CHANNEL_ID))
async def new_post(client: Client, message: Message):

    if DISABLE_CHANNEL_BUTTON:
        return

    converted_id = message.id * abs(client.db_channel.id)
    string = f"get-{converted_id}"
    base64_string = await encode(string)
    link = f"https://t.me/{client.me.username}?start={base64_string}"
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("📫 ʏᴏᴜʀ ᴜʀʟ", url=f'https://telegram.me/share/url?url={link}')]])
    try:
        await message.edit_reply_markup(reply_markup)
    except Exception as e:
        print(e)
        pass
        
