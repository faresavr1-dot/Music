import asyncio
import os
from pyrogram import Client, filters
from files import config
from files.youtube import get_youtube_info, download_youtube_file, background_upload_by_id


@Client.on_message(filters.command(["يوت", "تحميل"], prefixes=["", "/", "!"]) & filters.group)
async def youtube_download_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply("استخدم: يوت + اسم الأغنية")

    query = message.text.split(" ", 1)[1].strip()
    search_q = query.lower()
    cache_dict = config.bot_cache.get("audio", {})

    cached_msg_id = None
    for key, msg_id in cache_dict.items():
        if search_q in key.lower():
            cached_msg_id = msg_id
            break

    if cached_msg_id and config.STORAGE_CHANNEL_ID:
        try:
            cached_msg = await client.get_messages(config.STORAGE_CHANNEL_ID, cached_msg_id)
            if cached_msg and cached_msg.audio:
                return await message.reply_audio(
                    cached_msg.audio.file_id,
                    title=cached_msg.audio.title or query,
                    performer=cached_msg.audio.performer or "YouTube"
                )
            elif cached_msg and cached_msg.document:
                return await message.reply_document(cached_msg.document.file_id)
        except Exception:
            pass

    yt_info = await asyncio.to_thread(get_youtube_info, query)
    if not yt_info:
        return await message.reply("لم يتم العثور على نتائج")

    yt_id = yt_info["id"]
    title = yt_info["title"]

    if yt_id in cache_dict and config.STORAGE_CHANNEL_ID:
        try:
            cached_msg = await client.get_messages(config.STORAGE_CHANNEL_ID, cache_dict[yt_id])
            if cached_msg and cached_msg.audio:
                return await message.reply_audio(
                    cached_msg.audio.file_id,
                    title=cached_msg.audio.title or title,
                    performer=cached_msg.audio.performer or "YouTube"
                )
            elif cached_msg and cached_msg.document:
                return await message.reply_document(cached_msg.document.file_id)
        except Exception:
            pass

    status_msg = await message.reply("جاري التحميل...")

    try:
        media_path = await asyncio.to_thread(download_youtube_file, yt_info["url"], is_video=False)
    except Exception as e:
        return await status_msg.edit(f"فشل التحميل: {str(e)}")

    if not media_path or not os.path.exists(media_path):
        return await status_msg.edit("فشل التحميل: الملف غير موجود")

    await status_msg.edit("جاري الإرسال...")

    try:
        await message.reply_audio(media_path, title=title, performer="YouTube")
        await status_msg.delete()
    except Exception as e:
        return await status_msg.edit(f"فشل الإرسال: {str(e)}")

    asyncio.create_task(background_upload_by_id(client, media_path, yt_id, title, is_video=False))
