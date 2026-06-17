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

# FIXED: Removed 'setup_premium_handlers' from imports to kill the ImportError permanently
from plugins.premium import auto_premium_monitor_loop, premium_expiry_reminder_scheduler

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
        
        try:
            await self.send_message(
                chat_id=int(OWNER_ID),
                text="🚀 <b>Bot is successfully Online & Connected with MongoDB Cluster!</b>"
            )
        except Exception:
            pass

        # Fires background monitoring schedules safely
        asyncio.create_task(auto_premium_monitor_loop(self))
        asyncio.create_task(premium_expiry_reminder_scheduler(self))

        app = web.AppRunner(await web_server())
        await app.setup()
        bind_address = "0.0.0.0"
        await web.TCPSite(app, bind_address, PORT).start()

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("Bot stopped.")

# ==================== DYNAMIC /COMMANDS LIST REGISTRY ====================
@Bot.on_message(filters.command(['cmds', 'help_cmd']) & filters.private & ~is_banned, group=-100)
async def bot_commands_dictionary_list(bot: Bot, message):
    commands_text = (
        "📜 <b>🤖 BOT COMMANDS DICTIONARY PANEL</b>\n\n"
        "✨ <b>👤 USER COMMANDS:</b>\n"
        "• <code>/start</code> - Wake up the bot.\n"
        "• <code>/my_plan</code> - Check premium expiry.\n"
        "• <code>/request</code> - Submit movie requests.\n\n"
    )
    
    if await is_admin(None, bot, message):
        commands_text += (
            "⚙️ <b>🛠 ADMIN CONTROL COMMANDS:</b>\n"
            "• <code>/shorten</code> - Open inline shortener control panel.\n"
            "• <code>/add_premium</code> - Add user to premium tier.\n"
            "• <code>/remove_premium</code> - Revoke user premium access.\n"
            "• <code>/list_premium</code> - List all paid premium members.\n"
        )
        
    await message.reply_text(
        text=commands_text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("✖️ Close Menu", callback_data="close")]]),
        quote=True
    )
    message.stop_propagation()
    
