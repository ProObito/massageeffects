# +++ Centralized Bot Core Engine - Made By Obito +++

from aiohttp import web
from plugins import web_server

import pyromod.listen
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import sys
import asyncio
from datetime import datetime
import pyrogram.utils

from config import API_HASH, APP_ID, LOGGER, TG_BOT_TOKEN, TG_BOT_WORKERS, FORCESUB_CHANNEL, FORCESUB_CHANNEL2, CHANNEL_ID, PORT, OWNER_ID
from helper_func import is_admin, is_banned

# FIXED: Import background tasks and setup function without top-level Client hooks to prevent circular imports
from plugins.premium import auto_premium_monitor_loop, premium_expiry_reminder_scheduler, setup_premium_handlers

pyrogram.utils.MIN_CHANNEL_ID = -1009147483647

class Bot(Client):
    def __init__(self):
        super().__init__(
            name="Bot",
            api_hash=API_HASH,
            api_id=APP_ID,
            plugins={
                "root": "plugins"
            },
            workers=TG_BOT_WORKERS,
            bot_token=TG_BOT_TOKEN
        )
        self.LOGGER = LOGGER

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)
        usr_bot_me = await self.get_me()
        self.uptime = datetime.now()
        self.username = usr_bot_me.username

        if FORCESUB_CHANNEL:
            try:
                link = (await self.get_chat(FORCESUB_CHANNEL)).invite_link
                if not link:
                    await self.export_chat_invite_link(FORCESUB_CHANNEL)
                    link = (await self.get_chat(FORCESUB_CHANNEL)).invite_link
                self.invitelink1 = link
            except Exception as a:
                self.LOGGER(__name__).warning(a)
                self.LOGGER(__name__).warning("Bot can't Export Invite link from Force Sub Channel!")
                sys.exit()
                
        if FORCESUB_CHANNEL2:
            try:
                link = (await self.get_chat(FORCESUB_CHANNEL2)).invite_link
                if not link:
                    await self.export_chat_invite_link(FORCESUB_CHANNEL2)
                    link = (await self.get_chat(FORCESUB_CHANNEL2)).invite_link
                self.invitelink2 = link
            except Exception as a:
                self.LOGGER(__name__).warning(a)
                self.LOGGER(__name__).warning("Bot can't Export Invite link from Force Sub Channel!")
                sys.exit()
                
        try:
            db_channel = await self.get_chat(CHANNEL_ID)
            self.db_channel = db_channel
            test = await self.send_message(chat_id=db_channel.id, text="Test Message")
            await test.delete()
        except Exception as e:
            self.LOGGER(__name__).warning(e)
            sys.exit()

        self.set_parse_mode(ParseMode.HTML)
        self.LOGGER(__name__).info("Bot Running..! Created by @i_killed_my_clan")
        
        # ==================== STARTUP NOTIFICATION FOR OWNER ====================
        try:
            await self.send_message(
                chat_id=int(OWNER_ID),
                text="🚀 <b>Bot is successfully Online & Connected with MongoDB Cluster!</b>\n\n"
                     "⚡ <i>All systems and dynamic interceptors are functioning smoothly.</i>"
            )
        except Exception as e:
            self.LOGGER(__name__).warning(f"Could not notify owner on startup: {e}")

        # ==================== STARTUP PREMIUM DYNAMIC ROUTING & TIMERS ====================
        # This initializes add_premium / remove_premium / list_premium commands without loops
        setup_premium_handlers(self)
        
        # Starts background tasks asynchronously
        asyncio.create_task(auto_premium_monitor_loop(self))
        asyncio.create_task(premium_expiry_reminder_scheduler(self))
        self.LOGGER(__name__).info("🔥 Auto Premium Monitor & 24h Reminder Schedulers Activated Successfully!")

        # Web-response (Koyeb health check passes setup)
        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")


# ==================== DYNAMIC /COMMANDS LIST REGISTRY ====================
# FIXED: Set group=-100 to intercept everything first, ensuring normal users can call it and blocking the duplicate alert popups completely
@Bot.on_message(filters.command(['cmds', 'help_cmd']) & filters.private & ~is_banned, group=-100)
async def bot_commands_dictionary_list(bot: Bot, message):
    user_id = message.from_user.id
    
    commands_text = (
        "📜 <b>🤖 BOT COMMANDS DICTIONARY PANEL</b>\n\n"
        "✨ <b>👤 USER COMMANDS:</b>\n"
        "• <code>/start</code> - Wake up the bot and load active file database links.\n"
        "• <code>/my_plan</code> - Check your active premium membership validity and expiry countdown.\n"
        "• <code>/request</code> - Submit a direct movie or series request privately to the admin team.\n\n"
    )
    
    # Render admin menu block dynamically if the checking wrapper validates permissions
    if await is_admin(None, bot, message):
        commands_text += (
            "⚙️ <b>🛠 ADMIN CONTROL COMMANDS:</b>\n"
            "• <code>/shorten</code> - Open the inline panel to configure or remove url shorteners.\n"
            "• <code>/checkslots</code> - Check status of all 5 shortener sequential slots.\n"
            "• <code>/setslot [1-5] domain | api</code> - Quick shortcut command to set dynamic slots.\n"
            "• <code>/wipeslot [1-5]</code> - Text command to wipe out a specific slot configuration.\n"
            "• <code>/auto_del</code> - Adjust configuration variables for message deletion timers and modes.\n"
            "• <code>/fsub_chnl</code> - View the complete registry of active dynamic multi-fsub channels.\n"
            "• <code>/add_banuser [id]</code> - Blacklist a specific user and permanently restrict bot access.\n"
            "• <code>/del_banuser [id]</code> - Unban a user from the database blacklist registry.\n"
            "• <code>/banuser_list</code> - Inspect the log of all currently banned accounts.\n\n"
            
            "👑 <b>🔥 OWNER EXCLUSIVE POWER COMMANDS:</b>\n"
            "• <code>/add_premium [id] [days]</code> - Allot ad-free premium system access to a user for specific days.\n"
            "• <code>/remove_premium [id]</code> - Instantly wipe out a user's paid premium plan permissions.\n"
            "• <code>/list_premium</code> - Render a summary of all currently active premium paid accounts.\n"
            "• <code>/add_fsub [channel_id]</code> - Link a new channel to the dynamic force subscription engine.\n"
            "• <code>/del_fsub [channel_id / all]</code> - Remove specific or all channels from force subscribe checking.\n"
            "• <code>/add_admins [id]</code> - Appoint a user as a secondary bot manager inside the database.\n"
            "• <code>/del_admins [id]</code> - Revoke bot manager privileges from a specific admin account.\n"
            "• <code>/admin_list</code> - Monitor and fetch metadata profiles of all existing bot admins.\n"
            "• <code>/broadcast [timer]</code> - Deliver structural broadcast drops (e.g., <code>24h</code> for temporary delivery).\n"
            "• <code>/pbroadcast [timer]</code> - Distribute dynamic broadcasts and automatically pin them inside the user's PM inbox.\n"
        )
        
    await message.reply_text(
        text=commands_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Close Menu", callback_data="close")]]),
        quote=True
    )
    
    # CRITICAL INJECTION: Instantly kills downstream execution so no other hidden file can inject an unwanted alert popup box
    message.stop_propagation()
    
