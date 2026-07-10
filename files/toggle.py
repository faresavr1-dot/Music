# files/toggle.py
from pyrogram import Client, filters
from files import config

@Client.on_message(filters.command(["تعطيل", "تفعيل"], prefixes=["", "/", "!"]) & filters.group)
async def toggle_group(client, message):
    if message.from_user.id != config.OWNER_ID: 
        return
        
    cmd = message.command[0]
    chat_id = message.chat.id

    if "disabled_groups" not in config.bot_cache:
        config.bot_cache["disabled_groups"] = []

    if cmd == "تعطيل":
        if chat_id not in config.bot_cache["disabled_groups"]:
            config.bot_cache["disabled_groups"].append(chat_id)
            config.save_cache()
        await message.reply("🚫 تم تعطيل البوت في هذه المجموعة نهائياً.")
        
    elif cmd == "تفعيل":
        if chat_id in config.bot_cache["disabled_groups"]:
            config.bot_cache["disabled_groups"].remove(chat_id)
            config.save_cache()
        await message.reply("✅ تم تفعيل البوت في هذه المجموعة بنجاح.")
