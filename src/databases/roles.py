import aiosqlite



async def create():
    async with aiosqlite.connect('databases/roles.db') as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS roles (
                user_id INTEGER PRIMARY KEY,
                isModerator INTEGER,
                isPublisher INTEGER,
                isAdmin INTEGER,
                isBanned INTEGER,
                allowedChannels TEXT
            )
        """)
        await db.commit()


async def add(isModerator: int, isPublisher: int, isAdmin: int, isBanned: int, allowedChannels: str):
    async with aiosqlite.connect('databases/roles.db') as db:
        cursor = await db.execute("""
            INSERT INTO roles (isModerator, isPublisher, isAdmin, isBanned, allowedChannels)
            VALUES (?, ?, ?, ?, ?)
        """, (isModerator, isPublisher, isAdmin, isBanned, allowedChannels))
        await db.commit()
        return cursor.lastrowid


async def delete(user_id: int):
    async with aiosqlite.connect('databases/roles.db') as db:
        await db.execute("DELETE FROM roles WHERE user_id = ?", (user_id,))
        await db.commit()