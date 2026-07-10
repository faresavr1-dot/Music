# files/bot_replies.py

import random
import asyncio
import aiohttp
from pyrogram import Client, filters
from files import config

# ================== قوائم الردود ==================
BOT_REPLIES = [
    "أنا مو بوت، أنا قلوب تنبض 🥺",
    "أنت البوت يا أخي، على البشر ما تناديني بوت 😒",
    "لا تعيدها مرة ثانية، اسمي أحلى من كلمة بوت 🔪",
    "عيون البوت، أؤمرني؟ 👀",
    "بوت في عينك، احترم نفسك 😤"
]

NAME_REPLIES = [
    "في خدمتك يا سيدي، أؤمر يا باشا 🫡",
    "اطلب وأنا أنفذ 🧞‍♂️",
    "معاك يا بعد روحي ❤️",
    "معاك يا قلبي، تفضل 🥰",
    "لبيك يا غالي 🌹"
]

# ================== دالة الريأكت السريعة جداً ==================
async def send_bot_reaction(client, chat_id, message_id, emoji):
    """دالة ترسل الريأكت في الخلفية فوراً بدون انتظار"""
    token = getattr(config, "BOT_TOKEN", None) or getattr(config, "TOKEN", None) or getattr(client, "bot_token", None)
    if not token:
        return
        
    url = f"https://api.telegram.org/bot{token}/setMessageReaction"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "reaction": [{"type": "emoji", "emoji": emoji}],
        "is_big": False
    }
    
    async def fetch():
        try:
            async with aiohttp.ClientSession() as session:
                await session.post(url, json=payload)
        except:
            pass

    asyncio.create_task(fetch())

# ================== التفاعل والرد (في المجموعات) ==================
@Client.on_message(filters.text & filters.group & ~filters.bot, group=5)
async def handle_bot_mentions(client, message):
    text = message.text.strip()
    words = text.split()
    
    # 🔴 التعديل هنا: جلب الاسم المخصص، وإذا لم يوجد يكون "لفت" هو الافتراضي
    custom_name = config.bot_cache.get("custom_bot_name") or "لفت"
    
    # 1. إذا تم نداء البوت باسمه المعتمد
    if custom_name in text:
        asyncio.create_task(send_bot_reaction(client, message.chat.id, message.id, "❤️"))
        await message.reply(random.choice(NAME_REPLIES))
        return
        
    # 2. إذا تم نداء كلمة "بوت"
    if "بوت" in words:
        asyncio.create_task(send_bot_reaction(client, message.chat.id, message.id, "😍"))
        await message.reply(random.choice(BOT_REPLIES))

