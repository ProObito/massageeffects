# +++ Made By Obito [@i_killed_my_clan] +++

import asyncio
import logging
from datetime import datetime, timedelta
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from database.database import user_data, obito  
from helper_func import is_admin, is_banned

logger = logging.getLogger(__name__)

# ==================== 1. BACKGROUND SCHEDULERS & MONITORS ====================

async def auto_premium_monitor_loop(bot):
    """
    Background loop running every 5 minutes to automatically expire old subscriptions
    and send professional English expiration notices.
    """
    while True:
        try:
            now = datetime.now()
            expired_users_cursor = user_data.find({
                "is_premium": True,
                "premium_expiry": {"$lt": now}
            })

            async for user in expired_users_cursor:
                user_id = int(user["_id"])
                try:
                    await obito.remove_premium(user_id)

                    expired_text = (
                        "🚨 <b>YOUR PREMIUM PLAN HAS EXPIRED!</b>\n\n"
                        "Hello User,\n"
                        "Your premium ad-free subscription has officially expired, and your account has been reverted to the standard ad-supported mode.\n\n"
                        "✨ <b>Renew your plan now to continue enjoying:</b>\n"
                        "• High-speed direct link generation\n"
                        "• 100% seamless ad-free experience\n"
                        "• Priority movie & series requests handling\n\n"
                        "💡 Click the button below to renew your membership instantly and enjoy uninterrupted services."
                    )

                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("👑 Renew Premium Plan", url="https://t.me/+lZ_rLJwBKnllODY1")],
                        [InlineKeyboardButton("✖️ Close Menu", callback_data="close")]
                    ])

                    await bot.send_message(chat_id=user_id, text=expired_text, reply_markup=keyboard)
                    logger.info(f"Successfully expired and notified premium user: {user_id}")
                except Exception as ex:
                    logger.error(f"Auto-expiry notify error for user {user_id}: {ex}")
        except Exception as e:
            logger.error(f"Critical error inside premium monitor loop: {e}")
        
        await asyncio.sleep(300)

async def premium_expiry_reminder_scheduler(bot):
    """
    Hourly cron background scheduler checking for profiles expiring within the next 23-24 hour window
    to distribute critical warning notice messages.
    """
    while True:
        try:
            now = datetime.now()
            reminder_time_start = now + timedelta(hours=23)
            reminder_time_end = now + timedelta(hours=24)
            
            upcoming_expiry_cursor = user_data.find({
                "is_premium": True,
                "premium_expiry": {"$gte": reminder_time_start, "$lte": reminder_time_end},
                "expiry_reminder_sent": {"$ne": True}
            })
            
            async for user in upcoming_expiry_cursor:
                try:
                    user_id = int(user["_id"])
                    expiry_date_str = user["premium_expiry"].strftime("%d-%b-%Y %I:%M %p")
                    
                    reminder_text = (
                        "⚠️ <b>PREMIUM SUBSCRIPTION RENEWAL REMINDER</b>\n\n"
                        "Dear Customer,\n"
                        "This is an automated notification to inform you that your ad-free premium access will expire in less than 24 hours.\n\n"
                        f"📅 <b>Expiration Timestamp:</b> <code>{expiry_date_str}</code>\n\n"
                        "If you wish to maintain your premium benefits and secure ad-free navigation, please renew your subscription now."
                    )
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("👑 Renew Membership Now", url="https://t.me/+lZ_rLJwBKnllODY1")],
                        [InlineKeyboardButton("✖️ Close", callback_data="close")]
                    ])
                    
                    await bot.send_message(chat_id=user_id, text=reminder_text, reply_markup=keyboard)
                    await user_data.update_one({"_id": user["_id"]}, {"$set": {"expiry_reminder_sent": True}})
                except Exception as e:
                    logger.error(f"Reminder warning error for user {user.get('_id')}: {e}")
        except Exception as e:
            logger.error(f"Error in premium reminder scheduler thread: {e}")
            
        await asyncio.sleep(3600)

# ==================== 2. ADMIN INTERACTIVE CONTROLLERS ====================

@Client.on_message(filters.command('add_premium') & filters.private & ~is_banned & is_admin, group=-101)
async def add_premium_user_cmd(client: Client, message: Message):
    if len(message.command) < 3:
        await message.reply_text(
            "❌ <b>Usage Format Error!</b>\n\n"
            "<blockquote>Provide target user ID and duration in days:\n"
            "» <code>/add_premium 123456789 30</code></blockquote>",
            quote=True
        )
        message.stop_propagation()
        return
        
    user_str = message.command[1]
    days_str = message.command[2]
    
    if not user_str.isdigit() or not days_str.isdigit():
        await message.reply_text("❌ <b>Error:</b> User ID and Days value must be integers only.", quote=True)
        message.stop_propagation()
        return
        
    target_user_id = int(user_str)
    duration_days = int(days_str)
    
    # Fetch User Name from Telegram dynamically
    try:
        user_obj = await client.get_users(target_user_id)
        user_name = user_obj.first_name
    except Exception:
        user_name = "Unknown User"
    
    await obito.add_premium(target_user_id, duration_days)
    await message.reply_text(
        f"✅ <b>Premium Tier Activated Successfully!</b>\n\n"
        f"<blockquote>👤 <b>Name:</b> {user_name}\n"
        f"🆔 <b>User ID:</b> <code>{target_user_id}</code>\n"
        f"⏳ <b>Duration Allocated:</b> <code>{duration_days} Days</code></blockquote>",
        quote=True
    )
    
    try:
        await client.send_message(
            chat_id=target_user_id,
            text=f"🎉 <b>Congratulations!</b>\n\n"
                 f"Your account has been upgraded to the <b>Premium Ad-Free Tier</b> for the next <code>{duration_days} Days</code>.\n"
                 f"Enjoy high-speed bypass-free file downloads!"
        )
    except Exception:
        pass
        
    message.stop_propagation()

@Client.on_message(filters.command('remove_premium') & filters.private & ~is_banned & is_admin, group=-101)
async def remove_premium_user_cmd(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("❌ <b>Usage Format Error:</b> <code>/remove_premium [user_id]</code>", quote=True)
        message.stop_propagation()
        return
        
    user_str = message.command[1]
    if not user_str.isdigit():
        await message.reply_text("❌ <b>Error:</b> User ID must be a valid integer.", quote=True)
        message.stop_propagation()
        return
        
    target_user_id = int(user_str)
    
    if not await obito.is_premium(target_user_id):
        await message.reply_text("❌ <b>Error:</b> This user does not have an active premium status inside database.", quote=True)
        message.stop_propagation()
        return

    # Fetch User Name from Telegram dynamically
    try:
        user_obj = await client.get_users(target_user_id)
        user_name = user_obj.first_name
    except Exception:
        user_name = "Unknown User"
        
    await obito.remove_premium(target_user_id)
    await message.reply_text(
        f"🗑 <b>Premium Subscription Tier Revoked!</b>\n\n"
        f"<blockquote>👤 <b>Name:</b> {user_name}\n"
        f"🆔 <b>User ID:</b> <code>{target_user_id}</code></blockquote>", 
        quote=True
    )
    
    try:
        await client.send_message(
            chat_id=target_user_id,
            text="🚨 <b>Notification:</b> Your premium subscription package has been manually revoked by the management team."
        )
    except Exception:
        pass
        
    message.stop_propagation()

@Client.on_message(filters.command('list_premium') & filters.private & ~is_banned & is_admin, group=-101)
async def list_premium_users_cmd(client: Client, message: Message):
    loading_msg = await message.reply_text("🔍 <code>Fetching active premium accounts matrix...</code>")
    premium_ids = await obito.get_premium_users()
    
    if not premium_ids:
        await loading_msg.delete()
        await message.reply_text("ℹ️ <b>No active premium profiles found inside database index registry.</b>", quote=True)
        message.stop_propagation()
        return
        
    report = "👑 <b>ACTIVE PREMIUM USERS LOG LIST:</b>\n\n"
    for index, p_id in enumerate(premium_ids, start=1):
        # Fetch individual names for the log lists dynamically
        try:
            user_obj = await client.get_users(int(p_id))
            user_name = user_obj.first_name
        except Exception:
            user_name = "Unknown User"
            
        report += f"{index}. <blockquote>👤 <b>Name:</b> {user_name}\n🆔 <b>ID:</b> <code>{p_id}</code></blockquote>\n"
        
    await loading_msg.delete()
    await message.reply_text(report, quote=True)
    message.stop_propagation()

@Client.on_message(filters.command('my_plan') & filters.private & ~is_banned, group=-101)
async def check_my_plan_cmd(client: Client, message: Message):
    user_id = message.from_user.id
    user_data_entry = await user_data.find_one({"_id": user_id})
    
    if user_data_entry and user_data_entry.get("is_premium"):
        expiry = user_data_entry.get("premium_expiry")
        # Time calculation
        remaining = expiry - datetime.now()
        days = remaining.days
        hours = remaining.seconds // 3600
        
        status_text = (
            "👑 <b>YOUR PREMIUM MEMBERSHIP STATUS</b>\n\n"
            "<blockquote>👤 <b>Name:</b> {name}\n"
            "🆔 <b>User ID:</b> <code>{id}</code>\n"
            "💎 <b>Plan Status:</b> Active\n"
            "⏳ <b>Time Remaining:</b> {days} Days, {hours} Hours</blockquote>"
        ).format(name=message.from_user.first_name, id=user_id, days=days, hours=hours)
        
        await message.reply_text(status_text, quote=True)
    else:
        await message.reply_text(
            "ℹ️ <b>Membership Status:</b> <code>Standard (Ad-Supported)</code>\n\n"
            "You are currently not on a premium plan. Please contact admins for subscription details.",
            quote=True
        )
    message.stop_propagation()
    
