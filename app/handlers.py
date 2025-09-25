from config import bot, SUPERADMINS, fsmPlaceholderTextRetry

import app.keyboards as kb

import aiosqlite

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest


handlers = Router()



async def funcIsBanned(message: Message, user_id: int) -> bool: # Проверка человека на наличие бана.
    async with aiosqlite.connect('databases/roles.db') as db:
        async with db.execute("SELECT isBanned FROM roles WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
    
    if result is not None and result[0] == 1:
        await message.answer("💀 <b>Вы забанены в боте.</b>")
        return True
    
    return False



@handlers.message(Command("start"), F.chat.type == "private")
async def cmdStart(message: Message):
    if await funcIsBanned(message, user_id):
        return
    
    user_id = message.from_user.id
    
    async with aiosqlite.connect('databases/roles.db') as db:
        async with db.execute("SELECT isModerator, isPublisher, isAdmin, isBanned FROM roles WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()

    if result is None:
        if message.from_user.id in SUPERADMINS:
            async with aiosqlite.connect('databases/roles.db') as db:
                await db.execute("""
                    INSERT INTO roles (user_id, isModerator, isPublisher, isAdmin, isBanned) 
                    VALUES (?, 1, 1, 1, 0)
                """, (user_id,))
                await db.commit()
            
            async with aiosqlite.connect('databases/roles.db') as db:
                async with db.execute("SELECT isModerator, isPublisher, isAdmin, isBanned FROM roles WHERE user_id = ?", (user_id,)) as cursor:
                    result = await cursor.fetchone()
        else:
            text += "❓ <b>Вы неавторизированный пользователь</b> — /publish\n"
    
    text = ""
    if result[2] == 1:
        text += "🪪 <b>У Вас есть права администратора</b> — /admin\n"
    if result[0] == 1:
        text += "🛡️ <b>У Вас есть права модератора</b> — /moderator\n"
    if result[1] == 1:
        text += "📰 <b>У Вас есть права публикатора</b> — /publish\n"
    
    await message.reply(f"<b>Ваши права</b>\n\n{text}")


@handlers.message(Command("cancel"))
async def cmdCancel(message: Message, state: FSMContext):
    try:
        await state.clear()
        await message.answer("✅ <b>Текущая операция отменена.</b>")
    
    except Exception as e:
        await message.answer("❌ <b>Непредвиденная ошибка!</b> Попробуйте снова прописать команду или всё же закончить текущую операцию.")
        print(f"❌ Непредвиденная ошибка /cancel (handlers.py): {e}.")


class fsmGetId(StatesGroup):
    username = State()

@handlers.message(Command("getid"))
async def cmdGetId(message: Message, state: FSMContext):
    await state.set_state(fsmGetId.username)
    
    await message.answer("<b>Введите <a href='https://t.me/unbrokensociety'>@юзернейм</a> искомого человека.</b>")

@handlers.message(fsmGetId.username)
async def fsmGetIdUsername(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.text.replace("@", "").strip()

    if await funcIsBanned(message, user_id):
        return

    try:
        user = await bot.get_chat(f"@{username}")
        found_user_id = user.id
        await message.answer(f"✅ <code>{found_user_id}</code>")
        await state.clear()

    except TelegramBadRequest:
        await message.answer(f"❌ <b>Ошибка!</b> Такого пользователя не существует.{fsmPlaceholderTextRetry}")

    except Exception as e:
        await message.answer("❌ <b>Непредвиденная ошибка!</b> Возможно, искомый человек не начал переписку с ботом.")
        print(f"❌ Непредвиденная ошибка /getid (handlers.py): {e}.")
        await state.clear()


# Команды ролей (панели).
@handlers.message(Command("admin"))
async def cmdAdmin(message: Message):
    user_id = message.from_user.id

    if await funcIsBanned(message, user_id):
        return
    
    async with aiosqlite.connect('databases/roles.db') as db:
        async with db.execute("SELECT isModerator, isPublisher, isAdmin, isBanned FROM roles WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()

    if result[2] == 1:
        await message.answer("🛡️ <b>Управление правами.</b>",
                             reply_markup=kb.publishKeyboard)


@handlers.message(Command("publish"))
async def cmdPublish(message: Message):
    user_id = message.from_user.id

    if await funcIsBanned(message, user_id):
        return

    async with aiosqlite.connect('databases/roles.db') as db:
        async with db.execute("SELECT isModerator, isPublisher, isAdmin, isBanned FROM roles WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()

    if result[1] == 1:
        await message.answer("📰 <b>Управление предложенными постами.</b>",
                             reply_markup=kb.publishKeyboard)