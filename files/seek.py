# files/seek.py

import os
import time
import asyncio
from pyrogram import Client, filters
from pytgcalls.types import MediaStream
from files import config
from files.utils import check_disabled, play_next, is_admin

def get_user_mention(message):
    if message.from_user:
        return message.from_user.mention
    elif message.sender_chat:
        return f"[{message.sender_chat.title}](tg://user?id={message.sender_chat.id})"
    return "مجهول"

@Client.on_message(filters.command(["مرر", "رجع"], prefixes=["", "/", "!"]) & ~filters.private)
async def seek_cmds(client, message):
    if await check_disabled(client, message): return
    if not await is_admin(client, message, check_player=True): return  
    chat_id = message.chat.id
    if not config.call_py or not config.is_playing_now.get(chat_id):
        return await message.reply("لا يوجد بث حالياً")

    try: 
        seconds = int(message.command[1])
    except: 
        return await message.reply("يرجى كتابة عدد الثواني بعد الأمر، مثلاً: مرر 50")

    cmd = message.command[0]
    current_time = config.playback_offset.get(chat_id, 0) + (time.time() - config.playback_start_time.get(chat_id, time.time()))

    if cmd == "مرر":
        target = current_time + seconds
        direction = "تقديم"
    else:
        target = max(0, current_time - seconds)
        direction = "إرجاع"

    msg = await message.reply(f"جاري {direction} الأغنية...")
    await perform_seek(chat_id, target, msg, get_user_mention(message))

async def perform_seek(chat_id, target_time, msg, user_mention):
    track = config.current_playing.get(chat_id)
    if not track: return
    duration = track.get("duration", 0)

    if duration > 0 and target_time >= duration:
        await msg.edit(f"التمرير تخطى مدة الأغنية، تم التخطي بواسطة {user_mention}")
        return await play_next(chat_id, force_skip=True)

    original_path = track.get("original_path", track["path"])
    if not os.path.exists(original_path):
        await msg.delete()
        return await play_next(chat_id, force_skip=True)

    is_vid = track.get("type") == "video"
    ext = "mp4" if is_vid else "m4a"
    temp_path = f"downloads/seek_{chat_id}_{int(target_time)}.{ext}"

    if is_vid:
        cmd = f'ffmpeg -hide_banner -loglevel error -y -ss {target_time} -i "{original_path}" -map 0 -c copy -avoid_negative_ts make_zero -fflags +genpts "{temp_path}"'
    else:
        cmd = f'ffmpeg -hide_banner -loglevel error -y -ss {target_time} -i "{original_path}" -c copy "{temp_path}"'

    try:
        process = await asyncio.create_subprocess_shell(cmd)
        await asyncio.wait_for(process.communicate(), timeout=15)
    except Exception as e:
        await msg.delete()
        return await play_next(chat_id, force_skip=True)

    if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
        config.is_seeking[chat_id] = True
        try:
            stream_obj = MediaStream(temp_path)
            try: 
                await config.call_py.change_stream(chat_id, stream_obj)
            except: 
                await config.call_py.play(chat_id, stream_obj)

            config.playback_offset[chat_id] = target_time
            config.playback_start_time[chat_id] = time.time()
            config.current_playing[chat_id]["path"] = temp_path
            await msg.edit(f"تم التمرير بنجاح بواسطة {user_mention}")
        except: 
            await msg.delete()
            await play_next(chat_id, force_skip=True)

        await asyncio.sleep(1.5)
        config.is_seeking[chat_id] = False
    else: 
        await msg.delete()
        await play_next(chat_id, force_skip=True)
