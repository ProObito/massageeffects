# +++ Made By Obito [@i_killed_my_clan] +++

import asyncio
import logging
from datetime import datetime, timedelta
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from database.database import obito  # Uses your centralized obito database module instance
from helper_func import is_admin, is_banned

logger = logging.getLogger(__name__)

# ==================== 1. BACKGROUND SCHEDULERS & MONITORS ====================

async def auto_premium_monitor_loop(bot):
    """
    Background loop running every 5 minutes to automatically expire old subscriptions
    and send professional English expiration notices.
    """
    # FIXED: Local import inside function to break circular dependencies
    from bot import Bot
    
    while True:
        try:
            now = datetime.now()

            # Find active premium users whose plan has expired past the current date-time anchor
            expired_users_cursor = obito.user_data.find({
                "is_premium": True,
                "premium_expiry": {"$lt": now}
            })

            async for user in expired_users_cursor:
                user_id = int(user["_id"])
                try:
                    # Clean clear database modification parameters - revert to ad tier
                    await obito.user_data.update_one(
                        {"_id": user_id},
                        {
                            "$set": {"is_premium": False},
                            "$unset": {"premium_expiry": "", "expiry_reminder_sent": ""}
                        }
                    )

                    # Professional English Expiry Alert Message Text
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
                    logger.error(f"Failed to process auto-expiry notification for user {user_id}: {ex}")

        except Exception as e:
            logger.error(f"Critical error inside premium engine expiry monitor loop: {e}")

        await asyncio.sleep(300)  # Evaluation run sweep routine interval defaults to 5 minutes


async def premium_expiry_reminder_scheduler(bot):
    """
    Hourly cron background scheduler checking for profiles expiring within the next 23-24 hour window
    to distribute critical warning notice messages.
    """
    # FIXED: Local import inside function to break circular dependencies
    from bot import Bot
    
    while True:
        try:
            now = datetime.now()
            reminder_time_start = now + timedelta(hours=23)
            reminder_time_end = now + timedelta(hours=24)
            
            upcoming_expiry_cursor = obito.user_data.find({
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
                    
                    # Log state execution boolean flag variable to avoid duplicate triggers
                    await obito.user_data.update_one({"_id": user["_id"]}, {"$set": {"expiry_reminder_sent": True}})
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Failed to send 24h warning to user {user.get('_id')}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in premium warning scheduler routine thread: {e}")
            
        await asyncio.sleep(3600)  # Evaluates parameters once every 1 hour execution tick

# ==================== 2. ADMIN INTERACTIVE CONTROLLERS ====================

@Bot.on_message(filters.command('add_premium') & filters.private & ~is_banned & is_admin)
async def add_premium_user_cmd(bot, message: Message):
    if len(message.command) < 3:
        return await message.reply_text(
            "❌ <b>Usage Format Error!</b>\n\n"
            "<blockquote>Provide target user ID and duration in days:</blockquote>\n"
            "» <code>/add_premium 123456789 30</code> (For 30 Days plan)"
        )
        
    user_str = message.command[1]
    days_str = message.command[2]
    
    if not user_str.isdigit() or not days_str.isdigit():
        return await message.reply_text("❌ <b>Error:</b> User ID and Days value must be integers only.")
        
    target_user_id = int(user_str)
    duration_days = int(days_str)
    
    await obito.add_premium(target_user_id, duration_days)
    
    await message.reply_text(
        f"✅ <b>Premium Tier Activated Successfully!</b>\n\n"
        f"👤 <b>User ID:</b> <code>{target_user_id}</code>\n"
        f"⏳ <b>Duration Allocated:</b> <code>{duration_days} Days</code>"
    )
    
    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=f"🎉 <b>Congratulations!</b>\n\n"
                 f"Your account has been upgraded to the <b>Premium Ad-Free Tier</b> for the next <code>{duration_days} Days</code>.\n"
                 f"Enjoy high-speed bypass-free file downloads!"
        )
    except Exception:
        pass

@Bot.on_message(filters.command('remove_premium') & filters.private & ~is_banned & is_admin)
async def remove_premium_user_cmd(bot, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ <b>Usage Format Error:</b> <code>/remove_premium [user_id]</code>")
        
    user_str = message.command[1]
    if not user_str.isdigit():
        return await message.reply_text("❌ <b>Error:</b> User ID must be a valid integer.")
        
    target_user_id = int(user_str)
    
    if not await obito.is_premium(target_user_id):
        return await message.reply_text("❌ <b>Error:</b> This user does not have an active premium status inside database.")
        
    await obito.remove_premium(target_user_id)
    await message.reply_text(f"🗑 <b>Premium subscription tier revoked for user ID:</b> <code>{target_user_id}</code>")
    
    try:
        await bot.send_message(
            chat_id=target_user_id,
            text="🚨 <b>Notification:</b> Your premium subscription package has been manually revoked by the management team."
        )
    except Exception:
        pass

@Bot.on_message(filters.command('list_premium') & filters.private & ~is_banned & is_admin)
async def list_premium_users_cmd(bot, message: Message):
    loading_msg = await message.reply_text("🔍 <code>Fetching active premium accounts matrix...</code>")
    premium_ids = await obito.get_premium_users()
    
    if not premium_ids:
        await loading_msg.delete()
        return await message.reply_text("ℹ️ <b>No active premium profiles found inside database index registry.</b>")
        
    report = "👑 <b>ACTIVE PREMIUM USERS LOG LIST:</b>\n\n"
    for index, p_id in enumerate(premium_ids, start=1):
        report += f"{index}. 👤 <b>User Key:</b> <code>{p_id}</code>\n"
        
    await loading_msg.delete()
    await message.reply_text(report)
    
