# +++ Made By Obito [@i_killed_my_clan] +++
import os
import logging
from logging.handlers import RotatingFileHandler

#Bot token @Botfather
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "7403693425:AAHwGyWW_sVf6Ips2J1Mh8uQyMjgDiy3mIk")

#Your API ID from my.telegram.org
APP_ID = int(os.environ.get("APP_ID", "21352768"))

#Your API Hash from my.telegram.org
API_HASH = os.environ.get("API_HASH", "5fecf44f5dd9f46410d6d835491ae4a3")

#Your db channel Id
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1003975701563"))

#OWNER ID
OWNER_ID = int(os.environ.get("OWNER_ID", "8006059363"))

#Port
PORT = os.environ.get("PORT", "8080")

#Database 
DB_URI = os.environ.get("DATABASE_URL", "mongodb+srv://aadarsh_db_user:p1BmyjAgGv4y0OEJ@cluster0.gbos5lg.mongodb.net/?appName=Cluster0")
DB_NAME = os.environ.get("DATABASE_NAME", "obito")

#force sub channel id, if you want enable force sub
FORCESUB_CHANNEL = int(os.environ.get("FORCESUB_CHANNEL", "0"))
FORCESUB_CHANNEL2 = int(os.environ.get("FORCESUB_CHANNEL2", "0"))

TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "4"))

#pics
START_PIC = os.environ.get("START_PIC", "https://files.catbox.moe/43de6v.jpg")
FORCE_PIC = os.environ.get("FORCE_PIC", "https://files.catbox.moe/43de6v.jpg")

#text
HELP_TXT = """<b><blockquote>⚠️ Hᴇʏ, {} × ᴛʜᴇɴ ᴛʀʏ ᴀɢᴀɪɴ.. !

❗Fᴀᴄɪɴɢ ᴘʀᴏʙʟᴇᴍs, ᴜsᴇ: /help</b>"""

ABOUT_TXT = """<b>🤖 ᴍʏ ɴᴀᴍᴇ: Gojo
<b>» ᴅᴇᴠᴇʟᴏᴘᴇʀ : <a href=https://t.me/i_killed_my_clan>ᴏʙɪᴛᴏ</a></b>"""

SHORT_MSG = "Your Link is down here click on Short URL.."

#start message
START_MSG = os.environ.get("START_MESSAGE", """<b>⚡ Hᴇʏ, {mention} ~

<blockquote expandable>ɪ ᴀᴍ ғɪʟᴇ sᴛᴏʀᴇ ʙᴏᴛ, ɪ ᴄᴀɴ sᴛᴏʀᴇ ᴘʀɪᴠᴀᴛᴇ ғɪʟᴇs ɪɴ sᴘᴇᴄɪғɪᴇᴅ ᴄʜᴀɴɴᴇʟ ᴀɴᴅ ᴏᴛʜᴇʀ ᴜsᴇʀs ᴄᴀɴ ᴀᴄᴄᴇss ɪᴛ ғʀᴏᴍ sᴘᴇᴄɪᴀʟ ʟɪɴᴋ.</blockquote></b>""")
try:
    ADMINS=[5090651635]
    for x in (os.environ.get("ADMINS", "8006059363").split()):
        ADMINS.append(int(x))
except ValueError:
        raise Exception("Your Admins list does not contain valid integers.")

#Force sub message 
FORCE_MSG = os.environ.get("FORCE_SUB_MESSAGE", "ʜᴇʟʟᴏ {first}!⚡\n\n🫧ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ʙᴏᴛʜ ᴏꜰ ᴏᴜʀ ᴀɴɪᴍᴇ ᴄʜᴀɴɴᴇʟꜱ ᴀɴᴅ ᴛʀʏ ᴀɢᴀɪɴ...!")

#set your Custom Caption here, Keep None for Disable Custom Caption
CUSTOM_CAPTION = os.environ.get("CUSTOM_CAPTION", None)

#set True if you want to prevent users from forwarding files from bot
PROTECT_CONTENT = True if os.environ.get('PROTECT_CONTENT', "False") == "True" else False

#Set true if you want Disable your Channel Posts Share button
DISABLE_CHANNEL_BUTTON = os.environ.get("DISABLE_CHANNEL_BUTTON", False) == 'True'

#Short Url or Api
SHORT_URL = os.environ.get("SHORTNER_URL", "Arolinks.com")
SHORT_API = os.environ.get("SHORTNER_API", "7aed91f9dd06cf474ec93216ad40345985949d63")

BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "Pʟᴇᴀꜱᴇ ᴅᴏɴ'ᴛ ᴍᴇꜱꜱᴀɢᴇ ᴍᴇ ᴅɪʀᴇᴄᴛʟʏ ɪ ᴀᴍ ᴏɴʟʏ ᴡᴏʀᴋ ꜰᴏʀ - @AnimeInHindi094"

PLAN_TEXT = """
✨ <b>Exclusive Premium Membership</b> ✨
> <i>Unlock a World of Benefits Just for You!</i>

🔥 <b>Premium Perks:</b>
> ✔️ <b>Direct Channel Link</b> – No Ads, No Distractions!
> ✔️ <b>Special Access</b> to Exclusive Events & Content
> ✔️ <b>Faster Support</b> & Priority Assistance

💭 <b>Plus:</b> You'll get direct access to all the videos with any of these plans!

💰 <b>Affordable Pricing:</b>
> ○ <b>7 Days:</b> INR 60
> ○ <b>1 Month:</b> INR 140
> ○ <b>3 Months:</b> INR 299
> ○ <b>4 Months:</b> INR 400
> ○ <b>6 Months:</b> INR 550 

👤 <b>User:</b> {user_mention}
🆔 <b>Account ID:</b> <code>{user_id}</code>
📦 <b>Purchased Plan:</b> <code>{total_days} Days Plan</code>
⏳ <b>Remaining Validity:</b> {time_left}

Ready to Upgrade?
» Message @Its_lozo to get UPI or QR Code for payment.
» Send a screenshot of your payment to @its_lozo (for Auto Verification).

➡️ <b>Seats are LIMITED for Premium Members – Grab Yours Now!</b>
"""

AUTO_DEL = os.environ.get("AUTO_DEL", "True")
DEL_TIMER = int(os.environ.get("DEL_TIMER", "600"))
DEL_MSG = "<b>This File is deleting automatically in {time}. Forward in your Saved Messages..!</b>"

ADMINS.append(6654561076)
ADMINS.append(5585016974)

LOG_FILE_NAME = "filesharingbot.txt"

LOG_FILE_NAME = "filesharingbot.txt"

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)
