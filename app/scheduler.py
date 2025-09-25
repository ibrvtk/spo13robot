import asyncio
import databases.posts as dbp
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest

async def scheduler(bot: Bot):
    """
    Планировщик: проверяет, отправляет и удаляет посты.
    """
    while True:
        # Получаем все посты, которые уже пора отправить
        due_posts = await dbp.get_due_posts()

        for post in due_posts:
            post_id = post['post_id']
            try:
                # Отправляем пост в канал
                await bot.send_message(
                    chat_id=post['channel_id'],
                    text=post['text'],
                    parse_mode='HTML'
                )
                print(f"✅ Пост #{post_id} успешно отправлен.")
            except Exception as e:
                print(f"❌ Ошибка при отправке поста #{post_id}: {e}")
            finally:
                # Вне зависимости от успеха отправки, удаляем пост из очереди,
                # чтобы избежать повторных отправок или зацикливания на "битом" посте.
                await dbp.delete(post_id)

        # Ждем 60 секунд до следующей проверки
        await asyncio.sleep(60)