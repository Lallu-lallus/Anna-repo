import re
import base64
import logging
from struct import pack
from pyrogram.types import Message
from pyrogram.errors import UserNotParticipant
from pyrogram.file_id import FileId
from pyrogram.types import Message
from pymongo.errors import DuplicateKeyError
from umongo import Instance, Document, fields
from motor.motor_asyncio import AsyncIOMotorClient
from marshmallow.exceptions import ValidationError
import os
import PTN
import requests
import json
from imdb import IMDb
from typing import List
from typing import Union
from info import DATABASE_URI, DATABASE_NAME, COLLECTION_NAME, USE_CAPTION_FILTER, AUTH_CHANNEL, API_KEY
DATABASE_URI_2=os.environ.get('DATABASE_URI_2', DATABASE_URI)
DATABASE_NAME_2=os.environ.get('DATABASE_NAME_2', DATABASE_NAME)
COLLECTION_NAME_2="Posters"
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

client = AsyncIOMotorClient(DATABASE_URI)
db = client[DATABASE_NAME]
instance = Instance.from_db(db)

IClient = AsyncIOMotorClient(DATABASE_URI_2)
imdbdb=client[DATABASE_NAME_2]
imdb=Instance.from_db(imdbdb)

imdb = IMDb()

@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_type = fields.StrField(allow_none=True)
    mime_type = fields.StrField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        collection_name = COLLECTION_NAME
# temp db for banned 
class temp(object):
    BANNED_USERS = []
    BANNED_CHATS = []
    ME = None
    CURRENT=int(os.environ.get("SKIP", 2))
    CANCEL = False
    MELCOW = {}
    U_NAME = None

imdb = IMDb()

@imdb.register
class Poster(Document):
    imdb_id = fields.StrField(attribute='_id')
    title = fields.StrField()
    poster = fields.StrField()
    year= fields.IntField(allow_none=True)

    class Meta:
        collection_name = COLLECTION_NAME_2

async def get_poster(query, bulk=False, id=False):
    if not id:
        # https://t.me/GetTGLink/4183
        pattern = re.compile(r"^(([a-zA-Z\s])*)?\s?([1-2]\d\d\d)?", re.IGNORECASE)
        match = pattern.match(query)
        year = None
        if match:
            title = match.group(1)
            year = match.group(3)
        else:
            title = query
        movieid = imdb.search_movie(title.lower(), results=10)
        if not movieid:
            return None
        if year:
            filtered=list(filter(lambda k: str(k.get('year')) == str(year), movieid))
            if not filtered:
                filtered = movieid
        else:
            filtered = movieid
        movieid=list(filter(lambda k: k.get('kind') in ['movie', 'tv series'], filtered))
        if not movieid:
            movieid = filtered
        if bulk:
            return movieid
        movieid = movieid[0].movieID
    else:
        movieid = int(query)
    movie = imdb.get_movie(movieid)
    title = movie.get('title')
    genres = ", ".join(movie.get("genres")) if movie.get("genres") else None
    rating = str(movie.get("rating"))
    if movie.get("original air date"):
        date = movie["original air date"]
    elif movie.get("year"):
        date = movie.get("year")
    else:
        date = "N/A"
    poster = movie.get('full-size cover url')
    plot = movie.get('plot')
    if plot and len(plot) > 0:
        plot = plot[0]
    if plot and len(plot) > 800:
        plot = plot[0:800] + "..."
    return {
        'title': title,
        'year': date,
        'genres': genres,
        'poster': poster,
        'plot': plot,
        'rating': rating,
        'url':f'https://www.imdb.com/title/tt{movieid}'
    }

async def save_poster(imdb_id, title, year, url):
    try:
        data = Poster(
            imdb_id=imdb_id,
            title=title,
            year=int(year),
            poster=url
        )
    except ValidationError:
        logger.exception('Error occurred while saving poster in database')
    else:
        try:
            await data.commit()
        except DuplicateKeyError:
            logger.warning("already saved in database")
        else:
            logger.info("Poster is saved in database")

async def save_file(media):
    """Save file in database"""

    # TODO: Find better way to get same file_id for same media to avoid duplicates
    file_id, file_ref = unpack_new_file_id(media.file_id)

    try:
        file = Media(
            file_id=file_id,
            file_ref=file_ref,
            file_name=media.file_name,
            file_size=media.file_size,
            file_type=media.file_type,
            mime_type=media.mime_type,
            caption=media.caption.html if media.caption else None,
        )
    except ValidationError:
        logger.exception('Error occurred while saving file in database')
    else:
        try:
            await file.commit()
        except DuplicateKeyError:
            logger.warning(media.file_name + " is already saved in database")
        else:
            logger.info(media.file_name + " is saved in database")


async def get_search_results(query, file_type=None, max_results=10, offset=0):
    """For given query return (results, next_offset)"""

    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []

    if USE_CAPTION_FILTER:
        filter = {'$or': [{'file_name': regex}, {'caption': regex}]}
    else:
        filter = {'file_name': regex}

    if file_type:
        filter['file_type'] = file_type

    total_results = await Media.count_documents(filter)
    next_offset = offset + max_results

    if next_offset > total_results:
        next_offset = ''

    cursor = Media.find(filter)
    # Sort by recent
    cursor.sort('$natural', -1)
    # Slice files according to offset and max results
    cursor.skip(offset).limit(max_results)
    # Get list of files
    files = await cursor.to_list(length=max_results)

    return files, next_offset
def get_file_id(msg: Message):
    if msg.media:
        for message_type in (
            "photo",
            "animation",
            "audio",
            "document",
            "video",
            "video_note",
            "voice",
            "sticker"
        ):
            obj = getattr(msg, message_type)
            if obj:
                setattr(obj, "message_type", message_type)
                return obj
async def broadcast_messages(user_id, message):
    try:
        await message.copy(chat_id=user_id)
        return True, "Succes"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message)
    except InputUserDeactivated:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id}-Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        logging.info(f"{user_id} -Blocked the bot.")
        return False, "Blocked"
    except PeerIdInvalid:
        await db.delete_user(int(user_id))
        logging.info(f"{user_id} - PeerIdInvalid")
        return False, "Error"
    except Exception as e:
        return False, "Error"


async def get_filter_results(query):
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return []
    filter = {'file_name': regex}
    total_results = await Media.count_documents(filter)
    cursor = Media.find(filter)
    cursor.sort('$natural', -1)
    files = await cursor.to_list(length=int(total_results))
    return files

async def get_file_details(query):
    filter = {'file_id': query}
    cursor = Media.find(filter)
    filedetails = await cursor.to_list(length=1)
    return filedetails

async def is_subscribed(bot, query):
    try:
        user = await bot.get_chat_member(AUTH_CHANNEL, query.from_user.id)
    except UserNotParticipant:
        pass
    except Exception as e:
        logger.exception(e)
    else:
        if not user.status == 'kicked':
            return True

    return False

async def get_poster(movie):
    extract = PTN.parse(movie)
    try:
        title=extract["title"]
    except KeyError:
        title=movie
    try:
        year=extract["year"]
        year=int(year)
    except KeyError:
        year=None
    if year:
        filter = {'$and': [{'title': str(title).lower().strip()}, {'year': int(year)}]}
    else:
        filter = {'title': str(title).lower().strip()}
    cursor = Poster.find(filter)
    is_in_db = await cursor.to_list(length=1)
    poster=None
    if is_in_db:
        for nyav in is_in_db:
            poster=nyav.poster
    else:
        if year:
            url=f'https://www.omdbapi.com/?s={title}&y={year}&apikey={API_KEY}'
        else:
            url=f'https://www.omdbapi.com/?s={title}&apikey={API_KEY}'
        try:
            n = requests.get(url)
            a = json.loads(n.text)
            if a["Response"] == 'True':
                y = a.get("Search")[0]
                v=y.get("Title").lower().strip()
                poster = y.get("Poster")
                year=y.get("Year")[:4]
                id=y.get("imdbID")
                await get_all(a.get("Search"))
        except Exception as e:
            logger.exception(e)
            pass
    return poster


async def get_all(list):
    for y in list:
        v=y.get("Title").lower().strip()
        poster = y.get("Poster")
        year=y.get("Year")[:4]
        id=y.get("imdbID")
        await save_poster(id, v, year, poster)

def last_online(from_user):
    time = ""
    if from_user.is_bot:
        time += "🤖 Bot :("
    elif from_user.status == 'recently':
        time += "Recently"
    elif from_user.status == 'within_week':
        time += "Within the last week"
    elif from_user.status == 'within_month':
        time += "Within the last month"
    elif from_user.status == 'long_time_ago':
        time += "A long time ago :("
    elif from_user.status == 'online':
        time += "Currently Online"
    elif from_user.status == 'offline':
        time += datetime.fromtimestamp(from_user.last_online_date).strftime("%a, %d %b %Y, %H:%M:%S")
    return time

def split_quotes(text: str) -> List:
    if not any(text.startswith(char) for char in START_CHAR):
        return text.split(None, 1)
    counter = 1  # ignore first char -> is some kind of quote
    while counter < len(text):
        if text[counter] == "\\":
            counter += 1
        elif text[counter] == text[0] or (text[0] == SMART_OPEN and text[counter] == SMART_CLOSE):
            break
        counter += 1
    else:
        return text.split(None, 1)

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0

    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0

            r += bytes([i])

    return base64.urlsafe_b64encode(r).decode().rstrip("=")


def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")


def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref


def get_size(size):
    """Get size in readable format"""

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])
def parser(text, keyword):
    if "buttonalert" in text:
        text = (text.replace("\n", "\\n").replace("\t", "\\t"))
    buttons = []
    note_data = ""
    prev = 0
    i = 0
    alerts = []
    for match in BTN_URL_REGEX.finditer(text):
        # Check if btnurl is escaped
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        # if even, not escaped -> create button
        if n_escapes % 2 == 0:
            note_data += text[prev:match.start(1)]
            prev = match.end(1)
            if match.group(3) == "buttonalert":
                # create a thruple with button label, url, and newline status
                if bool(match.group(5)) and buttons:
                    buttons[-1].append(InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"alertmessage:{i}:{keyword}"
                    ))
                else:
                    buttons.append([InlineKeyboardButton(
                        text=match.group(2),
                        callback_data=f"alertmessage:{i}:{keyword}"
                    )])
                i += 1
                alerts.append(match.group(4))
            elif bool(match.group(5)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                ))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(4).replace(" ", "")
                )])

        else:
            note_data += text[prev:to_check]
            prev = match.start(1) - 1
    else:
        note_data += text[prev:]

    try:
        return note_data, buttons, alerts
    except:
        return note_data, buttons, None
