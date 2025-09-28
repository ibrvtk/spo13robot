import aiosqlite



async def create():
    async with aiosqlite.connect('databases/posts.db') as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                author_id INTEGER PRIMARY KEY,
                post_id INTEGER,
                text TEXT,
                mediafiles TEXT,
                channel_id INTEGER,
            )
        """)
        await db.commit()


async def add(post_id: int, text: str, mediafiles: str, channel_id: int):
    async with aiosqlite.connect('databases/posts.db') as db:
        cursor = await db.execute("""
            INSERT INTO posts (post_id, text, mediafiles, channel_id)
            VALUES (?, ?, ?, ?)
        """, (post_id, text, mediafiles, channel_id))
        await db.commit()
        return cursor.lastrowid


async def deletePost(post_id: int):
    async with aiosqlite.connect('databases/posts.db') as db:
        await db.execute("DELETE FROM posts WHERE post_id = ?", (post_id,))
        await db.commit()

async def deleteAuthor(author_id: int):
    async with aiosqlite.connect('databases/posts.db') as db:
        await db.execute("DELETE FROM posts WHERE author_id = ?", (author_id,))
        await db.commit()