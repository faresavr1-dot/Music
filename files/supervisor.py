# files/supervisor.py (أو chat_member.py حسب ما سميته)
import os
from pyrogram import Client, filters
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums import ChatMemberStatus, ChatType
from files import config

@Client.on_chat_member_updated(filters.group | filters.channel)
async def bot_added_or_promoted(client: Client, event: ChatMemberUpdated):
    # 1. حل مشكلة الـ NoneType (عشان لو العضو انطرد أو غادر)
    member = event.new_chat_member or event.old_chat_member
    if not member or not member.user:
        return
        
    bot = await client.get_me()
    if member.user.id != bot.id:
        return

    chat = event.chat
    new_status = event.new_chat_member.status if event.new_chat_member else None
    old_status = event.old_chat_member.status if event.old_chat_member else None
    promoter = event.from_user

    # تهيئة التخزين
    if "stats" not in config.bot_cache:
        config.bot_cache["stats"] = {"admin_groups": [], "channels": [], "private": []}
    stats = config.bot_cache["stats"]

    # ==========================================
    # أولاً: لو البوت اترفع مشرف (تم تفعيله)
    # ==========================================
    if new_status == ChatMemberStatus.ADMINISTRATOR:
        
        # --- الحفظ في الإحصائيات للتخزين والإذاعة ---
        if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            if chat.id not in stats["admin_groups"]:
                stats["admin_groups"].append(chat.id)
        elif chat.type == ChatType.CHANNEL:
            if chat.id not in stats["channels"]:
                stats["channels"].append(chat.id)
        config.save_cache()

        # --- إرسال رسالة ترحيبية في الجروب نفسه ---
        if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            user_link = f"[{promoter.first_name}](tg://user?id={promoter.id})" if promoter else "أحد المشرفين"
            
            # حل مشكلة زر المطور باستخدام user_id بدلاً من url
            dev_button = InlineKeyboardMarkup([
                [InlineKeyboardButton("👨‍💻 تواصل مع المطور", user_id=config.OWNER_ID)]
            ])
            try:
                await client.send_message(
                    chat.id,
                    f"✅ **تم تفعيل البوت بنجاح!**\n\n"
                    f"👤 بواسطة: {user_link}\n"
                    f"💡 أنا الآن جاهز لتشغيل الصوتيات والمرئيات.\n"
                    f"📞 إذا واجهت أي مشكلة، لا تتردد في مراسلة المطور من الزر بالأسفل.",
                    reply_markup=dev_button,
                    disable_web_page_preview=True
                )
            except:
                pass 

        # --- إرسال إشعار للمطور بالصورة والتفاصيل ---
        try:
            # نجلب بيانات الجروب بالكامل عشان نضمن وجود الصورة لو متاحة
            full_chat = await client.get_chat(chat.id)
            chat_type_text = "المجموعة" if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] else "القناة"
            
            # محاولة جلب رابط الجروب
            chat_link = full_chat.invite_link
            if not chat_link and chat.username:
                chat_link = f"https://t.me/{chat.username}"
            
            # تجهيز الأزرار (رابط الجروب + المالك) واستخدام user_id
            buttons = []
            row = []
            if chat_link:
                row.append(InlineKeyboardButton(f"🔗 رابط {chat_type_text}", url=chat_link))
            if promoter:
                row.append(InlineKeyboardButton("👤 المالك/المُفَعِّل", user_id=promoter.id))
            
            if row:
                buttons.append(row)
                
            reply_markup = InlineKeyboardMarkup(buttons) if buttons else None
            
            caption = (
                f"🎉 **تم تفعيل البوت في {chat_type_text} جديدة!**\n\n"
                f"📝 **اسم {chat_type_text}:** `{chat.title}`\n"
                f"🆔 **الآيدي:** `{chat.id}`\n"
            )
            if promoter:
                caption += f"👤 **تم الرفع بواسطة:** [{promoter.first_name}](tg://user?id={promoter.id})\n"

            # محاولة جلب صورة الجروب بدقة
            photo_path = None
            if full_chat.photo:
                photo_path = await client.download_media(full_chat.photo.big_file_id)

            if photo_path:
                await client.send_photo(
                    config.OWNER_ID,
                    photo=photo_path,
                    caption=caption,
                    reply_markup=reply_markup
                )
                os.remove(photo_path) # مسح الصورة بعد إرسالها
            else:
                await client.send_message(
                    config.OWNER_ID,
                    text=caption,
                    reply_markup=reply_markup
                )
        except Exception as e:
            print(f"Error in dev notification: {e}")

    # ==========================================
    # ثانياً: لو البوت نزل من الإشراف أو انضاف كعضو عادي
    # ==========================================
    elif new_status in [ChatMemberStatus.MEMBER, ChatMemberStatus.RESTRICTED, ChatMemberStatus.BANNED, ChatMemberStatus.LEFT, None]:
        
        # --- الإزالة من الإحصائيات فوراً ---
        if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            if chat.id in stats["admin_groups"]:
                stats["admin_groups"].remove(chat.id)
        elif chat.type == ChatType.CHANNEL:
            if chat.id in stats["channels"]:
                stats["channels"].remove(chat.id)
        config.save_cache()

        # --- المغادرة التلقائية لو كان مجرد "عضو عادي" ---
        if new_status == ChatMemberStatus.MEMBER:
            try:
                if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
                    await client.send_message(
                        chat.id, 
                        "❌ لا يمكنني العمل كعضو عادي، يجب رفعي مشرفاً بصلاحيات كاملة.\nسأغادر الآن، ارفعني مشرف ثم أضفني مجدداً."
                    )
                await client.leave_chat(chat.id)
            except:
                pass
            
        # --- إشعار الغدر/التنزيل (يصل للمطور فقط إذا كان البوت مشرفاً قبل ذلك) ---
        if old_status == ChatMemberStatus.ADMINISTRATOR:
            try:
                full_chat = await client.get_chat(chat.id)
                chat_type_text = "مجموعة" if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] else "قناة"
                
                chat_link = full_chat.invite_link
                if not chat_link and chat.username:
                    chat_link = f"https://t.me/{chat.username}"
                
                buttons = []
                if chat_link:
                    buttons.append([InlineKeyboardButton(f"🔗 رابط {chat_type_text}", url=chat_link)])
                reply_markup = InlineKeyboardMarkup(buttons) if buttons else None
                
                await client.send_message(
                    config.OWNER_ID,
                    f"⚠️ **تنبيه غدر وتم إيقاف التفعيل:**\n\n"
                    f"تم تنزيل البوت من الإشراف أو طرده من {chat_type_text}:\n"
                    f"**{chat.title}** (`{chat.id}`)\n\n"
                    f"✅ **تم مسح {chat_type_text} من التخزين تلقائياً والمغادرة.**",
                    reply_markup=reply_markup
                )
            except Exception as e:
                print(f"Error in demotion notification: {e}")
