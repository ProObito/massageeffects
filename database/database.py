# +++ Made By Obito [@i_killed_my_clan] +++
import time
from motor.motor_asyncio import AsyncIOMotorClient
from config import DB_URI, DB_NAME

# Asynchronous Database Client Setup (Non-blocking for Pyrogram)
dbclient = AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]

# Database collections mapping
user_data = database['users']
premium_user = database['premium']
channels_col = database['fsub_channels']
admins_col = database['bot_admins']
banned_col = database['banned_users']
orders_col = database['payment_orders']
shortener_col = database['shortener_settings']

class ObitoDB:
    def __init__(self):
        pass

    # ==================== 1. USER BASE FUNCTIONS ====================
    async def present_user(self, user_id: int):
        found = await user_data.find_one({'_id': user_id})
        return bool(found)

    async def add_user(self, user_id: int):
        if not await self.present_user(user_id):
            await user_data.insert_one({'_id': user_id})
        return

    async def full_userbase(self):
        user_ids = []
        async for doc in user_data.find({}):
            user_ids.append(doc['_id'])
        return user_ids

    async def del_user(self, user_id: int):
        await user_data.delete_one({'_id': user_id})
        return

    # ==================== 2. PREMIUM USER FUNCTIONS ====================
    async def is_premium(self, user_id: int):
        found = await premium_user.find_one({'_id': user_id})
        if found:
            # Check if premium plan has expired dynamically
            expiry = found.get('expiry')
            if expiry and time.time() > expiry:
                await self.remove_premium(user_id)
                return False
            return True
        return False

    async def add_premium(self, user_id: int, days: int = 30):
        expiry_time = time.time() + (days * 24 * 60 * 60)
        await premium_user.update_one(
            {'_id': user_id},
            {'$set': {'expiry': expiry_time}},
            upsert=True
        )
        return

    async def get_premium_users(self):
        premium_ids = []
        async for doc in premium_user.find({}):
            premium_ids.append(doc['_id'])
        return premium_ids

    async def remove_premium(self, user_id: int):
        await premium_user.delete_one({'_id': user_id})
        return

    # ==================== 3. ADVANCED FSUB CHANNELS ====================
    async def get_all_channels(self):
        channels = []
        async for doc in channels_col.find({}):
            channels.append(doc['channel_id'])
        return channels

    async def add_channel(self, channel_id: int):
        if not await channels_col.find_one({'channel_id': channel_id}):
            await channels_col.insert_one({'channel_id': channel_id})
            return True
        return False

    async def del_channel(self, channel_id: int):
        res = await channels_col.delete_one({'channel_id': channel_id})
        return res.deleted_count > 0

    # ==================== 4. ADVANCED BOT ADMINS ====================
    async def get_all_admins(self):
        admins = []
        async for doc in admins_col.find({}):
            admins.append(doc['admin_id'])
        return admins

    async def add_admin(self, admin_id: int):
        if not await admins_col.find_one({'admin_id': admin_id}):
            await admins_col.insert_one({'admin_id': admin_id})
            return True
        return False

    async def del_admin(self, admin_id: int):
        res = await admins_col.delete_one({'admin_id': admin_id})
        return res.deleted_count > 0

    # ==================== 5. ADVANCED BANNED USERS ====================
    async def get_ban_users(self):
        banned = []
        async for doc in banned_col.find({}):
            banned.append(doc['user_id'])
        return banned

    async def add_ban_user(self, user_id: int):
        if not await banned_col.find_one({'user_id': user_id}):
            await banned_col.insert_one({'user_id': user_id})
            return True
        return False

    async def del_ban_user(self, user_id: int):
        res = await banned_col.delete_one({'user_id': user_id})
        return res.deleted_count > 0

    # ==================== 6. AUTO PAYMENT ORDERS ====================
    async def save_payment_order(self, order_id: str, user_id: int, amount: float):
        await orders_col.insert_one({
            'order_id': order_id,
            'user_id': user_id,
            'amount': amount,
            'status': 'PENDING',
            'timestamp': time.time()
        })

    async def update_order_status(self, order_id: str, status: str):
        await orders_col.update_one({'order_id': order_id}, {'$set': {'status': status}})

    # ==================== 7. DYNAMIC INLINE SHORTENER ====================
    async def get_shortener_settings(self):
        settings = await shortener_col.find_one({'_id': 'bot_settings'})
        if not settings:
            default = {'_id': 'bot_settings', 'url': None, 'api': None, 'mode': 'Token Mode'}
            await shortener_col.insert_one(default)
            return default
        return settings

    async def update_shortener(self, url: str, api: str):
        await shortener_col.update_one(
            {'_id': 'bot_settings'},
            {'$set': {'url': url, 'api': api}},
            upsert=True
        )

    async def remove_shortener(self):
        await shortener_col.update_one(
            {'_id': 'bot_settings'},
            {'$set': {'url': None, 'api': None}}
        )

    async def toggle_shortener_mode(self, current_mode: str):
        new_mode = "1-Time Mode" if current_mode == "Token Mode" else "Token Mode"
        await shortener_col.update_one(
            {'_id': 'bot_settings'},
            {'$set': {'mode': new_mode}}
        )
        return new_mode

# Database instance globally accessible under 'obito' name mapping
obito = ObitoDB()
    
