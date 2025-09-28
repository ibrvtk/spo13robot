from config import SUPERADMINS

import app.keyboards as kb

import aiosqlite

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


handlers = Router()



async def funcIsBanned(message: Message, user_id: int) -> bool: # Проверка человека на наличие у него бана.
    async with aiosqlite.connect('databases/roles.db') as db:
        async with db.execute("SELECT isBanned FROM roles WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()
    
    if result is not None and result[0] == 1:
        await message.answer("💀 <b>Вы забанены в боте.</b>")
        return True
    
    return False



@handlers.message(Command("start"), F.chat.type == "private")
async def cmdStart(message: Message):
    user_id = message.from_user.id
    text = ""

    if await funcIsBanned(message, user_id):
        return
    
    async with aiosqlite.connect('databases/roles.db') as db:
        async with db.execute("SELECT isModerator, isPublisher, isAdmin, isBanned FROM roles WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()

    if result != None:
        if result[0] == 1:
            text += "🛡️ <b>У Вас есть права модератора</b> — /moderate\n"
        if result[1] == 1:
            text += "📰 <b>У Вас есть права публикатора</b> — /publish\n"
        if result[2] == 1:
            text += "🪪 <b>У Вас есть права администратора</b> — /admin\n"
    else:
        if message.from_user.id in SUPERADMINS:
            async with aiosqlite.connect('databases/roles.db') as db:
                await db.execute("""
                    INSERT OR REPLACE INTO roles (user_id, isModerator, isPublisher, isAdmin, isBanned) 
                    VALUES (?, 1, 1, 1, 0)
                """, (user_id,))
                await db.commit()
            text += "🪪 <b>У Вас есть права администратора</b> — /admin\n"
            text += "🛡️ <b>У Вас есть права модератора</b> — /moderate\n"
            text += "📰 <b>У Вас есть права публикатора</b> — /publish\n"
        else:
            text += "❓ <b>Вы неавторизированный пользователь</b> — /publish\n"
    
    await message.reply(f"<b>Ваши права</b>\n\n{text}")


@handlers.message(Command("cancel"))
async def cmdCancel(message: Message, state: FSMContext):
    try:
        await state.clear()
        await message.answer("✅ <b>Текущая операция отменена.</b>",
                             reply_markup=None)
    
    except Exception as e:
        await message.answer("❌ <b>Непредвиденная ошибка!</b> Попробуйте снова прописать команду или всё же закончить текущую операцию.")
        print(f"❌ Непредвиденная ошибка /cancel (handlers.py): {e}.")


# Команды ролей (панели).
@handlers.message(Command("admin"), F.chat.type == "private")
async def cmdAdmin(message: Message):
    user_id = message.from_user.id

    if await funcIsBanned(message, user_id):
        return
    
    async with aiosqlite.connect('databases/roles.db') as db:
        async with db.execute("SELECT isAdmin FROM roles WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()

    if result is not None and result[0] == 1:
        await message.answer("🪪 <b>Управление ролями.</b>",
                             reply_markup=kb.adminKeyboard)
    else:
        await message.answer("❌ <b>У вас нет прав на эту команду.</b>")


@handlers.message(Command("publish"), F.chat.type == "private")
async def cmdPublish(message: Message):
    user_id = message.from_user.id

    if await funcIsBanned(message, user_id):
        return

    async with aiosqlite.connect('databases/roles.db') as db:
        async with db.execute("SELECT isPublisher FROM roles WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()

    if result is not None and result[0] == 1:
        await message.answer(f"📰 <b>Управление предложенными постами.</b>",
                             reply_markup=kb.publishKeyboard)
    else:
        await message.answer("❌ <b>У вас нет прав на эту команду.</b>")