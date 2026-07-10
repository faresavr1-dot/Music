# ================== الملف كامل بعد التعديل ==================

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from files import config
from files.utils import is_admin

# ================== الأزرار المطلوبة بنفس الزخرفة ==================
SOURCE_BUTTON = InlineKeyboardButton("𝐒𝐎𝐔𝐑𝐂𝐄", url="https://t.me/AY_WV")
GROUP_BUTTON = InlineKeyboardButton("𝐆𝐑𝐎𝐔𝐏", url="https://t.me/O1_ZO")
DEV_BUTTON = InlineKeyboardButton("𝐃𝐄𝐕", user_id=config.OWNER_ID)

# ================== الكيبورد الرئيسي للأوامر ==================
# تم التعديل كله عشان الأزرار ملونة زي الصورة + ما فيهوش أي دالة أو زر جديد
def main_help_keyboard(user_id):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("م1", callback_data=f"help_m1_{user_id}"),
            InlineKeyboardButton("م2", callback_data=f"help_m2_{user_id}"),
            InlineKeyboardButton("م3", callback_data=f"help_m3_{user_id}"),
            InlineKeyboardButton("م4", callback_data=f"help_m4_{user_id}"),
        ],
        [
            InlineKeyboardButton("م5", callback_data=f"help_m5_{user_id}"),
        ],
        [
            SOURCE_BUTTON, GROUP_BUTTON
        ],
        [
            DEV_BUTTON
        ]
    ])

# ================== كيبورد الرجوع ==================
def back_keyboard(user_id):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("رجوع 🔙", callback_data=f"help_back_{user_id}")]
    ])

# ================== أمر /help أو الاوامر ==================
@Client.on_message(filters.command(["الاوامر", "help", "مساعدة"], prefixes=["/", "", "."]))
async def help_command(client, message):
    if not await is_admin(client, message, check_player=False, show_error=True):
        return

    is_anonymous_admin = (message.sender_chat and message.sender_chat.id == message.chat.id)
    user_id = message.from_user.id if message.from_user else 0

    text = (
        "👋 **أهلاً بك في قائمة أوامر البوت**\n\n"
        "م1 ↤ أوامر التشغيل 🎵\n"
        "م2 ↤ أوامر التحكم 🎛\n"
        "م3 ↤ أوامر الألعاب والتسلية 🎲\n"
        "م4 ↤ أوامر المشرفين 🛡\n"
        "م5 ↤ أوامر المطور 👨‍💻\n\n"
        "👇 **اختر القسم الذي تريده من الأزرار بالأسفل:**"
    )
    
    pass_id = message.chat.id if is_anonymous_admin else user_id
    await message.reply(text, reply_markup=main_help_keyboard(pass_id))

# ================== معالجة ضغطات الأزرار (Callbacks) ==================
@Client.on_callback_query(filters.regex(r"^help_"))
async def help_callbacks(client, callback_query: CallbackQuery):
    data = callback_query.data
    clicker_id = callback_query.from_user.id
    
    parts = data.split("_")
    action = parts[1] 
    requester_id = int(parts[2])
    
    if clicker_id != requester_id and requester_id != callback_query.message.chat.id:
        return await callback_query.answer("عذراً هذا الأمر لا يعنيك", show_alert=True)
        
    if action == "m5" and clicker_id != config.OWNER_ID:
        return await callback_query.answer("هذا القسم غير مخصص لك يا غبي، لا تتدخل فيه مرة ثانية! 😡", show_alert=True)
        
    if action == "m1":
        text = (
            "🎵 **أوامر التشغيل:**\n\n"
            "• `شغل` + [اسم الأغنية] : لتشغيل مقطع صوتي\n"
            "• `فيديو` + [اسم الفيديو] : لتشغيل مقطع مرئي\n"
            "• `انهاء` : لإيقاف التشغيل وإخلاء المكالمة تماماً"
        )
        await callback_query.message.edit_text(text, reply_markup=back_keyboard(requester_id))
        
    elif action == "m2":
        text = (
            "🎛 **أوامر التحكم:**\n\n"
            "• `وقف` : لإيقاف التشغيل مؤقتاً\n"
            "• `كمل` : لاستئناف التشغيل بعد الإيقاف\n"
            "• `تخطي` : لتخطي المقطع الحالي وتشغيل التالي\n"
            "• `كرر` : لتفعيل تكرار المقطع الحالي\n"
            "• `مرر` : لتقديم المقطع للأمام\n"
            "• `رجع` : لتأخير المقطع للخلف"
        )
        await callback_query.message.edit_text(text, reply_markup=back_keyboard(requester_id))
        
    elif action == "m3":
        text = (
            "🎲 **أوامر التسلية والإضافات:**\n\n"
            "• `ايدي` : لعرض معلوماتك\n"
            "• `الفايدي` : لعرض آيدي المجموعة أو الشخص\n"
            "• `قط` : لعرض صورة قطة عشوائية"
        )
        await callback_query.message.edit_text(text, reply_markup=back_keyboard(requester_id))
        
    elif action == "m4":
        text = (
            "🛡 **أوامر المشرفين:**\n\n"
            "• `رفع مشغل` : لإعطاء شخص صلاحية التحكم بالبوت\n"
            "• `تنزيل مشغل` : لسحب صلاحية التحكم\n"
            "• `قائمة المشغلين` : لعرض جميع المشغلين في المجموعة"
        )
        await callback_query.message.edit_text(text, reply_markup=back_keyboard(requester_id))
        
    elif action == "m5":
        text = (
            "👨‍💻 **أوامر المطور (خاصة بك فقط):**\n\n"
            "• `تفعيل` / `تعطيل` : لتشغيل أو إيقاف البوت في المجموعة الحالية\n"
            "• `غادر` : لسحب البوت والمساعد من المجموعة\n"
            "• `غادر الحساب` : لسحب الحساب المساعد فقط\n"
            "• `الاحصائيات` : لعرض إحصائيات البوت\n"
            "• `اذاعة` : لعمل إذاعة للمجموعات والخاص"
        )
        await callback_query.message.edit_text(text, reply_markup=back_keyboard(requester_id))
        
    elif action == "back":
        text = (
            "👋 **أهلاً بك في قائمة أوامر البوت**\n\n"
            "م1 ↤ أوامر التشغيل 🎵\n"
            "م2 ↤ أوامر التحكم 🎛\n"
            "م3 ↤ أوامر الألعاب والتسلية 🎲\n"
            "م4 ↤ أوامر المشرفين 🛡\n"
            "م5 ↤ أوامر المطور 👨‍💻\n\n"
            "👇 **اختر القسم الذي تريده من الأزرار بالأسفل:**"
        )
        await callback_query.message.edit_text(text, reply_markup=main_help_keyboard(requester_id))