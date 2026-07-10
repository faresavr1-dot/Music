import os
import asyncio
from pyrogram import Client, filters
from telethon import TelegramClient
from telethon.sessions import StringSession
from pytgcalls import PyTgCalls
from files import config  # استدعاء الإعدادات من مجلد files
from files.utils import setup_pytgcalls_handlers

# تحميل قاعدة البيانات
config.load_cache()

# المايسترو: البوت سيقرأ مجلد files ويشغل كل الأوامر التي بداخله
app = Client(
    "MusicBot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    plugins=dict(root="files")  # توجيه البوت لمجلد files المسطح
)
config.bot = app

# تفاعل بقلب أحمر على جميع الرسائل الواردة
@app.on_message(filters.all, group=-1)
async def global_heart_reaction(client, message):
    try:
        await message.react("❤️")
    except:
        pass

async def start_saved_assistant():
    """دالة للاتصال بالمساعد تلقائياً عند إعادة تشغيل السيرفر"""
    if "assistant_session" in config.bot_cache and config.bot_cache["assistant_session"]:
        print("🔄 جاري الاتصال بالحساب المساعد المحفوظ...")
        try:
            config.assistant_client = TelegramClient(
                StringSession(config.bot_cache["assistant_session"]), 
                config.API_ID, 
                config.API_HASH
            )
            await config.assistant_client.connect()
            config.assistant_id = (await config.assistant_client.get_me()).id
            config.call_py = PyTgCalls(config.assistant_client)
            setup_pytgcalls_handlers()
            await config.call_py.start()
            print("✅ تم تشغيل الحساب المساعد المحفوظ بنجاح!")
        except Exception as e:
            print(f"❌ فشل تشغيل المساعد المحفوظ (قد تكون الجلسة انتهت أو غير صالحة): {e}")

async def main():
    await app.start()
    print("🚀 Bot is Working Modularly from 'files' folder!")
    
    # --- تشغيل المساعد المحفوظ تلقائياً ---
    await start_saved_assistant()
    # --------------------------------------
    
    if config.STORAGE_CHANNEL_LINK:
        try:
            clean_link = config.STORAGE_CHANNEL_LINK.replace("https://t.me/", "").replace("@", "")
            config.STORAGE_CHANNEL_ID = (await app.get_chat(clean_link)).id
        except: pass
    await asyncio.Event().wait()

if __name__ == "__main__":
    if not os.path.exists("downloads"): os.makedirs("downloads")
    asyncio.get_event_loop().run_until_complete(main())
