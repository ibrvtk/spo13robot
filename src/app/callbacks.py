from config import bot

import app.keyboards as kb

import databases.roles as dbr
import databases.posts as dbp

import aiosqlite
from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


callbacks = Router()
fsmPlaceholderTextRetry = "\nПопробуйте снова или отмените действие (/cancel)."



# /admin
# callback F.data == "adminKeyboardAdd"
class fsmAdminAdd(StatesGroup):
    user_id = State()
    role = State()

@callbacks.callback_query(F.data == "adminKeyboardAdd")
async def cbAdminAdd(callback: CallbackQuery, state: FSMContext):
    await state.set_state(fsmAdminAdd.user_id)

    await callback.message.edit_text("<b>Сейчас нужно будет отправить Telegram ID нужного человека и, настроить ему права.</b>\n"
                          "Отправьте в следующем сообщении <u>Telegram ID</u> нужного человека <i>(не путать с @юзернеймом)</i>.",
                          reply_markup=None)
    
@callbacks.message(fsmAdminAdd.user_id)
async def fsmAdminAddUserId(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await state.update_data(user_id=user_id)
        
        data = await state.get_data()
        user_id = data.get('user_id')

        user = await bot.get_chat(user_id)
        found_username = user.username if user.username else f"<code>{user.id}</code>"
        await message.answer(f"<b>Какими правами должен обладать @{found_username}</b>\n\n"
                             "📰 <b>Публикатор</b> — убирает ограничение по времени между предложением постов.\n"
                             "🛡️ <b>Модератор</b> — добавляет возможность модерировать предложенные посты. <i>+возможности публикатора</i>\n"
                             "🪪 <b>Администратор</b> — может (де)верифицировать людей, кроме других админов. <i>+возможности публикатора и модератора</i>",
                             reply_markup=kb.adminKeyboardAddChooseRole)
        
        await state.set_state(fsmAdminAdd.role)
    
    except ValueError:
        await message.answer(f"❌ <b>Ошибка!</b> Такого пользователя не существует.{fsmPlaceholderTextRetry}")

    except Exception as e:
        await message.answer(f"❌ <b>Непредвиденная ошибка!</b> Возможно Вы ввели неправильный ID или такого пользователя не существует.{fsmPlaceholderTextRetry}")
        print(f"❌ Непредвиденная ошибка cbSuperadminAddUserId() (callbacks.py, /superadmin): {e}.")

@callbacks.message(fsmAdminAdd.role)
async def fsmAdminAddRole(message: Message, state: FSMContext):
    if message.text not in ("📰 Публикатор", "🛡️ Модератор", "🪪 Администратор"):
        await message.answer("❌ <b>Выберите из предложенных вариантов!</b>")
        return
    
    role = message.text
    await state.update_data(role=role)

    data = await state.get_data()
    user_id = data.get('user_id')

    match role:
        case "📰 Публикатор":
            async with aiosqlite.connect('databases/roles.db') as db:
                await db.execute("""
                    INSERT OR REPLACE INTO roles (user_id, isPublisher, isModerator, isAdmin, isBanned) 
                    VALUES (?, 1, 0, 0, 0)
                """, (user_id,))
                await db.commit()
        case "🛡️ Модератор":
            async with aiosqlite.connect('databases/roles.db') as db:
                await db.execute("""
                    INSERT OR REPLACE INTO roles (user_id, isPublisher, isModerator, isAdmin, isBanned) 
                    VALUES (?, 1, 1, 0, 0)
                """, (user_id,))
                await db.commit()
        case "🪪 Администратор":
            async with aiosqlite.connect('databases/roles.db') as db:
                await db.execute("""
                    INSERT OR REPLACE INTO roles (user_id, isPublisher, isModerator, isAdmin, isBanned) 
                    VALUES (?, 1, 1, 1, 0)
                """, (user_id,))
                await db.commit()

    user = await bot.get_chat(user_id)
    found_username = user.username if user.username else f"<code>{user.id}</code>"
    await message.answer(f"✅ <b>@{found_username} назначен {role}ом.</b>",
                         reply_markup=None)

    await state.clear()


# callback F.data == "adminList"
@callbacks.callback_query(F.data == "adminKeyboardList")
async def cbAdminKeyboardListBack(callback: CallbackQuery):
    await callback.message.edit_text("🪪 <b>Список верифицированных пользователей и управление их правами.</b>",
                        reply_markup=await kb.adminKeyboardList())

@callbacks.callback_query(F.data == "adminKeyboardListBack")
async def cbAdminKeyboardListBack(callback: CallbackQuery):
    await callback.message.edit_text("🪪 <b>Управление ролями.</b>",
                        reply_markup=kb.adminKeyboard)
    

@callbacks.callback_query(F.data.startswith("user_"))
async def cbAdminList(callback: CallbackQuery):
    user_id = int(callback.data.replace("user_", ""))
    
    async with aiosqlite.connect('databases/roles.db') as db:
        async with db.execute("SELECT isModerator, isPublisher, isAdmin, isBanned FROM roles WHERE user_id = ?", (user_id,)) as cursor:
            result = await cursor.fetchone()

        text = ""
        if result[0] == 1:
            text += "🛡️ Есть права модератора\n"
        if result[1] == 1:
            text += "📰 Есть права публикатора\n"
        if result[2] == 1:
            text += "🪪 Есть права администратора\n"

        user = await bot.get_chat(user_id)
        found_username = user.username if user.username else f"<code>{user.id}</code>"
        await callback.message.edit_text(f"<b>{found_username}</b>\n{text}",
                                         reply_markup=await kb.adminListActions_(user_id))


class fsmAdminListActionsChangeRole(StatesGroup):
    newRole = State()

@callbacks.callback_query(F.data.startswith("adminListActionsChangeRole_"))
async def cbAdminListActionsChangeRole(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.replace("adminListActionsChangeRole_", ""))

    await callback.message.delete()

    await state.update_data(user_id=user_id)
    await state.set_state(fsmAdminListActionsChangeRole.newRole)

    user = await bot.get_chat(user_id)
    found_username = user.username if user.username else f"<code>{user.id}</code>"
    await callback.message.answer(f"Выберите новую роль для {found_username}.",
                                     reply_markup=kb.adminKeyboardAddChooseRole)
    
@callbacks.message(fsmAdminListActionsChangeRole.newRole)
async def fsmAdminAddRole(message: Message, state: FSMContext):
    if message.text not in ("📰 Публикатор", "🛡️ Модератор", "🪪 Администратор"):
        await message.answer("❌ <b>Выберите из предложенных вариантов!</b>")
        return
    
    role = message.text
    await state.update_data(role=role)

    data = await state.get_data()
    user_id = data.get('user_id')

    match role:
        case "📰 Публикатор":
            async with aiosqlite.connect('databases/roles.db') as db:
                await db.execute("""
                    INSERT OR REPLACE INTO roles (user_id, isPublisher, isModerator, isAdmin, isBanned) 
                    VALUES (?, 1, 0, 0, 0)
                """, (user_id,))
                await db.commit()
        case "🛡️ Модератор":
            async with aiosqlite.connect('databases/roles.db') as db:
                await db.execute("""
                    INSERT OR REPLACE INTO roles (user_id, isPublisher, isModerator, isAdmin, isBanned) 
                    VALUES (?, 1, 1, 0, 0)
                """, (user_id,))
                await db.commit()
        case "🪪 Администратор":
            async with aiosqlite.connect('databases/roles.db') as db:
                await db.execute("""
                    INSERT OR REPLACE INTO roles (user_id, isPublisher, isModerator, isAdmin, isBanned) 
                    VALUES (?, 1, 1, 1, 0)
                """, (user_id,))
                await db.commit()

    user = await bot.get_chat(user_id)
    found_username = user.username if user.username else f"<code>{user.id}</code>"
    await message.answer(f"✅ <b>@{found_username} назначен {role}ом.</b>",
                         reply_markup=None)

    await state.clear()


@callbacks.callback_query(F.data.startswith("adminListActionsDelete_"))
async def cbPostsListActionsDelete(callback: CallbackQuery):
    user_id = int(callback.data.replace("adminListActionsDelete_", ""))
    await dbr.delete(user_id)

    user = await bot.get_chat(user_id)
    found_username = user.username if user.username else user.id
    await callback.answer(f"{found_username} больше не верифицирован.")
    await callback.message.edit_text("🪪 <b>Список верифицированных пользователей и управление их правами.</b>",
                        reply_markup=await kb.adminKeyboardList())
    
@callbacks.callback_query(F.data == "adminListActionsBack")
async def cbAdminListActionsBack(callback: CallbackQuery):
    await callback.message.edit_text("🪪 <b>Список верифицированных пользователей и управление их правами.</b>",
                        reply_markup=await kb.adminKeyboardList())


# /publish
# callback F.data == "publishAdd"
class fsmPublishAdd(StatesGroup):
    text = State()
    multimedia = State()

@callbacks.callback_query(F.data == "publishAdd")
async def cbPublishAdd(callback: CallbackQuery, state: FSMContext):
    await state.set_state(fsmPublishAdd.text)

    await callback.message.edit_text("<b>Сейчас нужно будет написать содержание поста и, опционально, прикрепить мультимедиа.</b>\n"
                          "Отправьте в следующем сообщении содержание поста. Можно использовать <a href='https://core.telegram.org/api/entities#allowed-entities'>HTML-форматирование</a>.",
                          reply_markup=None)
    
@callbacks.message(fsmPublishAdd.text)
async def fsmPublishAddText(message: Message, state: FSMContext):
    await state.update_data(text=message.html_text)
    await state.set_state(fsmPublishAdd.multimedia)

    await message.answer("Теперь отправьте мультимедиа <i>(видео, фотографии, документы)</i>.\nОтправьте прочерк (-) для их отсутствия.")

@callbacks.message(fsmPublishAdd.multimedia)
async def fsmPublishAddMultimedia(message: Message, state: FSMContext):
    data = await state.get_data()
    fsmText = data.get('text')