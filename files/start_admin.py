# files/admin.py
import os
import sys
import time
import shutil
import platform
import asyncio
import zipfile
from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup
import psutil
from telethon import TelegramClient
from telethon.sessions import StringSession
from pytgcalls import PyTgCalls
from files import config
from files.utils import setup_pytgcalls_handlers

# ================== الكيبوردات (الأزرار) ==================
def get_dev_keyboard():
    return ReplyKeyboardMarkup([
        ["إضافة مساعد", "حذف مساعد"],
        ["غادر الكل"],
        ["إضافة صورة", "حذف صورة"],
        ["تعيين اسم البوت", "حذف اسم البوت"],
        ["الإحصائيات", "الإذاعة"],
        ["بنج", "تفريغ السيرفر", "رفع ملف"],
        ["جلب السجل"],
        ["جلب نسخة احتياطية", "رفع نسخة احتياطية"]
    ], resize_keyboard=True)

def get_broadcast_keyboard():
    return ReplyKeyboardMarkup([
        ["إذاعة خاص", "إذاعة مجموعات"],
        ["إذاعة عام"],
        ["رجوع"]
    ], resize_keyboard=True)

def get_cancel_keyboard():
    return ReplyKeyboardMarkup([["رجوع"]], resize_keyboard=True)

# ================== رسالة البدء ==================
@Client.on_message(filters.command(["start", "بدء"], prefixes=["/", ""]) & filters.private)
async def start_cmd(client, message):
    if message.from_user.id == config.OWNER_ID:
        config.user_states[config.OWNER_ID] = None
        await message.reply("👨‍💻 لوحة تحكم المطور الذكية:", reply_markup=get_dev_keyboard())
    else:
        text = "👋 أهلاً بك! ارفعني مشرفاً في مجموعتك وسأقوم بتشغيل الصوتيات."
        bot_image = config.bot_cache.get("bot_image")
        if bot_image:
            await message.reply_photo(photo=bot_image, caption=text)
        else:
            await message.reply(text)

# ================== معالجة أزرار وأوامر المطور ==================
@Client.on_message(filters.private & (filters.text | filters.photo | filters.document | filters.video | filters.audio))
async def handle_admin(client, message):
    if message.from_user.id != config.OWNER_ID: return
    
    if message.text == "رجوع":
        config.user_states[config.OWNER_ID] = None
        await message.reply("🔙 تم العودة للقائمة الرئيسية.", reply_markup=get_dev_keyboard())
        return

    state = config.user_states.get(config.OWNER_ID)

    # --- 1. الإذاعة ---
    if state in ["إذاعة خاص", "إذاعة مجموعات", "إذاعة عام"]:
        broadcast_type = state
        config.user_states[config.OWNER_ID] = None
        msg_wait = await message.reply(f"⏳ جاري تنفيذ {broadcast_type}...\nيرجى الانتظار.")
        
        stats = config.bot_cache.get("stats", {"admin_groups": [], "channels": [], "private": []})
        targets = []
        
        if broadcast_type == "إذاعة خاص":
            targets = stats.get("private", [])
        elif broadcast_type == "إذاعة مجموعات":
            targets = stats.get("admin_groups", []) + stats.get("channels", [])
        elif broadcast_type == "إذاعة عام":
            targets = stats.get("private", []) + stats.get("admin_groups", []) + stats.get("channels", [])
            
        targets = list(set(targets))
        sent = 0
        failed = 0
        
        for chat_id in targets:
            try:
                await client.copy_message(chat_id, message.chat.id, message.id)
                sent += 1
                await asyncio.sleep(0.05)
            except:
                failed += 1
                
        await msg_wait.edit(f"✅ انتهت عملية **{broadcast_type}** بنجاح!\n\n📤 الإرسال الناجح: `{sent}`\n🚫 الفشل: `{failed}`", reply_markup=get_dev_keyboard())
        return

    # --- 2. معالجة الحالات ---
    if state == "wait_image":
        if message.photo:
            config.bot_cache["bot_image"] = message.photo.file_id
            config.save_cache()
            config.user_states[config.OWNER_ID] = None
            await message.reply("✅ تم حفظ الصورة.", reply_markup=get_dev_keyboard())
        return

    if state == "wait_bot_name":
        if message.text:
            config.bot_cache["custom_bot_name"] = message.text.strip()
            config.save_cache()
            config.user_states[config.OWNER_ID] = None
            await message.reply(f"✅ تم حفظ اسم البوت: **{message.text.strip()}**", reply_markup=get_dev_keyboard())
        return

    if state == "wait_file":
        if message.document:
            file_name = message.document.file_name
            await message.download(file_name=f"files/{file_name}")
            config.user_states[config.OWNER_ID] = None
            await message.reply("✅ تم حفظ الملف.\n🔄 جاري إعادة التشغيل...", reply_markup=get_dev_keyboard())
            os.execl(sys.executable, sys.executable, "main.py")
        return

    if state == "wait_session":
        if message.text:
            text = message.text.strip()
            config.user_states[config.OWNER_ID] = None
            try:
                config.assistant_client = TelegramClient(StringSession(text), config.API_ID, config.API_HASH)
                await config.assistant_client.connect()
                config.assistant_id = (await config.assistant_client.get_me()).id
                config.call_py = PyTgCalls(config.assistant_client)
                setup_pytgcalls_handlers()
                await config.call_py.start()
                
                config.bot_cache["assistant_session"] = text
                config.save_cache()
                await message.reply("✅ تم الاتصال بنجاح!", reply_markup=get_dev_keyboard())
            except Exception as e: 
                await message.reply(f"❌ خطأ: {e}", reply_markup=get_dev_keyboard())
        return

    if state == "wait_backup":
        if message.document and message.document.file_name.endswith(".zip"):
            file_path = await message.download(file_name="temp_backup.zip")
            try:
                with zipfile.ZipFile(file_path, 'r') as zip_ref: zip_ref.extractall(".")
                os.remove(file_path)
                config.user_states[config.OWNER_ID] = None
                config.load_cache()
                await message.reply("✅ تمت استعادة الذاكرة! جاري إعادة التشغيل ليتذكر البوت كل شيء...", reply_markup=get_dev_keyboard())
                os.execl(sys.executable, sys.executable, "main.py")
            except:
                pass
        return

    # --- 3. الأزرار المباشرة ---
    if not message.text: return
    text = message.text.strip()
    
    if text == "الإحصائيات":
        stats = config.bot_cache.get("stats", {"admin_groups": [], "channels": [], "private": []})
        admin_count = len(stats.get("admin_groups", []))
        channels_count = len(stats.get("channels", []))
        private_count = len(stats.get("private", []))
        
        await message.reply(
            f"⚡️ **إحصائيات البوت الفورية:**\n\n"
            f"🛡 **مجموعات البوت مشرف فيها:** `{admin_count}`\n"
            f"📢 **القنوات:** `{channels_count}`\n"
            f"👤 **الدردشات الخاصة:** `{private_count}`\n\n"
            f"💡 *يتم التحديث تلقائياً في الخلفية.*"
        )

    elif text == "الإذاعة":
        await message.reply("📢 اختر نوع الإذاعة:", reply_markup=get_broadcast_keyboard())

    elif text in ["إذاعة خاص", "إذاعة مجموعات", "إذاعة عام"]:
        config.user_states[config.OWNER_ID] = text
        await message.reply(f"✍️ أرسل الآن المحتوى ليتم إرساله كـ «{text}»:", reply_markup=get_cancel_keyboard())

    elif text == "إضافة صورة":
        config.user_states[config.OWNER_ID] = "wait_image"
        await message.reply("🖼 أرسل الصورة الآن:", reply_markup=get_cancel_keyboard())
        
    elif text == "حذف صورة":
        config.bot_cache["bot_image"] = None
        config.save_cache()
        await message.reply("🗑 تم حذف الصورة.")

    elif text == "تعيين اسم البوت":
        config.user_states[config.OWNER_ID] = "wait_bot_name"
        await message.reply("أرسل اسم البوت الجديد:", reply_markup=get_cancel_keyboard())
        
    elif text == "حذف اسم البوت":
        if "custom_bot_name" in config.bot_cache:
            del config.bot_cache["custom_bot_name"]
            config.save_cache()
        await message.reply("🗑 تم حذف الاسم وعاد للوضع الافتراضي.")

    elif text == "إضافة مساعد":
        config.user_states[config.OWNER_ID] = "wait_session"
        await message.reply("أرسل جلسة تيلثون الحساب المساعد:", reply_markup=get_cancel_keyboard())
        
    elif text == "حذف مساعد":
        if config.assistant_client:
            try: 
                await config.call_py.leave_call(message.chat.id)
                await config.assistant_client.disconnect()
            except: pass
            config.assistant_client = config.call_py = config.assistant_id = None
        if "assistant_session" in config.bot_cache:
            del config.bot_cache["assistant_session"]
            config.save_cache()
        await message.reply("✅ تم حذف المساعد بنجاح.")

    # --- زر غادر الكل (متصل بملف chat_member.py عن طريق التخزين) ---
    elif text == "غادر الكل":
        msg_wait = await message.reply("⏳ جاري سحب البوت والمساعد من جميع المجموعات والقنوات المحفوظة في الذاكرة...")
        
        bot_left = 0
        assist_left = 0
        
        # جلب الجروبات والقنوات من التخزين (نفس التخزين اللي بيضيف فيه chat_member.py)
        stats = config.bot_cache.get("stats", {"admin_groups": [], "channels": [], "private": []})
        groups_to_leave = set(stats.get("admin_groups", []) + stats.get("channels", []))
        
        # 1. البوت يغادر الجروبات المسجلة
        for chat_id in groups_to_leave:
            try:
                await client.leave_chat(chat_id)
                bot_left += 1
            except:
                pass
                
        # 2. المساعد يغادر الجروبات المسجلة
        if config.assistant_client:
            for chat_id in groups_to_leave:
                try:
                    await config.assistant_client.delete_dialog(chat_id)
                    assist_left += 1
                except:
                    pass
                    
        # تصفير الإحصائيات بعد المغادرة من التخزين
        config.bot_cache["stats"]["admin_groups"] = []
        config.bot_cache["stats"]["channels"] = []
        config.save_cache()

        await msg_wait.edit(f"✅ تمت المغادرة بنجاح بناءً على قاعدة البيانات المشتركة!\n\n🤖 البوت غادر: `{bot_left}` جروب/قناة\n👤 المساعد غادر: `{assist_left}` جروب/قناة")

    # --- زر بنج ---
    elif text == "بنج":
        start_time = time.time()
        msg = await message.reply("🔄 جاري الفحص...")
        end_time = time.time()
        
        ping_time = round((end_time - start_time) * 1000)
        cpu_name = platform.processor() or "غير معروف"
        cpu_usage = psutil.cpu_percent(interval=1)
        os_name = f"{platform.system()} {platform.release()}"
        
        await msg.edit(
            f"🚀 **البنج وسرعة البوت:** `{ping_time} ms`\n"
            f"🧠 **نوع المعالج:** `{cpu_name}`\n"
            f"⚙️ **استهلاك المعالج:** `{cpu_usage}%`\n"
            f"🖥 **النظام (الاستضافة):** `{os_name}`"
        )

    elif text == "تفريغ السيرفر":
        deleted = 0
        if os.path.exists("downloads"):
            for root, _, files in os.walk("downloads"):
                for f in files:
                    fp = os.path.join(root, f)
                    if not os.path.islink(fp): deleted += os.path.getsize(fp)
            shutil.rmtree("downloads")
            os.makedirs("downloads")
        await message.reply(f"✅ تم تفريغ المهملات وتنظيف السيرفر.")

    elif text == "رفع ملف":
        config.user_states[config.OWNER_ID] = "wait_file"
        await message.reply("📂 قم بإرسال الملف الآن:", reply_markup=get_cancel_keyboard())

    # --- الزر القديم المدمج (جلب السجل) ---
    elif text == "جلب السجل":
        if not config.STORAGE_CHANNEL_ID:
            return await message.reply("❌ لم يتم تعيين قناة تخزين في الإعدادات.")
            
        if not config.assistant_client:
            return await message.reply("❌ الحساب المساعد غير متصل. يرجى إضافة المساعد أولاً ليتمكن من سحب السجل.")
        
        msg_wait = await message.reply("⏳ جاري فحص قناة التخزين بواسطة المساعد وبناء ذاكرة البوت...\n(سيتم فحص آخر 1000 رسالة لربط الأيديهات وفصل الصوت عن الفيديو)")
        
        count_audio = 0
        count_video = 0
        
        if "audio" not in config.bot_cache: config.bot_cache["audio"] = {}
        if "video" not in config.bot_cache: config.bot_cache["video"] = {}
            
        try:
            async for m in config.assistant_client.iter_messages(config.STORAGE_CHANNEL_ID, limit=1000):
                if m.audio or m.video or m.document:
                    yt_id = m.text if m.text else None
                    
                    if yt_id:
                        yt_id = yt_id.strip()
                        if len(yt_id) <= 15: 
                            if m.video:
                                if yt_id not in config.bot_cache["video"]:
                                    config.bot_cache["video"][yt_id] = m.id
                                    count_video += 1
                            elif m.audio or m.document:
                                if yt_id not in config.bot_cache["audio"]:
                                    config.bot_cache["audio"][yt_id] = m.id
                                    count_audio += 1
                                
            config.save_cache()
            await msg_wait.edit(f"✅ تم الانتهاء من فحص السجل بنجاح!\n\n📥 **تم استخراج وحفظ:**\n🎵 `{count_audio}` مقطع صوتي.\n🎬 `{count_video}` مقطع فيديو.\n\n💡 **البوت الآن يفرق بينهم بدقة وسيجلبهم من القناة مباشرة.**")
        except Exception as e:
            await msg_wait.edit(f"❌ حدث خطأ أثناء الجلب، تأكد أن الحساب المساعد موجود كعضو في قناة التخزين: {e}")

    # --- زر جلب نسخة احتياطية ---
    elif text == "جلب نسخة احتياطية":
        msg_wait = await message.reply("⏳ جاري استخراج ذاكرة البوت والنسخة الاحتياطية...")
        
        stats = config.bot_cache.get("stats", {"admin_groups": [], "channels": [], "private": []})
        likes = config.bot_cache.get("likes", 0) 
        play_history_count = len(config.bot_cache.get("play_history", [])) 
        
        bot_groups = len(stats.get("admin_groups", []))
        bot_channels = len(stats.get("channels", []))
        bot_private = len(stats.get("private", []))
        
        caption = (
            f"📊 **ذاكرة البوت الشاملة (النسخة الاحتياطية)** 📊\n\n"
            f"🛡 **المجموعات التي عمل بها:** `{bot_groups}`\n"
            f"📢 **القنوات المتواجد بها:** `{bot_channels}`\n"
            f"👤 **الأشخاص في الخاص:** `{bot_private}`\n"
            f"❤️ **اللايكات المسجلة:** `{likes}`\n"
            f"🎵 **سجل التفاعلات والتشغيل:** `{play_history_count}`\n\n"
            f"💡 *هذا الملف المرفق يحتوي على كل الروابط والأشخاص وتاريخ البوت. ارفعه في أي وقت بـ (رفع نسخة احتياطية) ليتذكر البوت كل شيء وكأنه لم يتوقف!*"
        )
        
        try:
            with zipfile.ZipFile("bot_backup.zip", 'w') as zipf:
                if os.path.exists("bot_cache.json"): zipf.write("bot_cache.json")
                if os.path.exists("local_config.json"): zipf.write("local_config.json")
                
            await message.reply_document("bot_backup.zip", caption=caption)
            os.remove("bot_backup.zip")
            await msg_wait.delete()
        except Exception as e:
            await msg_wait.edit(f"❌ خطأ أثناء استخراج الذاكرة: {e}")

    elif text == "رفع نسخة احتياطية":
        config.user_states[config.OWNER_ID] = "wait_backup"
        await message.reply("📂 أرسل ملف .zip لاستعادة ذاكرة البوت بالكامل:", reply_markup=get_cancel_keyboard())
