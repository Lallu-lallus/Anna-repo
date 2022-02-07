import re
from os import environ

id_pattern = re.compile(r'^.\d+$')

# Bot information
SESSION = environ.get('SESSION', 'Media_search')
API_ID = int(environ['API_ID'])
API_HASH = environ['API_HASH']
BOT_TOKEN = environ['BOT_TOKEN']

# Bot settings
CACHE_TIME = int(environ.get('CACHE_TIME', 300))
USE_CAPTION_FILTER = bool(environ.get('USE_CAPTION_FILTER', False))

# Photo Mode
PICS = (environ.get('PICS', 'https://telegra.ph/file/497f21338351cef6cc1fd.jpg https://telegra.ph/file/60ec3a4a522d06b5e4a2c.jpg https://telegra.ph/file/90345e9255d32f5c8ad75.jpg https://telegra.ph/file/e81e25e0c3ee753530c7f.jpg https://telegra.ph/file/41aaa2bc85bad6986641b.jpg https://telegra.ph/file/78f1bd0309d6607dc44fa.jpg https://telegra.ph/file/4e0bbf59af8c55dfce9ff.jpg https://telegra.ph/file/7ae43915facd8eb0a3d00.jpg https://telegra.ph/file/2e91f2168859795bebec1.jpg https://telegra.ph/file/2c91985dd562ea835ef3b.jpg https://telegra.ph/file/daab7f2becc4ddab45586.jpg https://telegra.ph/file/7beda83fbe243952f6768.jpg https://telegra.ph/file/c3fdb36e73269c2e4d629.jpg https://telegra.ph/file/07af4bdb370593909aa51.jpg')).split()
SEPLLING_MODE_VIDEO = (environ.get('SEPLLING_MODE_VIDEO', 'https://telegra.ph/file/7658da66b1771aabd026c.mp4 https://telegra.ph/file/7658da66b1771aabd026c.mp4 https://telegra.ph/file/7658da66b1771aabd026c.mp4 https://telegra.ph/file/7658da66b1771aabd026c.mp4 https://telegra.ph/file/7658da66b1771aabd026c.mp4 https://telegra.ph/file/7658da66b1771aabd026c.mp4 https://telegra.ph/file/7658da66b1771aabd026c.mp4 https://telegra.ph/file/7658da66b1771aabd026c.mp4')).split()

# Admins, Channels & Users
ADMINS = [int(admin) if id_pattern.search(admin) else admin for admin in environ['ADMINS'].split()]
CHANNELS = [int(ch) if id_pattern.search(ch) else ch for ch in environ['CHANNELS'].split()]
auth_users = [int(user) if id_pattern.search(user) else user for user in environ.get('AUTH_USERS', '').split()]
AUTH_USERS = (auth_users + ADMINS) if auth_users else []
auth_channel = environ.get('AUTH_CHANNEL')
AUTH_CHANNEL = int(auth_channel) if auth_channel and id_pattern.search(auth_channel) else auth_channel
AUTH_GROUPS = [int(admin) for admin in environ.get("AUTH_GROUPS", "").split()]

# MongoDB information
DATABASE_URI = environ['DATABASE_URI']
DATABASE_NAME = environ['DATABASE_NAME']
COLLECTION_NAME = environ.get('COLLECTION_NAME', 'Telegram_files')
SUPPORT_CHAT = environ.get('SUPPORT_CHAT', 'TeamEvamaria')

# Messages
default_start_msg = """
**👋Hey<a href="tg://settings"> Bruh </a>, 
𝙼𝚈 𝙽𝙰𝙼𝙴 <a href="https://t.me/Dqautofl_bot"> Anna Ben </a> 𝙸 𝙲𝙰𝙽 𝙿𝚁𝙾𝚅𝙸𝙳𝙴 𝙼𝙾𝚅𝙸𝙴𝚂 𝙸𝙽 𝙶𝚁𝙾𝚄𝙿𝚂,**

𝙸𝚃'𝚂 𝚅𝙴𝚁𝚈 𝙴𝙰𝚂𝚈. 𝙹𝚄𝚂𝚃 𝙰𝙳𝙳 𝙼𝙴 𝚃𝙾 𝚈𝙾𝚄𝚁 𝙶𝚁𝙾𝚄𝙿 𝙰𝙽𝙳 𝙼𝙰𝙺𝙴 𝙼𝙴 𝙰𝙳𝙼𝙸𝙽, 𝚃𝙷𝙰𝚃𝚂 𝙰𝙻𝙻, 𝙸'𝙻𝙻 𝙿𝚁𝙾𝚅𝙸𝙳𝙴 𝙼𝙾𝚅𝙸𝙴𝚂 𝚃𝙷𝙴𝚁𝙴 🤓

Hey <a href="https://t.me/Dqautofl_bot?startgroup=true"> add me to your grp and make me an admin </a>

Send me /id and give your id and group id
➖➖➖➖➖➖➖➖➖➖➖➖➖
©️MᴀɪɴᴛᴀɪɴᴇD Bʏ :<a href="https://t.me/pro_editor_tg"> Lallu-llalus </a>
"""
START_MSG = environ.get('START_MSG', default_start_msg)

FILE_CAPTION = environ.get("CUSTOM_FILE_CAPTION", "")
OMDB_API_KEY = environ.get("OMDB_API_KEY", "")
if FILE_CAPTION.strip() == "":
    CUSTOM_FILE_CAPTION=None
else:
    CUSTOM_FILE_CAPTION=FILE_CAPTION
if OMDB_API_KEY.strip() == "":
    API_KEY=None
else:
    API_KEY=OMDB_API_KEY
