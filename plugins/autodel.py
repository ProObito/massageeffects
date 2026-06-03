# +++ Made By Obito [@i_killed_my_clan] +++

import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.enums import ChatAction
from datetime import datetime, timedelta

from bot import Bot
from config import OWNER_ID, START_PIC  
from database.database import obito
from helper_func import is_admin, is_banned

# Global state tracker to safely handle setting states across multiple workers
AUTODEL_STATE = {}

on_txt = "<code>ENABLED ✅</code>"
off_txt = "<code>DISABLED ❌</code>"
autodel_cmd_pic = START_PIC

AUTODEL_CMD_TXT = """
⚙️ <b>Auto Delete Configuration Panel</b>

◈ <b>Status:</b> {autodel_mode}
◈ <b>Current Timer:</b> <code>{timer}</code>

<blockquote>💡 <i>Tip: When enabled, files will be automatically deleted based on the set timer after being delivered to the user.</i></blockquote>
"""

DEL_MSG = """<b>⚠️ Due to Copyright issues....
<blockquote>Your files will be deleted within <a href="https://t.me/{username}">{time}</a>. So please forward them to any other place for future availability.</blockquote></b>"""

# ==================== 1. TIME CONVERSION UTILITIES ====================

def convert_time(duration_seconds: int) -> str:
    periods = [
        ('year', 60 * 60 * 24 * 365),
        ('month', 60 * 60 * 24 * 30),
        ('day', 60 * 60 * 24),
        ('hour', 60 * 60),
        ('minute', 60),
        ('second', 1)
    ]

    parts = []
    for period_name, period_seconds in periods:
        if duration_seconds >= period_seconds:
            num_periods = duration_seconds // period_seconds
            duration_seconds %= period_seconds
            parts.append(f"{num_periods} {period_name}{'s' if num_periods > 1 else ''}")

    if len(parts) == 0:
        return "0 seconds"
    elif len(parts) == 1:
        return parts[0]
    else:
        return ', '.join(parts[:-1]) + ' and ' + parts[-1]


# ==================== 2. BACKGROUND WORKER UTILITIES ====================

async def auto_del_notification(bot_username, msg, delay_time, transfer): 
    temp = await msg.reply_text(DEL_MSG.format(username=bot_username, time=convert_time(delay_time)), disable_web_page_preview=True) 

    await asyncio.sleep(delay_time)
    try:
        if transfer:
            try:
                name = "♻️ Click Here"
                link = f"https://t.me/{bot_username}?start={transfer}"
                button = [[InlineKeyboardButton(text=name, url=link), InlineKeyboardButton(text="Close ✖️", callback_data="close")]]

                await temp.edit_text(text=f"<b>Previous Message was Deleted 🗑\n<blockquote>If you want to get the files again, then click: [<a href={link}>{name}</a>] button below else close this message.</blockquote></b>", reply_markup=InlineKeyboardMarkup(button), disable_web_page_preview=True)
            except Exception as e:
                await temp.edit_text(f"<b><blockquote>Previous Message was Deleted 🗑</blockquote></b>")
                print(f"Error editing text: {e}")
        else:
            await temp.edit_text(f"<b><blockquote>Previous Message was Deleted 🗑</blockquote></b>")
    except Exception as e:
        print(f"Error editing text: {e}")

    try: 
        await msg.delete()
    except Exception: 
        pass


async def delete_message(msg, delay_time): 
    await asyncio.sleep(delay_time)
    try: 
        await msg.delete()
    except Exception: 
        pass


# ==================== 3. COMMAND & INTERACTIVE SETTINGS ====================

@Client.on_message(filters.command('auto_del') & filters.private & ~is_banned & is_admin)
async def autoDelete_settings(client: Client, message: Message):
    await message.reply_chat_action(ChatAction.TYPING)
    try:
        timer = convert_time(await obito.get_del_timer())
        is_enabled = await obito.get_auto_delete()
        
        autodel_mode = on_txt if is_enabled else off_txt
        mode = 'Disable Mode ❌' if is_enabled else 'Enable Mode ✅'
        
        await message.reply_photo(
            photo=autodel_cmd_pic,
            caption=AUTODEL_CMD_TXT.format(autodel_mode=autodel_mode, timer=timer),
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(mode, callback_data='chng_autodel'), InlineKeyboardButton('◈ Set Timer ⏱', callback_data='set_timer')],
                [InlineKeyboardButton('🔄 Refresh', callback_data='autodel_cmd'), InlineKeyboardButton('Close ✖️', callback_data='close')]
            ])
        )
    except Exception as e:
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("Close ✖️", callback_data="close")]])
        await message.reply(f"<b>! Error Occurred..\n<blockquote>Reason:</b> {e}</blockquote>", reply_markup=reply_markup)


# ==================== 4. CALLBACK PANEL INTERFACES ====================

@Client.on_callback_query(filters.regex(r"^(autodel_cmd|chng_autodel|set_timer)$"))
async def autodel_callbacks(client: Client, query: CallbackQuery):
    data = query.data
    user_id = query.from_user.id
    
    if user_id != int(OWNER_ID):
        return await query.answer("⚠️ Only the Bot Owner can change configuration variables!", show_alert=True)
        
    await query.answer("♻️ Processing....")
    timer_seconds = await obito.get_del_timer()
    timer_readable = convert_time(timer_seconds)

    if data == 'autodel_cmd':
        is_enabled = await obito.get_auto_delete()
        autodel_mode = on_txt if is_enabled else off_txt
        mode = 'Disable Mode ❌' if is_enabled else 'Enable Mode ✅'
        
        try:
            await query.edit_message_caption(
                caption=AUTODEL_CMD_TXT.format(autodel_mode=autodel_mode, timer=timer_readable),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(mode, callback_data='chng_autodel'), InlineKeyboardButton('◈ Set Timer ⏱', callback_data='set_timer')],
                    [InlineKeyboardButton('🔄 Refresh', callback_data='autodel_cmd'), InlineKeyboardButton('Close ✖️', callback_data='close')]
                ])
            )
        except Exception:
            pass

    elif data == 'chng_autodel':
        new_state = await obito.toggle_auto_delete()
        autodel_mode = on_txt if new_state else off_txt
        mode = 'Disable Mode ❌' if new_state else 'Enable Mode ✅'
        
        try:
            await query.edit_message_caption(
                caption=AUTODEL_CMD_TXT.format(autodel_mode=autodel_mode, timer=timer_readable),
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(mode, callback_data='chng_autodel'), InlineKeyboardButton('◈ Set Timer ⏱', callback_data='set_timer')],
                    [InlineKeyboardButton('🔄 Refresh', callback_data='autodel_cmd'), InlineKeyboardButton('Close ✖️', callback_data='close')]
                ])
            )
        except Exception:
            pass

    elif data == 'set_timer':
        AUTODEL_STATE[user_id] = query.message.id
        await query.message.delete()
        
        await client.send_message(
            chat_id=user_id,
            text=f"<b><blockquote>⏱ Current Timer: {timer_readable}</blockquote>\n\n"
                 "To change timer, please send a valid number in seconds.\n"
                 "<blockquote>Example: <code>300</code> (5m), <code>600</code> (10m), <code>3600</code> (1h)</blockquote></b>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Cancel Process", callback_data="autodel_cmd")]])
        )


# ==================== 5. TEXT INTERCEPTOR FOR TIMER INPUT (ULTRA SAFE) ====================

# Dynamic filter callback logic checking state parameters entry points instantly
async def check_active_autodel_state(_, __, message: Message):
    if not message.from_user:
        return False
    return message.from_user.id in AUTODEL_STATE

@Client.on_message(filters.private & filters.text & filters.create(check_active_autodel_state), group=1)
async def process_raw_timer_text(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Pop out state instantly to prevent message leakage
    AUTODEL_STATE.pop(user_id, None)
    input_text = message.text.strip()
    
    if not input_text.isdigit():
        await message.reply_text(
            "❌ <b>Invalid input format! Seconds values must be integers only.</b>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Try Again", callback_data="set_timer")]])
        )
        message.stop_propagation()
        return
        
    seconds_val = int(input_text)
    await obito.set_del_timer(seconds_val)
    
    timer_readable = convert_time(seconds_val)
    is_enabled = await obito.get_auto_delete()
    autodel_mode = on_txt if is_enabled else off_txt
    mode = 'Disable Mode ❌' if is_enabled else 'Enable Mode ✅'
    
    await message.reply_text(
        f"<b>Added Successfully ✅\n<blockquote>⏱ Current Timer Updated: {timer_readable}</blockquote></b>",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(mode, callback_data='chng_autodel'), InlineKeyboardButton('◈ Set Timer ⏱', callback_data='set_timer')],
            [InlineKeyboardButton('🔄 Dashboard Panel', callback_data='autodel_cmd')]
        ])
    )
    message.stop_propagation() # Breaks downstream operations ONLY when capturing input state configs
