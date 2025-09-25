from config import bot, fsmPlaceholderTextRetry

import app.keyboards as kb

import databases.roles as dbr
import databases.posts as dbp

import aiosqlite
from datetime import datetime

from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import ValueError


callbacks = Router()



# /admin
# callback F.data == "adminAdd"
class fsmAdminAdd(StatesGroup):
    user_id = State()
    role = State()

callbacks.callback_query(F.data == "adminAdd")
async def cbAdminAdd(callback: CallbackQuery, state: FSMContext):
    await state.set_state(fsmAdminAdd.user_id)

    await callback.message.edit_text("<b>Сейчас нужно будет отправить Telegram ID нужного человека и, настроить ему права.</b>\n"
                          "Отправьте в следующем сообщении Telegram ID нужного человека. Если вы его не знаете, отмените текущую операцию (командой /cancel), а затем пропишите команду /getid.",
                          reply_markup=None)
    
@callbacks.message(fsmAdminAdd.user_id)
async def fsmAdminAddUserId(message: Message, state: FSMContext):
    try:
        user_id = int(message.text)
        await state.update_data(user_id=user_id)
        
        data = await state.get_data()
        fsmUserId = data.get('user_id')

        user = await bot.get_chat(fsmUserId)
        found_username = user.username if user.username else f"<code>{user.id}</code>"
        await message.answer(f"<b>Какими правами должен обладать @{found_username}</b>\n\n"
                             "📰 <b>Публикатор</b> — убирает ограничение по времени между предложением постов.\n"
                             "🛡️ <b>Модератор</b> — добавляет возможность модерировать предложенные посты. <i>+возможности публикатора</i>\n"
                             "🪪 <b>Администратор</b> — может (де)верифицировать людей, кроме других админов. <i>+возможности публикатора и модератора</i>",
                             reply_markup=kb.adminKeyboardAdd)
        
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
    fsmUserId = data.get('user_id')

    #match sta.ole:


# /publish
# callback F.data == "publishAdd"
class fsmPublishAdd(StatesGroup):
    text = State()
    multimedia = State()

callbacks.callback_query(F.data == "publishAdd")
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
    data = await state.get_data
    fsmText = data.get('text')