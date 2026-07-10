from pyrogram import Client, filters
from files import config

# ---------- أمر مين مشغل ----------

@Client.on_message(filters.command(["مين مشغل"], prefixes=["", "/", "!"]) & filters.group)
async def who_playing_cmd(client, message):
    chat_id = message.chat.id
    if not config.is_playing_now.get(chat_id):
        return await message.reply("لا يوجد شيء قيد التشغيل حالياً")
    
    current = config.current_playing.get(chat_id, {})
    requester = current.get("requester", "غير معروف")
    title = current.get("title", "غير معروف")
    await message.reply(f"المقطع الحالي: {title}\nتم التشغيل بواسطة: {requester}")