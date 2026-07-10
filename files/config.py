import os
import json

# اسم الملف المحلي لحفظ البيانات وتجنب كتابتها مع كل إعادة تشغيل للسيرفر
CONFIG_FILE = "local_config.json"

if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            saved_vars = json.load(f)
    except:
        saved_vars = {}
else:
    saved_vars = {}

# إذا لم تكن البيانات محفوظة من قبل، سيطلبها البوت بالترتيب عبر الكونسول
if not saved_vars:
    print("\n🚀 يرجى إدخال متغيرات تشغيل البوت الأساسية:")
    saved_vars["API_HASH"] = input("👉 1. أدخل API_HASH: ").strip()
    saved_vars["API_ID"] = input("👉 2. أدخل API_ID: ").strip()
    saved_vars["BOT_TOKEN"] = input("👉 3. أدخل BOT_TOKEN: ").strip()
    saved_vars["OWNER_ID"] = input("👉 4. أدخل OWNER_ID (أيدي المطور): ").strip()
    saved_vars["STORAGE_CHANNEL"] = input("👉 5. أدخل رابط قناة التخزين (STORAGE_CHANNEL): ").strip()
    # ✅ تم إزالة طلب الـ COOKIE نهائياً
    
    # حفظ المدخلات في ملف محلي
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(saved_vars, f, ensure_ascii=False, indent=4)
    print("✅ تم حفظ المتغيرات بنجاح في ملف local_config.json وسيتم تشغيل البوت الآن.\n")

# تعيين المتغيرات للبوت بناءً على البيانات المحفوظة
API_ID = int(saved_vars.get("API_ID", 0)) if saved_vars.get("API_ID") else 0
API_HASH = saved_vars.get("API_HASH", "")
BOT_TOKEN = saved_vars.get("BOT_TOKEN", "")
OWNER_ID = int(saved_vars.get("OWNER_ID", 0)) if saved_vars.get("OWNER_ID") else 0
STORAGE_CHANNEL_LINK = saved_vars.get("STORAGE_CHANNEL", "").strip()
# ✅ تم إزالة COOKIE_DATA نهائياً

bot = None
assistant_client = None
call_py = None
assistant_id = None
STORAGE_CHANNEL_ID = None

CACHE_FILE = "bot_cache.json"
bot_cache = {"audio": {}, "video": {}, "disabled_groups": [], "bot_image": None}
music_queue = {}
current_playing = {}
is_playing_now = {}
playback_start_time = {}
playback_offset = {}
is_seeking = {}
repeat_mode = {}
user_states = {}
likes_db = {}

def load_cache():
    global bot_cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                bot_cache.update(data)
        except: pass

def save_cache():
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(bot_cache, f, ensure_ascii=False, indent=4)
