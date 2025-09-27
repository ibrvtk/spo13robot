import aiosqlite

import datetime



async def create():
    async with aiosqlite.connect('databases/posts.db') as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                post_id INTEGER PRIMARY KEY,
                text TEXT,
                time DATETIME,
                channel_id INTEGER,
                status TEXT
            )
        """)
        await db.commit()


async def add(text: str, time: datetime, channel_id: int):
    async with aiosqlite.connect('databases/posts.db') as db:
        cursor = await db.execute("""
            INSERT INTO posts (text, time, channel_id, status)
            VALUES (?, ?, ?, 'planned')
        """, (text, time, channel_id))
        await db.commit()
        return cursor.lastrowid


async def delete(post_id: int):
    async with aiosqlite.connect('databases/posts.db') as db:
        await db.execute("DELETE FROM posts WHERE post_id = ?", (post_id,))
        await db.commit()


async def get_due_posts():
    now = datetime.datetime.now()
    async with aiosqlite.connect('databases/posts.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT post_id, text, channel_id FROM posts WHERE time <= ?", (now,)) as cursor:
            return await cursor.fetchall()