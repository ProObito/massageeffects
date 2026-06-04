import time
from pyrogram import Client, filters
from pyrogram.types import Message

from bot import Bot
from database.database import obito, premium_user
from config import OWNER_ID, ADMINS, PLAN_TEXT 

# ==================== 2. ADVANCED ADD PREMIUM WITH DAYS ====================
@Bot.on_message(filters.command('add_premium') & filters.user(int(OWNER_ID)))
async def add_premium_command(client: Client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("<b>❌ Incorrect Format!</b>\n\n<b>Use:</b> `/add_premium {user_id} {days}`\n<b>Example:</b> `/add_premium 123456789 30`")
        return

    try:
        user_id = int(message.command[1])
        # Agar admin days pass karna bhool gaya toh default 30 days apply hoga
        days = int(message.command[2]) if len(message.command) > 2 else 30
    except ValueError:
        await message.reply_text("❌ Invalid User ID or Days format. Please pass integers only.")
        return

    try:
        user = await client.get_users(user_id)
        user_name = user.first_name + (" " + user.last_name if user.last_name else "")
    except Exception as e:
        await message.reply_text(f"Error fetching user information: {e}")
        return

    if not await obito.is_premium(user_id):
        await obito.add_premium(user_id, days=days)
        
        # Save explicit plan metadata tracker info into collection for `/my_plan` tracking calculations
        await premium_user.update_one(
            {'_id': user_id},
            {'$set': {'total_duration_days': days, 'activated_at': time.time()}},
            upsert=True
        )
        
        await message.reply(f"✅ User <b>{user_name}</b> (`{user_id}`) has been added as a premium user for <b>{days} Days</b>.")
        try:
            await client.send_message(user_id, f"🎉 **Congratulations! Your Premium Membership has been activated for {days} Days!**")
        except Exception as e:
            await message.reply(f"Failed to notify the user: {e}")
    else:
        await message.reply(f"⚠️ User {user_name} (`{user_id}`) is already a premium user.")


# ==================== 3. REMOVE PREMIUM COMMAND ====================
@Bot.on_message(filters.command('remove_premium') & filters.user(int(OWNER_ID)))
async def remove_premium_command(client: Client, message: Message):
    if len(message.command) != 2:
        await message.reply_text("<b>Use:</b> `/remove_premium {user_id}`")
        return

    try:
        user_id = int(message.command[1])
    except ValueError:
        await message.reply_text("Invalid user ID.")
        return

    try:
        user = await client.get_users(user_id)
        user_name = user.first_name + (" " + user.last_name if user.last_name else "")
    except Exception as e:
        await message.reply_text(f"Error fetching user information: {e}")
        return

    if await obito.is_premium(user_id):
        await obito.remove_premium(user_id)
        await message.reply(f"⛔️ User {user_name} (`{user_id}`) has been removed from premium users.")
        try:
            await client.send_message(user_id, "Your Premium membership has been ended. Contact admins to renew here - @Its_Lozo")
        except Exception as e:
            await message.reply(f"Failed to notify the user: {e}")
    else:
        await message.reply(f"User {user_name} (`{user_id}`) is not a premium user.")


# ==================== 4. LIST PREMIUM USERS ====================
@Bot.on_message(filters.command('list_premium') & filters.user(int(OWNER_ID)))
async def list_premium_command(client: Client, message: Message):
    premium_users = await obito.get_premium_users()
    if not premium_users:
        await message.reply("There are no premium users.")
        return

    user_list = []
    for user_id in premium_users:
        try:
            user = await client.get_users(user_id)
            user_name = user.first_name + (" " + user.last_name if user.last_name else "")
            user_list.append(f"👤 {user_name} - (`{user_id}`)")
        except Exception:
            user_list.append(f"👤 User ID: `{user_id}` (Name: Could not fetch)")

    user_list_text = "\n".join(user_list)
    await message.reply(f"<b>✨ Premium Users List:</b>\n\n{user_list_text}")


# ==================== 5. DYNAMIC MY PLAN MANAGEMENT ====================
@Bot.on_message(filters.command('my_plan') & filters.private)
async def my_plan_command(client: Client, message: Message):
    user_id = message.from_user.id
    
    # Check regular subscription state inside DB object
    is_user_premium = await obito.is_premium(user_id)
    
    if not is_user_premium:
        await message.reply_text(
            "<b>🚫 You don't have any active premium plans!</b>\n\n"
            "Ads: Enabled ❌\n"
            "Premium Features: Locked 🔒\n\n"
            "💡 Unlock premium to download files instantly without shorteners!\n"
            "Contact admin here to buy - @Its_Lozo"
        )
        return

    # Fetch extended structural stats breakdown parameters from mongo context document metadata
    premium_data = await premium_user.find_one({'_id': user_id})
    
    if premium_data:
        expiry_timestamp = premium_data.get('expiry', 0)
        total_days = premium_data.get('total_duration_days', 'N/A')
        
        # Calculate time difference remaining variables calculations logic
        time_left_seconds = expiry_timestamp - time.time()
        
        if time_left_seconds > 0:
            days_left = int(time_left_seconds // (24 * 3600))
            hours_left = int((time_left_seconds % (24 * 3600)) // 3600)
            minutes_left = int((time_left_seconds % 3600) // 60)
            
            readable_validity = f"<code>{days_left} Days, {hours_left} Hours, {minutes_left} Minutes</code>"
        else:
            readable_validity = "Expired / System processing delay"
            
        # Format custom custom message layer strings imported out from configuration global schema mapping
        formatted_plan_text = PLAN_TEXT.format(
            user_mention=message.from_user.mention,
            user_id=user_id,
            total_days=total_days,
            time_left=readable_validity
        )
        
        await message.reply_text(formatted_plan_text)
    else:
        # Fallback safeguard state layer checking parameters control validation 
        await message.reply_text(
            f"<b>✨ Premium State: Active ✅</b>\n\n"
            f"👤 <b>User:</b> {message.from_user.mention}\n"
            f"ℹ️ Detailed tracking timeline values not found in records, please contact support team admin. @Its_Lozo"
        )
        
