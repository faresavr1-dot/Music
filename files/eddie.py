from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from files import config

# ---------- أمر الأيدي وكل ما يتعلق به ----------

@Client.on_message(filters.command(["ايدي", "ا"], prefixes=["", "/", "!"]) & filters.group)
async def id_command(client, message):
    user_id = message.from_user.id
    mention = message.from_user.mention
    
    try:
        chat_info = await client.get_chat(user_id)
        bio = chat_info.bio if chat_info.bio else "لا يوجد"
    except: bio = "لا يوجد"
    
    chat_id = message.chat.id
    
    # الرتبة
    try:
        member = await client.get_chat_member(chat_id, user_id)
        status = str(member.status).split('.')[1] if '.' in str(member.status) else str(member.status)
        if status == "OWNER" or status == "creator":
            rank = "مالك الجروب"
        elif status == "ADMINISTRATOR" or status == "administrator":
            rank = "مشرف"
        else:
            rank = "عضو"
    except:
        rank = "عضو"
    
    if user_id not in config.likes_db: config.likes_db[user_id] = {}
    likes_count = len(config.likes_db[user_id])
    markup = InlineKeyboardMarkup([[InlineKeyboardButton(f"❤️ {likes_count}", callback_data=f"like_{user_id}")]])

    text = (
        f"𖡋 𝐔𝐒𝐄 ⌯ {mention}\n"
        f"𖡋 𝐒𝐓𝐀 ⌯ {rank}\n"
        f"𖡋 𝐈𝐃 ⌯ `{user_id}`\n"
        f"𖡋 𝐁𝐈𝐎 ⌯ {bio}"
    )

    try:
        photos = [p async for p in client.get_chat_photos(user_id, limit=1)]
        if photos:
            await message.reply_photo(photos[0].file_id, caption=text, reply_markup=markup, has_spoiler=True)
        else:
            await message.reply(text, reply_markup=markup)
    except:
        await message.reply(text, reply_markup=markup)

@Client.on_callback_query(filters.regex(r"^like_(\d+)"))
async def like_callback(client, callback_query):
    target_id = int(callback_query.matches[0].group(1))
    clicker_id = callback_query.from_user.id
    clicker_mention = callback_query.from_user.mention
    
    if clicker_id == target_id:
        return await callback_query.answer("ما ينفع تتفاعل على نفسك يا غبي", show_alert=True)

    if target_id not in config.likes_db: config.likes_db[target_id] = {}
    
    if clicker_id in config.likes_db[target_id]:
        del config.likes_db[target_id][clicker_id]
        likes_count = len(config.likes_db[target_id])
        markup = InlineKeyboardMarkup([[InlineKeyboardButton(f"❤️ {likes_count}", callback_data=f"like_{target_id}")]])
        await callback_query.edit_message_reply_markup(reply_markup=markup)
        return
    
    config.likes_db[target_id][clicker_id] = clicker_mention
    likes_count = len(config.likes_db[target_id])
    
    markup = InlineKeyboardMarkup([[InlineKeyboardButton(f"❤️ {likes_count}", callback_data=f"like_{target_id}")]])
    await callback_query.edit_message_reply_markup(reply_markup=markup)
    
    try:
        await client.send_message(
            target_id,
            f"{clicker_mention} عمل لك إعجاب ❤️"
        )
    except:
        pass

@Client.on_message(filters.command(["المعجبين"], prefixes=["", "/", "!"]) & filters.group)
async def admirers_command(client, message):
    user_id = message.from_user.id
    if user_id not in config.likes_db or not config.likes_db[user_id]:
        return await message.reply("لا يوجد لديك معجبين حتى الآن")
    
    text = "قائمة المعجبين:\n\n"
    for idx, (uid, mention) in enumerate(config.likes_db[user_id].items(), 1):
        text += f"{idx}- {mention}\n"
    
    await message.reply(text)