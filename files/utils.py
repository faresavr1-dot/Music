# files/utils.py

import os
import time
import asyncio
from pytgcalls.types import MediaStream
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatType, ChatMemberStatus
from files import config

def get_play_buttons():
    """الأزرار النهائية بالترتيب المطلوب"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Ⅱ", callback_data="music_pause"),
            InlineKeyboardButton("▸", callback_data="music_resume"),
            InlineKeyboardButton("↻", callback_data="music_repeat"),
            InlineKeyboardButton("▸▸", callback_data="music_skip"),
            InlineKeyboardButton("□", callback_data="music_stop")
        ],
        [
            InlineKeyboardButton("𝐒𝐎𝐔𝐑𝐂𝐄", url="https://t.me/AY_WV"),
            InlineKeyboardButton("𝐆𝐑𝐎𝐔𝐏", url="https://t.me/O1_ZO")
        ],
        [
            InlineKeyboardButton("𝐀𝐃𝐃 𝐆𝐑𝐎𝐔𝐏", url="https://t.me/fares_V_bot?startgroup=true")
        ]
    ])

async def check_disabled(client, message):
    if message.chat and message.chat.id in config.bot_cache.get("disabled_groups", []):
        try:
            dev = await client.get_users(config.OWNER_ID)
            dev_name = f"[{dev.first_name}](tg://user?id={config.OWNER_ID})"
        except:
            dev_name = f"[المطور](tg://user?id={config.OWNER_ID})"
        await message.reply(f"تم تعطيل البوت بواسطة المطور.\nراسل {dev_name} للتفعيل.", disable_web_page_preview=True)
        return True
    return False

async def send_playing_caption(chat_id, track):
    """كليشة التشغيل"""
    bot_image = config.bot_cache.get("bot_image")
    title = track.get("title", "غير معروف")
    dur_str = track.get("duration_str", "00:00")
    requester = track.get("requester", "غير معروف")
    
    caption = (
        f"▶️ **تم التشغيل**\n\n"
        f"🎵 **العنوان:** {title}\n"
        f"⏱ **المدة:** {dur_str}\n"
        f"👤 **بواسطة:** {requester}"
    )
    
    try:
        if bot_image:
            await config.bot.send_photo(chat_id, photo=bot_image, caption=caption, reply_markup=get_play_buttons())
        else:
            await config.bot.send_message(chat_id, caption, reply_markup=get_play_buttons())
    except:
        pass

async def play_next(chat_id, force_skip=False):
    if chat_id in config.current_playing and config.current_playing[chat_id]:
        old_path = config.current_playing[chat_id].get("path", "")
        if "seek_" in old_path and os.path.exists(old_path):
            try: os.remove(old_path)
            except: pass

    if not force_skip and config.repeat_mode.get(chat_id) and config.current_playing.get(chat_id):
        next_track = config.current_playing[chat_id]
    elif chat_id in config.music_queue and config.music_queue[chat_id]:
        next_track = config.music_queue[chat_id].pop(0)
    else:
        config.current_playing[chat_id] = None
        config.is_playing_now[chat_id] = False
        try: await config.call_py.leave_call(chat_id)
        except: pass
        return

    config.current_playing[chat_id] = next_track
    config.is_playing_now[chat_id] = True
    config.playback_start_time[chat_id] = time.time()
    config.playback_offset[chat_id] = 0
    
    try:
        stream_obj = MediaStream(next_track["path"])
        try: await config.call_py.change_stream(chat_id, stream_obj)
        except: await config.call_py.play(chat_id, stream_obj)
        
        await send_playing_caption(chat_id, next_track)
    except:
        await play_next(chat_id, force_skip=force_skip)

def setup_pytgcalls_handlers():
    @config.call_py.on_update()
    async def update_handler(client, update):
        update_name = type(update).__name__
        chat_id = getattr(update, "chat_id", None)
        if chat_id and any(x in update_name.lower() for x in ["ended", "end", "stopped", "finished"]):
            if not config.is_seeking.get(chat_id) and config.is_playing_now.get(chat_id):
                await play_next(chat_id)

# ================== دوال التحقق الجديدة ==================
async def check_privilege(client, chat_id, user_id, check_player=False):
    """دالة خفيفة وسريعة للتحقق من الصلاحية (تم مسح أدمن البوت)"""
    if user_id == config.OWNER_ID: return True
    
    chat_str = str(chat_id)
        
    # مشغل البوت (لو مسموح بالتحقق منه للأوامر المتعلقة بالتشغيل)
    if check_player and chat_str in config.bot_cache.get("custom_players", {}) and user_id in config.bot_cache["custom_players"][chat_str]:
        return True
        
    # مشرف أساسي في الجروب
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            return True
    except:
        pass
        
    return False

async def is_admin(client, message, check_player=False, show_error=True):
    """دالة التحقق الخاصة بالرسائل والأوامر"""
    if getattr(message.chat, "type", None) == ChatType.CHANNEL or getattr(message, "sender_chat", None):
        return True
        
    user_id = message.from_user.id if message.from_user else None
    if not user_id: return False
    
    chat_id = message.chat.id
    
    has_priv = await check_privilege(client, chat_id, user_id, check_player)
    
    if not has_priv and show_error:
        # هنا التعديل
        await message.reply(f"❥ عذرا هذا الامر لايخصك")
        
    return has_priv
