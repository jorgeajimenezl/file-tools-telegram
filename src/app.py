from typing import Tuple
from pyrogram import (Client, filters, emoji)
from pyrogram.methods.auth import connect
from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                            CallbackQuery, Message, ReplyKeyboardMarkup)

import yaml, os, time, asyncio, tempfile, traceback
from filesize import naturalsize

BOT_USER = None
CONFIG_FOLDER_PATH = './config/'
DATA_FOLDER_PATH = './data/'
CONFIG_PATH = os.path.join(CONFIG_FOLDER_PATH, 'config.yml')
SPLIT_FILE_SIZE = 100 * 1024 * 1024

# Read config file
with open(CONFIG_PATH, 'r') as file:
    CONFIG = yaml.load(file.read(), Loader=yaml.Loader)

if not os.path.exists(DATA_FOLDER_PATH):
    os.mkdir(DATA_FOLDER_PATH)

app = Client('deverlop',
             api_id=CONFIG['telegram']['api-id'],
             api_hash=CONFIG['telegram']['api-hash'],
             bot_token=CONFIG['telegram']['bot-token'])
    
CACHE_DOWNLOAD_CURSOR = { }

async def progress_update(current, total, *args):
    _, message, message_id, text = args
    lastTime = CACHE_DOWNLOAD_CURSOR.pop(message_id, None)
    now = time.time()
    if lastTime != None and (now - lastTime) < 5.0:
        return
    
    CACHE_DOWNLOAD_CURSOR[message_id] = now
    s = f"{text}: ({naturalsize(current)}/{naturalsize(total)})"
    if message.text != s:
        await message.edit_text(s)

@app.on_message(filters.document | filters.photo | filters.video | filters.audio)
async def file_options(client: Client, message: Message):
    user = message.from_user.id
    await app.send_message(user,
                        f"What's do you do with this file?",
                            reply_markup=InlineKeyboardMarkup([
                                [InlineKeyboardButton(f"Split {emoji.KITCHEN_KNIFE}", callback_data=f'split {message.message_id}')],
                                [InlineKeyboardButton(f"Compress {emoji.FILE_FOLDER}", callback_data=f'zip {message.message_id}')]
                           ]))

def get_file_name(message: Message):
    available_media = ("audio", "document", "photo", "sticker", "animation", "video", "voice", "video_note", "new_chat_photo")
    if isinstance(message, Message):
        for kind in available_media:
            media = getattr(message, kind, None)

            if media is not None:
                break
        else:
            raise ValueError("This message doesn't contain any downloadable media")
    else:
        media = message

    return getattr(media, "file_name", 'random.zip')

@app.on_callback_query(~filters.bot & filters.regex('^split .*$'))
async def split_file(client: Client, callback_query: CallbackQuery):
    user = callback_query.from_user.id
    _, _, message_id = callback_query.data.partition(' ')
    file_message = await app.get_messages(user, int(message_id))
    file_path = None
    fp = None

    try:
        message = await app.send_message(user, f"{emoji.HOURGLASS_DONE} Downloading from Telegram: 0%")
        name = get_file_name(file_message)
        file_path = os.path.join(DATA_FOLDER_PATH, name)

        fp = open(file_path, 'w+b')
        current = 0
        k = 0

        async for chunk, offset, total in file_message.iter_download():
            # manual call to report download progress
            await progress_update(offset, total, client, message, message_id, f"{emoji.HOURGLASS_DONE} Downloading from Telegram")

            fp.write(chunk)
            fp.flush()

            current += len(chunk)

            # reach size limit
            if current > SPLIT_FILE_SIZE:
                # send downloaded part
                current = 0             
                await app.send_document(user, 
                                        document=fp,
                                        file_name=f"{name}.part{k}",
                                        progress=progress_update,
                                        progress_args=(client, message, message_id, f"{emoji.HOURGLASS_DONE} Uploading **Piece #{k}**")
                                    )

                # TODO: Fix bug in pyrogram that close underline file when that is used in send_document function
                # Opening file again
                fp = open(file_path, 'w+b')  
                k = k + 1

        # had some bytes to write
        if current != 0:
            current = 0
            await app.send_document(user, 
                                    document=fp,
                                    file_name=f"{name}.part{k}",
                                    progress=progress_update,
                                    progress_args=(client, message, message_id, f"{emoji.HOURGLASS_DONE} Uploading **Piece #{k}**")
                                )
                                
        await message.edit_text(f"{emoji.CHECK_MARK_BUTTON} File successful splited")        
    except Exception as e:
        await app.send_message(user, f"{emoji.CROSS_MARK} Error while try upload file")
        tb = traceback.format_exc()
        await app.send_message(user, f"Error: {tb}")
    finally:
        CACHE_DOWNLOAD_CURSOR.pop(message_id, None)

        if fp:
            fp.close()

        if file_path:
            try:
                os.remove(file_path)
            except Exception:
                pass        

async def main():
    async with app:
        # TODO: add something
        global BOT_USER
        BOT_USER = await app.get_me()

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("Stoped!!! ...")

if __name__ == "__main__":
    app.run(main())
