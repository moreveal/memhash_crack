import os
import aiosqlite

from handlers.paths import get_main_path

database_path = os.path.join(get_main_path(), 'users.db')

class Database:
    def __init__(self, path=database_path):
        self.path = path
    
    async def init(self):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
            CREATE TABLE IF NOT EXISTS "users" (
                "telegram_id"	INTEGER NOT NULL UNIQUE,
                "expire_date"	INTEGER NOT NULL DEFAULT 0,
                "test"          INTEGER NOT NULL DEFAULT 0,
                "donate"	    INTEGER DEFAULT 0
                "tag"           TEXT DEFAULT '-'
            );
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS "unique_offers" (
                "telegram_id"	INTEGER NOT NULL,
                "hours"	INTEGER NOT NULL,
                "price"	INTEGER NOT NULL
            );          
            """)

            await db.commit()

    async def create_new_user(self, telegramid: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute('INSERT OR IGNORE INTO users (telegram_id) VALUES (?)', (telegramid,))
            await db.commit()

    async def create_buy(self, telegramid: int, expire_date: int, hours: int = 0, price: int = 0):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("UPDATE users SET expire_date = ?, donate = donate + ? WHERE telegram_id = ?", (expire_date, price, telegramid)) as cursor:
                if cursor.rowcount < 1:
                    await db.execute('INSERT INTO users (telegram_id) VALUES (?)', (telegramid,))
                    await db.execute("UPDATE users SET expire_date = ?, donate = donate + ? WHERE telegram_id = ?", (expire_date, price, telegramid))

            await db.execute("UPDATE users SET test = 1 WHERE telegram_id = ?", (telegramid,))
            await db.execute("DELETE FROM unique_offers WHERE telegram_id = ? AND hours = ?", (telegramid, int(hours)))
            await db.commit()

    async def is_user_tested(self, telegramid: int):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT test FROM users WHERE telegram_id = ?", (telegramid,)) as cursor:
                async for row in cursor:
                    return row[0] > 0
            
        return False

    async def get_user_expires(self, telegramid: int):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT expire_date FROM users WHERE telegram_id = ?", (telegramid,)) as cursor:
                async for row in cursor:
                    return int(row[0])
        
        return 0

    async def get_hours_price(self, telegramid: int, hours):
        hours = int(hours)

        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT price FROM unique_offers WHERE telegram_id = ? AND hours = ?", (telegramid, hours)) as cursor:
                async for row in cursor:
                    return int(row[0])
                
                if hours < 1:
                    return 0
                if hours <= 8:
                    return 1000
                if hours <= 24:
                    return 1500
                if hours <= 48:
                    return 2500
                if hours <= 96:
                    return 5000
        
        return 50000
