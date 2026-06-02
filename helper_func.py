import base64
import re
import asyncio
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant
from pyrogram.errors import FloodWait

from config import OWNER_ID
from database.database import obito

# ==================== Dynamic Multi-FSub Check ====================
async def is_subscribed_filter(_, client, update):
    if not update.from_user:
        return True

    user_id = update.from_user.id

    # Owner checking bypass
    if user_id == int(OWNER_ID):
        return True

    # DB Admins checking bypass
    admin_ids = await obito.get_all_admins()
    if user_id in admin_ids:
        return True

    # Fetch channels from MongoDB dynamic object
    channels = await obito.get_all_channels()
    if not channels:
        return True

    member_status = [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.MEMBER]

    for channel_id in channels:
        try:
            member = await client.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status not in member_status:
                return False
        except UserNotParticipant:
            return False
        except Exception:
            continue

    return True

subscribed = filters.create(is_subscribed_filter)


# ==================== Dynamic Admin & Ban Verification ====================
async def admin_check_filter(_, client, message):
    if not message.from_user:
        return False
    user_id = message.from_user.id
    if user_id == int(OWNER_ID):
        return True
    admin_ids = await obito.get_all_admins()
    return user_id in admin_ids

is_admin = filters.create(admin_check_filter)


async def banned_check_filter(_, client, message):
    if not message.from_user:
        return False
    banned_users = await obito.get_ban_users()
    return message.from_user.id in banned_users

is_banned = filters.create(banned_check_filter)


# ==================== Core Utilities ====================
async def encode(string):
    string_bytes = string.encode("ascii")
    base64_bytes = base64.urlsafe_b64encode(string_bytes)
    base64_string = (base64_bytes.decode("ascii")).strip("=")
    return base64_string

async def decode(base64_string):
    base64_string = base64_string.strip("=")
    base64_bytes = (base64_string + "=" * (-len(base64_string) % 4)).encode("ascii")
    string_bytes = base64.urlsafe_b64decode(base64_bytes)
    string = string_bytes.decode("ascii")
    return string

async def get_messages(client, message_ids):
    messages = []
    total_messages = 0
    while total_messages != len(message_ids):
        temb_ids = message_ids[total_messages:total_messages+200]
        try:
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except FloodWait as e:
            await asyncio.sleep(e.x)
            msgs = await client.get_messages(
                chat_id=client.db_channel.id,
                message_ids=temb_ids
            )
        except:
            pass
        total_messages += len(temb_ids)
        messages.extend(msgs)
    return messages

async def get_message_id(client, message):
    if message.forward_from_chat:
        if message.forward_from_chat.id == client.db_channel.id:
            return message.forward_from_message_id
        else:
            return 0
    elif message.forward_sender_name:
        return 0
    elif message.text:
        pattern = "https://t.me/(?:c/)?(.*)/(\d+)"
        matches = re.match(pattern, message.text)
        if not matches:
            return 0
        channel_id = matches.group(1)
        msg_id = int(matches.group(2))
        if channel_id.isdigit():
            if f"-100{channel_id}" == str(client.db_channel.id):
                return msg_id
        else:
            if channel_id == client.db_channel.username:
                return msg_id
    else:
        return 0

def get_readable_time(seconds: int) -> str:
    count = 0
    up_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]
    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)
    hmm = len(time_list)
    for x in range(hmm):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        up_time += f"{time_list.pop()}, "
    time_list.reverse()
    up_time += ":".join(time_list)
    return up_time
    
