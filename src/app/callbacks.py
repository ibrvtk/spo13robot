from config import bot

import app.keyboards as kb

import databases.roles as dbr
#import databases.posts as dbp

import aiosqlite
import time

from aiogram import F, Router
from aiogram.types import (
    CallbackQuery, Message,
    ReplyKeyboardMarkup, KeyboardButton,
    InputMediaPhoto, InputMediaVideo, InputMediaDocument
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup


callbacks = Router()
mediafilesPinned = {}
post_id_count = 0
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
async def timeoutCleanup():
    currentTime = time.time()
    for user_id, data in list(mediafilesPinned.items()):
        if currentTime > data['timeout']:
            del mediafilesPinned[user_id]

class fsmPublishAdd(StatesGroup):
    text = State()
    mediafiles = State()
    preview = State()

@callbacks.callback_query(F.data == "publishAdd")
async def cbPublishAdd(callback: CallbackQuery, state: FSMContext):
    mediafilesPinned[callback.from_user.id] = {
        'user_id': callback.from_user.id,
        'mediafilesType': "None",
        'mediafiles_id': [],
        'mediafilesCount': 0,
        'timeout': time.time() + 300
    }

    await state.set_state(fsmPublishAdd.text)

    await callback.message.edit_text("<b>Сейчас нужно будет написать содержание поста и, опционально, прикрепить мультимедиа.</b>\n"
                          "Отправьте в следующем сообщении содержание поста. Можно использовать <a href='https://core.telegram.org/api/entities#allowed-entities'>HTML-форматирование</a>.",
                          reply_markup=None)
    
@callbacks.message(fsmPublishAdd.text)
async def fsmPublishAddText(message: Message, state: FSMContext):
    await state.update_data(text=message.html_text)
    await state.set_state(fsmPublishAdd.mediafiles)

    await message.answer("Теперь отправьте медиафайл <i>(видео, фотографии, документы)</i>.\nМожно отправить до 10 медиафайлов "
                         "<i>(не смешивайте разные типы медиафайлов: в одном посте должны быть только фото, только видео или только документы)</i>.",
                         reply_markup=[[ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="Без медиафайлов")]],
                             resize_keyboard=True,
                             input_field_placeholder="Прикрепите медиафайлы...",
                             one_time_keyboard=True
                         )]])

@callbacks.message(fsmPublishAdd.mediafiles)
async def fsmPublishAddMediafiles(message: Message, state: FSMContext):
    user_id = message.from_user.id
    fsmPlaceholderTextMediafileTypeWrong = "<b>Один или несколько медиафайлов не соответствуют остальным и не будут добавлены.</b>"
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Готово")]],
        resize_keyboard=True, 
        one_time_keyboard=True
    )

    await timeoutCleanup()

    if message.text == "Без медиафайлов":
        await state.update_data(mediafiles=None)
        await state.set_state(fsmPublishAdd.preview)
        return

    if message.photo:
        if mediafilesPinned[user_id]['mediafilesType'] in ["None", "photo"] and mediafilesPinned[user_id]['mediafilesCount'] < 10:
            mediafilesPinned[user_id]['mediafilesType'] = "photo"
            mediafilesPinned[user_id]['mediafiles_id'].append(message.photo[-1].file_id)
            mediafilesPinned[user_id]['mediafilesCount'] += 1
            mediafilesPinned[user_id]['timeout'] = time.time() + 300
            await message.reply("✅",
                                reply_markup=keyboard)
        else:
            await message.reply(fsmPlaceholderTextMediafileTypeWrong)
            
    elif message.video:
        if mediafilesPinned[user_id]['mediafilesType'] in ["None", "video"] and mediafilesPinned[user_id]['mediafilesCount'] < 10:
            mediafilesPinned[user_id]['mediafilesType'] = "video"
            mediafilesPinned[user_id]['mediafiles_id'].append(message.video.file_id)
            mediafilesPinned[user_id]['mediafilesCount'] += 1
            mediafilesPinned[user_id]['timeout'] = time.time() + 300
            await message.reply("✅",
                                reply_markup=keyboard)
        else:
            await message.reply(fsmPlaceholderTextMediafileTypeWrong)

    elif message.document:
        if mediafilesPinned[user_id]['mediafilesType'] in ["None", "document"] and mediafilesPinned[user_id]['mediafilesCount'] < 10:
            mediafilesPinned[user_id]['mediafilesType'] = "document"
            mediafilesPinned[user_id]['mediafiles_id'].append(message.document.file_id)
            mediafilesPinned[user_id]['mediafilesCount'] += 1
            mediafilesPinned[user_id]['timeout'] = time.time() + 300
            await message.reply("✅",
                                reply_markup=keyboard)
        else:
            await message.reply(fsmPlaceholderTextMediafileTypeWrong)

@callbacks.message(F.text == "Готово")
async def textDone(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if mediafilesPinned[user_id]['mediafilesType'] != "None":
        await timeoutCleanup()
        await state.update_data(mediafiles=mediafilesPinned[user_id]['mediafiles_id'])
        await state.set_state(fsmPublishAdd.preview)
        return
    
@callbacks.message(fsmPublishAdd.preview)
async def fsmPublishAddPreview(message: Message, state: FSMContext):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Принять"), KeyboardButton(text="📝 Изменить"), KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True, 
        one_time_keyboard=True
    )

    data = await state.get_data()
    text = data.get('text')

    mediafiles = data.get('mediafiles', [])
    mediafilesType = data.get('mediafilesType', "None")

    if mediafiles and mediafilesType != "None":
        mediafilesGroup = []
        
        for i, file_id in enumerate(mediafiles): # enumerate подсказала ИИ
            if mediafilesType == "photo":
                if i == 0: mediafilesGroup.append(InputMediaPhoto(media=file_id, caption=text, parse_mode='HTML'))
                else: mediafilesGroup.append(InputMediaPhoto(media=file_id))
            
            elif mediafilesType == "video":
                if i == 0: mediafilesGroup.append(InputMediaVideo(media=file_id, caption=text, parse_mode='HTML'))
                else: mediafilesGroup.append(InputMediaVideo(media=file_id))
            
            elif mediafilesType == "document":
                if i == 0: mediafilesGroup.append(InputMediaDocument(media=file_id, caption=text, parse_mode='HTML'))
                else: mediafilesGroup.append(InputMediaDocument(media=file_id))

        await message.answer_media_group(mediafilesGroup,
                                         reply_markup=keyboard)
    
    else:
        await message.answer(text, parse_mode='HTML', reply_markup=keyboard)

@callbacks.message((F.text == "✅ Принять") | (F.text == "❌ Отмена"))
async def textApplyOrCancel(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if message.text == "✅ Принять":
        data = await state.get_data()
        text = data.get('text')
        mediafiles = data.get('mediafiles', [])
        
        post_id_count += 1

    elif message.text == "❌ Отмена":
        del mediafilesPinned[user_id]
        await state.clear()
        await message.answer("✅ <b>Предложение поста отменено.</b>",
                             reply_markup=None)