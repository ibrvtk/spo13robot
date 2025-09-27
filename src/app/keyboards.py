from config import bot

import aiosqlite

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder


keyboardsPlaceholderTextChoose = "Выберите..."



# /admin
adminKeyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Верифицировать человека", callback_data="adminKeyboardAdd"),
     InlineKeyboardButton(text="Верификационный список", callback_data="adminKeyboardList")]
])


adminKeyboardAddChooseRole = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📰 Публикатор")],
    [KeyboardButton(text="🛡️ Модератор")],
    [KeyboardButton(text="🪪 Администратор")]
],
resize_keyboard=True,
input_field_placeholder=f"{keyboardsPlaceholderTextChoose}",
one_time_keyboard=True)


async def adminKeyboardList():
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="🔙 Назад", callback_data="adminKeyboardListBack"))
    
    async with aiosqlite.connect('databases/roles.db') as db:
        async with db.execute("SELECT user_id FROM roles") as cursor:
            result = await cursor.fetchall()

    for row in result:
        user_id = row[0]
        user = await bot.get_chat(user_id)
        found_username = user.username if user.username else user.id
        keyboard.add(InlineKeyboardButton(text=f"{found_username}", callback_data=f"user_{user_id}"))

    return keyboard.adjust(2).as_markup()

async def adminListActions_(user_id: int):
    keyboard = InlineKeyboardBuilder()
    
    keyboard.add(InlineKeyboardButton(text="📜 Изменить роль", callback_data=f"adminListActionsChangeRole_{user_id}"))
    keyboard.add(InlineKeyboardButton(text="❌ Удалить", callback_data=f"adminListActionsDelete_{user_id}"))
    keyboard.add(InlineKeyboardButton(text="🔙 Назад", callback_data="adminListActionsBack"))
    
    return keyboard.adjust(2).as_markup()


# /publish
publishKeyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Написать пост", callback_data="publishAdd"),
     InlineKeyboardButton(text="Список моих постов", callback_data="publishList")]
])