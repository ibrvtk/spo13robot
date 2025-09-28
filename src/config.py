from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from os import getenv

load_dotenv()

TOKEN = getenv("TOKEN")
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))

SUPERADMINS = [] # Список суперадминов. Они могут назначать новых, обычных админов в боте.


# Заранее прописаные тексты.
colleagueName = "🟢 <b>ПК им. П. А. Овчинникова</b>"
