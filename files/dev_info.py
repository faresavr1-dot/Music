from pyrogram import Client, filters
from files import config

@Client.on_message(filters.command(["المطور"], prefixes=["", "/", "!"]))
async def dev_info_cmd(client, message):
    try:
        # جلب بيانات المطور
        user = await client.get_users(config.OWNER_ID)
        
        # تجهيز البيانات
        name = user.mention
        username = f"@{user.username}" if user.username else "لا يوجد"
        bio = (await client.get_chat(config.OWNER_ID)).bio or "لا يوجد بايو"
        user_id = user.id
        
        text = (
            f"👤 **معلومات المطور:**\n\n"
            f"📛 **الاسم:** {name}\n"
            f"🆔 **ID:** `{user_id}`\n"
            f"🔗 **اليوزر:** {username}\n"
            f"📝 **البايو:** {bio}"
        )
        
        # جلب صورة المطور
        photos = [p async for p in client.get_chat_photos(config.OWNER_ID)]
        if photos:
            await message.reply_photo(photo=photos[0].file_id, caption=text)
        else:
            await message.reply(text)
            
    except Exception as e:
        await message.reply(f"❌ تعذر جلب معلومات المطور. تأكد من أن ID المطور صحيح.")
