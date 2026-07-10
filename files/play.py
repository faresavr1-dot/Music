# files/play.py

import time
import asyncio
import os
from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from telethon.tl.functions.messages import ImportChatInviteRequest
from pytgcalls.types import MediaStream

from files import config
from files.youtube import get_youtube_info, download_youtube_file, get_cached_file_id, background_upload_by_id
from files.utils import check_disabled, send_playing_caption, get_play_buttons, is_admin

def get_user_mention(message):
    if message.from_user:
        return message.from_user.mention
    elif message.sender_chat:
        return f"[{message.sender_chat.title}](tg://user?id={message.sender_chat.id})"
    return "مجهول"

@Client.on_message(filters.command(["تشغيل", "شغل", "فيديو", "فيد"], prefixes=["", "/", "!"]) & ~filters.private)
async def play_command(client, message):
    if await check_disabled(client, message): return
    if not await is_admin(client, message, check_player=True): return
    if not config.call_py or not config.assistant_id:
        return await message.reply("المساعد غير متصل")

    status_msg = await message.reply("جاري التشغيل...")

    chat_id = message.chat.id
    is_video = message.command[0] in ["فيديو", "فيد"]

    media_path = title = duration = None

    # تشغيل ملف من رد
    if message.reply_to_message and getattr(message.reply_to_message, 'media', None):
        obj = message.reply_to_message.audio or message.reply_to_message.voice or message.reply_to_message.video
        title = getattr(obj, "title", "مقطع محلي")
        duration = getattr(obj, "duration", 0)
        ext = "mp4" if is_video else "mp3"
        media_path = await message.reply_to_message.download(file_name=f"downloads/reply_{chat_id}.{ext}")
    else:
        if len(message.command) < 2:
            return await status_msg.edit("يرجى كتابة اسم الأغنية بعد الأمر")

        query = message.text.split(" ", 1)[1].strip()

        yt_info = await asyncio.to_thread(get_youtube_info, query)
        if not yt_info:
            return await status_msg.edit("لم يتم العثور على نتائج")

        yt_id = yt_info["id"]
        title = yt_info["title"]
        duration = yt_info["duration"]

        cached_file_id = await get_cached_file_id(client, yt_id, is_video)

        if cached_file_id:
            ext = "mp4" if is_video else "mp3"
            media_path = await client.download_media(
                cached_file_id,
                file_name=f"downloads/cached_{yt_id}.{ext}"
            )
            if not media_path:
                return await status_msg.edit("فشل تحميل الملف من التخزين")
        else:
            media_path = await asyncio.to_thread(download_youtube_file, yt_info["url"], is_video)
            if not media_path:
                return await status_msg.edit("فشل التحميل من يوتيوب")
            asyncio.create_task(background_upload_by_id(client, media_path, yt_id, title, is_video))

    try:
        await client.get_chat_member(chat_id, config.assistant_id)
    except UserNotParticipant:
        try:
            link = await client.export_chat_invite_link(chat_id)
            invite = link.split("/")[-1].replace("+", "")
            await config.assistant_client(ImportChatInviteRequest(invite))
        except:
            pass

    user_mention = get_user_mention(message)
    mins, secs = divmod(duration or 0, 60)
    dur_str = f"{mins:02d}:{secs:02d}"

    track_info = {
        "path": media_path,
        "original_path": media_path,
        "title": title,
        "type": "video" if is_video else "audio",
        "duration": duration or 0,
        "duration_str": dur_str,
        "requester": user_mention
    }

    if config.is_playing_now.get(chat_id):
        queue = config.music_queue.setdefault(chat_id, [])
        queue.append(track_info)
        position = len(queue)
        await status_msg.delete()
        cap = f"تمت الاضافة للطابور #{position}\n\n{title}\n{dur_str}\n{user_mention}"
        await message.reply(cap, reply_markup=get_play_buttons())
    else:
        config.current_playing[chat_id] = track_info
        config.is_playing_now[chat_id] = True
        config.playback_start_time[chat_id] = time.time()
        config.playback_offset[chat_id] = 0

        try:
            # التعديل الجذري هنا: فصل الصوت عن الفيديو في البث
            if is_video:
                # لو طلب فيديو، نفتح الشاشة عادي
                stream = MediaStream(media_path)
            else:
                # لو طلب صوت، نجبر المكتبة تقفل مشاركة الشاشة تماماً
                stream = MediaStream(media_path, video_flags=MediaStream.Flags.IGNORE)

            await config.call_py.play(chat_id, stream)
            await status_msg.delete()
            await send_playing_caption(chat_id, track_info)
        except Exception as e:
            config.is_playing_now[chat_id] = False
            await status_msg.edit(f"حدث خطأ اثناء التشغيل: {e}")
