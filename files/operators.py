# files/players.py

from pyrogram import Client, filters
from files import config
from files.utils import is_admin, check_disabled

async def get_target(client, message):
    if message.reply_to_message:
        return message.reply_to_message.from_user
    if len(message.command) > 1:
        target = message.command[1]
        try:
            if target.isdigit():
                return await client.get_users(int(target))
            else:
                return await client.get_users(target)
        except:
            return None
    return None

@Client.on_message(filters.command(["رفع مشغل"], prefixes=["", "/", "!"]) & ~filters.private)
async def promote_player(client, message):
    if await check_disabled(client, message): return
    # هنا بنمنع المشغل إنه يرفع مشغل زيه (لازم مشرف أو أدمن)
    if not await is_admin(client, message, check_player=False, show_error=True):
        return
        
    target_user = await get_target(client, message)
    if not target_user:
        return await message.reply("📌 يرجى الرد على الشخص أو كتابة المعرف/الايدي بعد الأمر.")
        
    chat_id = str(message.chat.id)
    user_id = target_user.id
    
    if "custom_players" not in config.bot_cache:
        config.bot_cache["custom_players"] = {}
    if chat_id not in config.bot_cache["custom_players"]:
        config.bot_cache["custom_players"][chat_id] = []
        
    if user_id not in config.bot_cache["custom_players"][chat_id]:
        config.bot_cache["custom_players"][chat_id].append(user_id)
        config.save_cache()
        await message.reply(f"✅ تم رفع {target_user.mention} كـ (مشغل) بنجاح.\nيمكنه الآن استخدام أوامر وأزرار التشغيل بحرية.")
    else:
        await message.reply(f"⚠️ {target_user.mention} هو مشغل بالفعل.")

@Client.on_message(filters.command(["تنزيل مشغل"], prefixes=["", "/", "!"]) & ~filters.private)
async def demote_player(client, message):
    if await check_disabled(client, message): return
    if not await is_admin(client, message, check_player=False, show_error=True):
        return
        
    target_user = await get_target(client, message)
    if not target_user:
        return await message.reply("📌 يرجى الرد على الشخص أو كتابة المعرف/الايدي بعد الأمر.")
        
    chat_id = str(message.chat.id)
    user_id = target_user.id
    
    if "custom_players" in config.bot_cache and chat_id in config.bot_cache["custom_players"]:
        if user_id in config.bot_cache["custom_players"][chat_id]:
            config.bot_cache["custom_players"][chat_id].remove(user_id)
            config.save_cache()
            return await message.reply(f"✅ تم تنزيل {target_user.mention} من قائمة المشغلين بنجاح.")
            
    await message.reply(f"⚠️ {target_user.mention} ليس مشغلاً من الأساس.")
