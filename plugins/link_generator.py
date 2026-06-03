# +++ Made By Obito [@i_killed_my_clan] +++
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot import Bot
from helper_func import encode, get_message_id, is_admin, is_banned

# Global dictionary to track batch/genlink user steps safely across workers
GENLINK_STATE = {}

# Commands list to ignore inside our text interceptor
command_list = [
    'start', 'users', 'broadcast', 'pbroadcast', 'batch', 'flink', 'genlink', 'help', 'cmd', 
    'info', 'add_fsub', 'fsub_chnl', 'restart', 'del_fsub', 'add_admins', 
    'del_admins', 'admin_list', 'cancel', 'auto_del', 'forcesub', 'files', 
    'add_banuser', 'del_banuser', 'banuser_list', 'status', 'req_fsub',
    'add_premium', 'commands', 'help_cmd', 'remove_premium', 'list_premium', 'my_plan', 'shorten', 'premium'
]

# ==================== 1. TRIGGER COMMAND HANDLERS ====================

@Bot.on_message(filters.private & ~is_banned & is_admin & filters.command('batch'))
async def batch_command(client: Client, message: Message):
    user_id = message.from_user.id
    GENLINK_STATE[user_id] = {"mode": "batch", "step": 1, "first_id": None}
    
    await message.reply_text(
        "🚀 <b>Batch Mode Activated!</b>\n\n"
        "Please <b>FORWARD</b> the <b>FIRST</b> message from your DB Channel (with quotes), "
        "or paste the DB Channel post link directly.\n\n"
        "💬 <i>Send /cancel to terminate this process anytime.</i>"
    )

@Bot.on_message(filters.private & ~is_banned & is_admin & filters.command('genlink'))
async def genlink_command(client: Client, message: Message):
    user_id = message.from_user.id
    GENLINK_STATE[user_id] = {"mode": "single", "step": 1}
    
    await message.reply_text(
        "🚀 <b>Single Link Generator Activated!</b>\n\n"
        "Please <b>FORWARD</b> the target message from your DB Channel (with quotes), "
        "or paste the DB Channel post link directly.\n\n"
        "💬 <i>Send /cancel to terminate this process anytime.</i>"
    )

@Bot.on_message(filters.private & filters.command('cancel') & is_admin)
async def cancel_generator_session(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in GENLINK_STATE:
        GENLINK_STATE.pop(user_id, None)
        await message.reply_text("✅ <b>Link generation process canceled and reset.</b>")
    else:
        await message.reply_text("❌ <b>You do not have any active link generation tasks running.</b>")


# ==================== 2. SAFE TEXT & FORWARD INTERCEPTOR ====================

@Bot.on_message(filters.private & ~filters.command(command_list), group=1)
async def process_generator_inputs(client: Client, message: Message):
    user_id = message.from_user.id
    
    if user_id not in GENLINK_STATE:
        return  # Fall through to other handlers if the user isn't configuring a link
        
    user_session = GENLINK_STATE[user_id]
    mode = user_session["mode"]
    step = user_session["step"]
    
    # Extract message ID validation checks from the forward or link text
    msg_id = await get_message_id(client, message)
    
    if not msg_id:
        await message.reply_text(
            "❌ <b>Error: Invalid Post Format!</b>\n\n"
            "This post does not belong to your registered DB Channel. Please forward it correctly or check your channel settings.",
            quote=True
        )
        message.stop_propagation()
        return

    # Handle single link generation route execution path
    if mode == "single":
        GENLINK_STATE.pop(user_id, None)
        
        base64_string = await encode(f"get-{msg_id * abs(client.db_channel.id)}")
        link = f"https://t.me/{client.username}?start={base64_string}"
        reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("📫 Your Share Link", url=f'https://telegram.me/share/url?url={link}')]])
        
        await message.reply_text(f"✅ <b>Here is your generated link:</b>\n\n{link}", quote=True, reply_markup=reply_markup)
        message.stop_propagation()
        return

    # Handle multi-step batch link generation path
    elif mode == "batch":
        if step == 1:
            GENLINK_STATE[user_id]["first_id"] = msg_id
            GENLINK_STATE[user_id]["step"] = 2
            
            await message.reply_text(
                "📥 <b>First message recorded successfully!</b>\n\n"
                "Now, please <b>FORWARD</b> the <b>LAST</b> message from your DB Channel (with quotes), "
                "or paste the final post link below."
            )
            message.stop_propagation()
            return
            
        elif step == 2:
            first_id = user_session["first_id"]
            GENLINK_STATE.pop(user_id, None)  # Clean up state tracker memory
            
            string = f"get-{first_id * abs(client.db_channel.id)}-{msg_id * abs(client.db_channel.id)}"
            base64_string = await encode(string)
            link = f"https://t.me/{client.username}?start={base64_string}"
            reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("📫 Your Share Link", url=f'https://telegram.me/share/url?url={link}')]])
            
            await message.reply_text(f"✅ <b>Here is your generated batch link:</b>\n\n{link}", quote=True, reply_markup=reply_markup)
            message.stop_propagation()
            return
            
