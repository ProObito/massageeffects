import asyncio
import logging
from datetime import datetime, timedelta
from pyrogram import filters
from bot import Bot
from database.database import obito # Assuming 'obito' has users collection access
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

async def premium_expiry_reminder_scheduler(bot: Bot):
    """
    Har ghante chalne wala background task jo 24 ghante pehle reminder bhejega.
    """
    while True:
        try:
            now = datetime.now()
            # Hum un users ko dhundhenge jinka premium exact 23 se 24 ghante ke beech bacha hai
            # aur jinhe abhi tak reminder nahi bheja gaya hai.
            reminder_time_start = now + timedelta(hours=23)
            reminder_time_end = now + timedelta(hours=24)
            
            # Database query (Aapko apne schema ke hisab se ise adjust karna ho sakta hai)
            # Maan lete hain database mein 'premium_expiry' ek datetime object hai
            async for user in obito.users_col.find({
                "premium_expiry": {"$gte": reminder_time_start, "$lte": reminder_time_end},
                "expiry_reminder_sent": {"$ne": True} # Double messaging se bachne ke liye flag
            }):
                try:
                    user_id = int(user["_id"])
                    expiry_date_str = user["premium_expiry"].strftime("%d-%b-%Y %I:%M %p")
                    
                    text = (
                        "⚠️ <b>Pʀᴇᴍɪᴜᴍ Exᴘɪʀʏ Rᴇᴍɪɴᴅᴇʀ !</b>\n\n"
                        f"Bhai, aapka premium subscription agle 24 ghante mein expire hone wala hai.\n\n"
                        f"📅 <b>Expiry Time:</b> <code>{expiry_date_str}</code>\n\n"
                        "💡 Agar aap bina ad ke seamless service continue rakhna chahte hain, "
                        "toh abhi apna plan renew karein."
                    )
                    
                    keyboard = InlineKeyboardMarkup([
                        [InlineKeyboardButton("👑 Renew Premium Now", url="https://t.me/+lZ_rLJwBKnllODY1")],
                        [InlineKeyboardButton("✖️ Close", callback_data="close")]
                    ])
                    
                    await bot.send_message(chat_id=user_id, text=text, reply_markup=keyboard)
                    
                    # Reminder send hone ke baad flag ko True set kar do
                    await obito.users_col.update_one({"_id": user["_id"]}, {"$set": {"expiry_reminder_sent": True}})
                    await asyncio.sleep(1) # Flood wait avoid karne ke liye chota delay
                    
                except Exception as e:
                    logger.error(f"Failed to send expiry reminder to {user.get('_id')}: {e}")
                    
        except Exception as e:
            logger.error(f"Error in premium reminder scheduler: {e}")
            
        # Har 1 ghante (3600 seconds) mein check chalega
        await asyncio.sleep(3600)
      
