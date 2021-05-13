from typing import Tuple
from pyrogram import (Client, filters, emoji)
from pyrogram.methods.auth import connect
from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                            CallbackQuery, Message, ReplyKeyboardMarkup)

import yaml, os, time, asyncio
from filesize import naturalsize

BOT_USER = None
CONFIG_FOLDER_PATH = './config/'
DATA_FOLDER_PATH = './data/'
CONFIG_PATH = os.path.join(CONFIG_FOLDER_PATH, 'config.yml')
SPLIT_FILE_SIZE = 100 * 1024 * 1024

# Read config file
with open(CONFIG_PATH, 'r') as file:
    CONFIG = yaml.load(file.read(), Loader=yaml.Loader)

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

@app.on_callback_query(~filters.bot & filters.regex('^split .*$'))
async def split_file(client: Client, callback_query: CallbackQuery):
    user = callback_query.from_user.id
    _, _, message_id = callback_query.data.partition(' ')
    file_message = await app.get_messages(user, int(message_id))
    local_path = None

    try:
        message = await app.send_message(user, f"{emoji.HOURGLASS_DONE} Downloading from Telegram: 0%")
        local_path = await file_message.download(file_name=DATA_FOLDER_PATH,
                                                block=True,
                                                progress=progress_update,
                                                progress_args=(client, message, message_id, f"{emoji.HOURGLASS_DONE} Downloading from Telegram"))
        if not local_path:
            raise Exception()

        name = os.path.basename(local_path)
        k = 0
        with open(local_path, 'rb') as localfile:
            while True:
                data = localfile.read(SPLIT_FILE_SIZE)
                    
                if not data: # not more data
                    break

                # write part
                partname = f"{name}.part{k}"
                partpath = os.path.join(DATA_FOLDER_PATH, partname)
                with open(partpath, 'wb') as partfile:
                    partfile.write(data)
                await app.send_document(user, 
                                        document=partpath, 
                                        progress=progress_update,
                                        progress_args=(client, message, message_id, f"{emoji.HOURGLASS_DONE} Uploading **Piece #{k}**"))
                k = k + 1 # advance part count
                os.unlink(partpath)
        await message.edit_text(f"{emoji.CHECK_MARK_BUTTON} File successful uploaded")        
    except Exception:
        await app.send_message(user, f"{emoji.CROSS_MARK} Error while try upload file")
        return
    finally:
        if local_path:
            os.unlink(local_path) 
        CACHE_DOWNLOAD_CURSOR.pop(message_id, None)

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
