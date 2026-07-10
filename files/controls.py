# files/controls.py

import time
from pyrogram import Client, filters
from files import config
from files.utils import check_disabled, play_next, get_play_buttons, is_admin, check_privilege

def get_user_mention(message):
    if message.from_user:
        return message.from_user.mention
    elif message.sender_chat:
        return f"[{message.sender_chat.title}](tg://user?id={message.sender_chat.id})"
    return "مجهول"

# ================= أوامر نصية =================
@Client.on_message(filters.command(["إيقاف", "ايقاف", "اسكت"], prefixes=["", "/", "!"]) & ~filters.private)
async def stop_command(client, message):
    if await check_disabled(client, message): return
    if not await is_admin(client, message, check_player=True): return
    chat_id = message.chat.id
    if not config.is_playing_now.get(chat_id):
        return await message.reply("لا يوجد بث حالياً.")
    config.music_queue[chat_id] = []
    config.repeat_mode[chat_id] = False
    config.current_playing[chat_id] = None
    config.is_playing_now[chat_id] = False
    try: await config.call_py.leave_call(chat_id)
    except: pass
    await message.reply(f"تم الإيقاف بواسطة {get_user_mention(message)}")

@Client.on_message(filters.command(["تخطي"], prefixes=["", "/", "!"]) & ~filters.private)
async def skip_cmd(client, message):
    if await check_disabled(client, message): return
    if not await is_admin(client, message, check_player=True): return
    chat_id = message.chat.id
    if not config.is_playing_now.get(chat_id):
        return await message.reply("لا يوجد شيء للتخطي")
    current = config.current_playing.get(chat_id, {})
    title = current.get("title", "غير معروف")
    await message.reply(f"تم التخطي: {title} بواسطة {get_user_mention(message)}")
    await play_next(chat_id, force_skip=True)

@Client.on_message(filters.command(["كرر"], prefixes=["", "/", "!"]) & ~filters.private)
async def repeat_cmd(client, message):
    if await check_disabled(client, message): return
    if not await is_admin(client, message, check_player=True): return
    chat_id = message.chat.id
    current = config.current_playing.get(chat_id)
    if not current: 
        return await message.reply("لا يوجد أغنية حالياً")
    if chat_id not in config.music_queue: 
        config.music_queue[chat_id] = []
    config.music_queue[chat_id].append(current)
    position = len(config.music_queue[chat_id])

    title = current.get("title", "غير معروف")
    dur_str = current.get("duration_str", "00:00")
    requester = current.get("requester", "غير معروف")

    await message.reply(
        f"تمت الاضافة للطابور #{position}\n\n{title}\n{dur_str}\n{requester}",
        reply_markup=get_play_buttons()
    )

@Client.on_message(filters.command(["وقف", "كمل"], prefixes=["", "/", "!"]) & ~filters.private)
async def pause_resume_cmds(client, message):
    if await check_disabled(client, message): return
    if not await is_admin(client, message, check_player=True): return
    chat_id = message.chat.id
    if not config.is_playing_now.get(chat_id):
        return await message.reply("لا يوجد بث حالياً")
    cmd = message.command[0]
    try:
        if cmd == "وقف":
            await config.call_py.pause(chat_id)
            config.playback_offset[chat_id] = config.playback_offset.get(chat_id, 0) + (time.time() - config.playback_start_time.get(chat_id, time.time()))
            await message.reply(f"تم الإيقاف المؤقت بواسطة {get_user_mention(message)}")
        elif cmd == "كمل":
            await config.call_py.resume(chat_id)
            config.playback_start_time[chat_id] = time.time()
            await message.reply(f"تم الاستئناف بواسطة {get_user_mention(message)}")
    except: 
        await message.reply("حدث خطأ أثناء تنفيذ الأمر.")

# ================= أزرار التحكم (تم الإصلاح الدقيق) =================
@Client.on_callback_query(filters.regex(r"^music_(pause|resume|stop|skip|repeat)$"))
async def music_buttons_handler(client, callback_query):
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id
    data = callback_query.data
    user = callback_query.from_user.mention
    
    # التحقق المباشر من هوية من ضغط الزر (وليس هوية البوت)
    if not await check_privilege(client, chat_id, user_id, check_player=True):
        await callback_query.answer("❥ عذرا هذا الامر لايخصك ", show_alert=True)
        return

    if not config.is_playing_now.get(chat_id):
        await callback_query.answer("عذراً لا يوجد بث حالياً", show_alert=True)
        return

    if data == "music_pause":
        try:
            await config.call_py.pause(chat_id)
            config.playback_offset[chat_id] = config.playback_offset.get(chat_id, 0) + (time.time() - config.playback_start_time.get(chat_id, time.time()))
            await callback_query.answer("تم الإيقاف المؤقت")
            await callback_query.message.reply(f"تم إيقاف البث مؤقتاً بواسطة {user}")
        except:
            await callback_query.answer("خطأ في الإيقاف المؤقت", show_alert=True)

    elif data == "music_resume":
        try:
            await config.call_py.resume(chat_id)
            config.playback_start_time[chat_id] = time.time()
            await callback_query.answer("تم الاستئناف")
            await callback_query.message.reply(f"تم استئناف البث بواسطة {user}")
        except:
            await callback_query.answer("خطأ في الاستئناف", show_alert=True)

    elif data == "music_stop":
        config.music_queue[chat_id] = []
        config.current_playing[chat_id] = None
        config.is_playing_now[chat_id] = False
        try: await config.call_py.leave_call(chat_id)
        except: pass
        await callback_query.answer("تم الإيقاف")
        await callback_query.message.reply(f"تم إيقاف التشغيل بواسطة {user}")

    elif data == "music_skip":
        if not config.is_playing_now.get(chat_id):
            return await callback_query.answer("لا يوجد شيء للتخطي", show_alert=True)
        current = config.current_playing.get(chat_id, {})
        title = current.get("title", "غير معروف")
        await callback_query.answer("تم التخطي")
        await callback_query.message.reply(f"تم التخطي: {title} بواسطة {user}")
        await play_next(chat_id, force_skip=True)

    elif data == "music_repeat":
        if not config.is_playing_now.get(chat_id):
            return await callback_query.answer("لا يوجد أغنية حالياً", show_alert=True)
        current = config.current_playing.get(chat_id)
        if chat_id not in config.music_queue:
            config.music_queue[chat_id] = []
        config.music_queue[chat_id].append(current)
        position = len(config.music_queue[chat_id])

        title = current.get("title", "غير معروف")
        dur_str = current.get("duration_str", "00:00")
        requester = current.get("requester", "غير معروف")

        await callback_query.message.reply(
            f"تمت الاضافة للطابور #{position}\n\n{title}\n{dur_str}\n{requester}",
            reply_markup=get_play_buttons()
        )
        await callback_query.answer("تم التكرار")
