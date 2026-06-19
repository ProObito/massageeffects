import os
import asyncio
import re
from pyrogram import Client, filters, __version__
from pyrogram.enums import ParseMode, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated

from bot import Bot
from config import ADMINS, FORCE_MSG, OWNER_ID, START_MSG, CUSTOM_CAPTION, DISABLE_CHANNEL_BUTTON, PROTECT_CONTENT, START_PIC, FORCE_PIC, SHORT_MSG, DEL_MSG
from helper_func import subscribed, encode, decode, get_messages, is_banned, is_admin
from database.database import obito
from plugins.shorturl import get_dynamic_short_url
from plugins.autodel import convert_time  

# ==================== DYNAMIC AUTO DELETE WORKERS ====================

async def delete_message(msg, delay_time):
    if await obito.get_auto_delete(): 
        await asyncio.sleep(delay_time)    
        try:
            await msg.delete()
        except Exception:
            pass

async def auto_del_notification(client, msg, delay_time):
    if await obito.get_auto_delete():  
        try:
            readable_time = convert_time(delay_time)
            reply = await msg.reply_text(DEL_MSG.format(time=readable_time), disable_web_page_preview=True) 
            await asyncio.sleep(delay_time)
            try:
                await reply.delete()
            except Exception:
                pass
            try:
                await msg.delete()
            except Exception:
                pass
        except Exception:
            pass

# ==================== MAIN CORE LOGIC DIRECT HANDLER ====================

@Bot.on_message(filters.command('start') & filters.private & ~is_banned & subscribed)
async def start_command(client: Client, message: Message):
    user_id = message.from_user.id
    try:
        if not await obito.present_user(user_id):
            await obito.add_user(user_id)
    except Exception as e:
        print(f"Error adding user: {e}")

    text = message.text

    if len(text) > 7:
        try:
            basic = text.split(" ", 1)[1]
            if basic.startswith("yu3elk"):
                base64_string = basic[6:-1]
            else:
                base64_string = text.split(" ", 1)[1]
        except Exception as e:
            print(f"Error processing message: {e}")
            return

        is_user_premium = await obito.is_premium(user_id)
        if not is_user_premium and user_id != int(OWNER_ID) and not basic.startswith("yu3elk"):
            await short_url(client, message, base64_string)
            return

        string = await decode(base64_string)
        argument = string.split("-")
        if len(argument) == 3:
            try:
                start = int(int(argument[1]) / abs(client.db_channel.id))
                end = int(int(argument[2]) / abs(client.db_channel.id))
            except Exception as e:
                print(f"Error calculating start/end: {e}")
                return
            if start <= end:
                ids = range(start, end + 1)
            else:
                ids = []
                i = start
                while True:
                    ids.append(i)
                    i -= 1
                    if i < end:
                        break
        elif len(argument) == 2:
            try:
                ids = [int(int(argument[1]) / abs(client.db_channel.id))]
            except Exception as e:
                print(f"Error processing argument: {e}")
                return
                
        temp_msg = await message.reply("Please wait...")
        try:
            messages = await get_messages(client, ids)
        except Exception as e:
            print(f"Error getting messages: {e}")
            await message.reply_text("Something went wrong..!")
            return
        await temp_msg.delete()

        db_del_timer = await obito.get_del_timer()
        is_autodel_active = await obito.get_auto_delete()

        last_message = None
        for idx, msg in enumerate(messages):
            if bool(CUSTOM_CAPTION) & bool(msg.document):
                caption = CUSTOM_CAPTION.format(previouscaption="" if not msg.caption else msg.caption.html,
                                                filename=msg.document.file_name)
            else:
                caption = "" if not msg.caption else msg.caption.html

            if DISABLE_CHANNEL_BUTTON:
                reply_markup = msg.reply_markup
            else:
                reply_markup = None

            try:
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML,
                               reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                await asyncio.sleep(0.5)
                
                asyncio.create_task(delete_message(copied_msg, db_del_timer))
                if idx == len(messages) - 1:
                    last_message = copied_msg
            except FloodWait as e:
                await asyncio.sleep(e.x)
                copied_msg = await msg.copy(chat_id=message.from_user.id, caption=caption, parse_mode=ParseMode.HTML,
                               reply_markup=reply_markup, protect_content=PROTECT_CONTENT)
                await asyncio.sleep(0.5)
                asyncio.create_task(delete_message(copied_msg, db_del_timer))
                if idx == len(messages) - 1:
                    last_message = copied_msg
            except Exception as e:
                print(f"Error copying message: {e}")

        if is_autodel_active and last_message:
            asyncio.create_task(auto_del_notification(client, last_message, db_del_timer))
        return
    else:
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("• ʜᴇʟᴘ", callback_data='help'),
             InlineKeyboardButton("ᴀʙᴏᴜᴛ •", callback_data='about')],
            [InlineKeyboardButton("• ᴄʟᴏsᴇ •", callback_data='close')]
        ])
        try:
            await message.reply_photo(
                photo=START_PIC,
                caption=START_MSG.format(
                    first=message.from_user.first_name,
                    last=message.from_user.last_name,
                    username=None if not message.from_user.username else '@' + message.from_user.username,
                    mention=message.from_user.mention,
                    id=message.from_user.id
                ),
                reply_markup=reply_markup,
            )
        except Exception as e:
            print(f"Error replying to message: {e}")
        return

#=====================================================================================##
WAIT_MSG = "<b>Working....</b>"
REPLY_ERROR = "<code>Use this command as a reply to any telegram message without any spaces.</code>"
#=====================================================================================##

async def short_url(client: Client, message: Message, base64_string):
    try:
        prem_link = f"https://t.me/{client.me.username}?start=yu3elk{base64_string}7"
        short_link = await get_dynamic_short_url(prem_link)

        buttons = [
            [
                InlineKeyboardButton(text="Click to download your file", url=short_link)
            ],
            [
                InlineKeyboardButton(text="How to Open", url="https://t.me/AnimeInHindi094/1066"),
                InlineKeyboardButton(text="Premium", url="https://t.me/+lZ_rLJwBKnllODY1")
            ]
        ]

        await message.reply_photo(
            photo=START_PIC,
            caption=SHORT_MSG.format(total_count="N/A"),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
    except Exception:
        pass

@Bot.on_message(filters.command('start') & filters.private & ~is_banned)
async def not_joined(client: Client, message: Message):
    channels = await obito.get_all_channels()
    buttons = []
    
    temp_row = []
    for idx, ch_id in enumerate(channels, start=1):
        try:
            chat_info = await client.get_chat(ch_id)
            invite_link = chat_info.invite_link or f"https://t.me/AnimeInHindi094"
            temp_row.append(InlineKeyboardButton(text=f"Channel {idx}", url=invite_link))
            if len(temp_row) == 2:
                buttons.append(temp_row)
                temp_row = []
        except Exception:
            continue
            
    if temp_row:
        buttons.append(temp_row)

    try:
        start_param = message.text.split(" ", 1)[1]
        buttons.append([InlineKeyboardButton(text='Try Again 🔄', url=f"https://t.me/{client.me.username}?start={start_param}")])
    except IndexError:
        # FIXED: Changed lowercase {true} variable into a valid "True" python payload string to resolve crashes
        buttons.append([InlineKeyboardButton(text='Try Again 🔄', url=f"https://t.me/{client.me.username}?start=True")])

    await message.reply_photo(
        photo=FORCE_PIC,
        caption=FORCE_MSG.format(
            first=message.from_user.first_name,
            last=message.from_user.last_name,
            username=None if not message.from_user.username else '@' + message.from_user.username,
            mention=message.from_user.mention,
            id=message.from_user.id
        ),
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Bot.on_message(filters.command('request') & filters.private & ~is_banned)
async def request_command(client: Client, message: Message):
    user_id = message.from_user.id

    if not await obito.is_premium(user_id):
        await message.reply("You are not a premium user. Upgrade to premium to access this feature.")
        return

    if len(message.command) < 2:
        await message.reply("Send me your request in this format: /request your_request_here")
        return

    requested = " ".join(message.command[1:])
    owner_message = f"{message.from_user.first_name} ({message.from_user.id})\n\nRequest: {requested}"
    await client.send_message(int(OWNER_ID), owner_message)
    await message.reply("Thanks for your request! Your request will be reviewed soon. Please wait.")

@Bot.on_message(filters.command('users') & filters.private & filters.user(int(OWNER_ID)))
async def get_users(client: Client, message: Message):
    msg = await message.reply(text=WAIT_MSG)
    users = await obito.full_userbase()
    await msg.edit(f"{len(users)} users are using this bot")


# ==================== ADVANCED TIMER & PIN BROADCAST SYSTEM ====================

def parse_broadcast_timer(time_str: str) -> int:
    if not time_str:
        return 0
    match = re.match(r"(\d+)([smhd])", time_str.lower())
    if not match:
        return 0
    value, unit = int(match.group(1)), match.group(2)
    if unit == 's': return value
    if unit == 'm': return value * 60
    if unit == 'h': return value * 3600
    if unit == 'd': return value * 86400
    return 0

async def scheduled_broadcast_deleter(client: Client, chat_id: int, message_id: int, delay: int):
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id=chat_id, message_ids=message_id)
    except Exception:
        pass

@Bot.on_message(filters.private & filters.command(['broadcast', 'pbroadcast']) & is_admin & ~is_banned)
async def advanced_broadcast_handler(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text(
            "<b>❌ Usage Error!</b>\n\n"
            "<blockquote>Reply to any message with:</blockquote>\n"
            "• <code>/broadcast [timer]</code> -> Normal delivery\n"
            "• <code>/pbroadcast [timer]</code> -> Deliver + Pin inside PM\n\n"
            "<b>Examples:</b>\n"
            "» <code>/pbroadcast 24h</code> (Auto delete in 24 hours)\n"
            "» <code>/broadcast 45m</code> (Auto delete in 45 minutes)\n"
            "» <code>/pbroadcast</code> (Permanent broadcast, no deletion)"
        )

    cmd_type = message.command[0].lower()
    should_pin = True if cmd_type == 'pbroadcast' else False
    
    timer_arg = message.command[1] if len(message.command) > 1 else None
    duration_seconds = parse_broadcast_timer(timer_arg)
    
    is_permanent = True if duration_seconds == 0 else False
    timer_readable = timer_arg.upper() if not is_permanent else "PERMANENT ♾"

    query = await obito.full_userbase()
    broadcast_msg = message.reply_to_message
    
    total = 0
    successful = 0
    blocked = 0
    deleted = 0
    unsuccessful = 0
    
    pls_wait = await message.reply(
        f"<b>🚀 Broadcast Initialization Started...</b>\n\n"
        f"⚙️ <b>Type:</b> <code>{cmd_type.upper()}</code>\n"
        f"⏱ <b>Lifespan:</b> <code>{timer_readable}</code>\n"
        f"⏳ <i>Please wait till system transfers blocks...</i>"
    )

    for chat_id in query:
        try:
            copied_msg = await broadcast_msg.copy(chat_id)
            successful += 1
            
            if should_pin:
                try:
                    await copied_msg.pin(disable_notification=True)
                except Exception:
                    pass
            
            if not is_permanent:
                asyncio.create_task(
                    scheduled_broadcast_deleter(
                        client=client, 
                        chat_id=chat_id, 
                        message_id=copied_msg.id, 
                        delay=duration_seconds
                    )
                )

        except FloodWait as e:
            await asyncio.sleep(e.x)
            try:
                copied_msg = await broadcast_msg.copy(chat_id)
                successful += 1
                if should_pin:
                    try: await copied_msg.pin(disable_notification=True)
                    except Exception: pass
                if not is_permanent:
                    asyncio.create_task(scheduled_broadcast_deleter(client, chat_id, copied_msg.id, duration_seconds))
            except Exception:
                unsuccessful += 1

        except UserIsBlocked:
            await obito.del_user(chat_id)
            blocked += 1
        except InputUserDeactivated:
            await obito.del_user(chat_id)
            deleted += 1
        except Exception:
            unsuccessful += 1
            pass
            
        total += 1
        await asyncio.sleep(0.05)
    
    status = f"""<b>📢 <u>BROADCAST COMPLETED!</u></b>

<blockquote>📊 <b>Stats Report:</b></blockquote>
• <b>Total Users DB:</b> <code>{total}</code>
• <b>Successful:</b> <code>{successful}</code>
• <b>Blocked Users Wiped:</b> <code>{blocked}</code>
• <b>Deleted Accounts Wiped:</b> <code>{deleted}</code>
• <b>Unsuccessful/Failed:</b> <code>{unsuccessful}</code>

⚙️ <b>Config Mode:</b> <code>{cmd_type.upper()}</code>
⏱ <b>Task Lifespan:</b> <code>{timer_readable}</code>
"""
    return await pls_wait.edit(status)
        
