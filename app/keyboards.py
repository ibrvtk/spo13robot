from config import keyboardsPlaceholderTextChoose

import aiosqlite

from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder



# /admin
adminKeyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Верифицировать человека", callback_data="adminAdd"),
     InlineKeyboardButton(text="Верификационный список", callback_data="adminList")]
])

adminKeyboardAdd = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="📰 Публикатор")],
    [KeyboardButton(text="🛡️ Модератор")],
    [KeyboardButton(text="🪪 Администратор")]
],
resize_keyboard=True,
input_field_placeholder=f"{keyboardsPlaceholderTextChoose}")


# /publish
publishKeyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Написать пост", callback_data="publishAdd"),
     InlineKeyboardButton(text="Список моих постов", callback_data="publishList")]
])