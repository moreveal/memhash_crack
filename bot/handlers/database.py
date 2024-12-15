import os
import time
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
                "test"          INTEGER NOT NULL DEFAULT 0,
                "donate"	    INTEGER NOT NULL DEFAULT 0,
                "hours"         INTEGER NOT NULL DEFAULT 0,
                "tag"           TEXT DEFAULT '-'
            );
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS "builds" (
                "user_id"       INTEGER NOT NULL,
                "telegram_id"   INTEGER NOT NULL,
                "timestamp"     INTEGER NOT NULL,
                "expire_date"   INTEGER NOT NULL,
                             
                UNIQUE(user_id, telegram_id, timestamp)
            );
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS "unique_offers" (
                "telegram_id"	INTEGER NOT NULL,
                "hours"	INTEGER NOT NULL,
                "price"	INTEGER NOT NULL
            );          
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS "referrals" (
                "user_id" INTEGER NOT NULL,
                "friend_id" INTEGER NOT NULL UNIQUE,
                "hours" INTEGER DEFAULT 0,
                "referrer_used" INTEGER DEFAULT 0
            );
            """)

            await db.commit()

    async def create_new_user(self, telegramid: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute('INSERT OR IGNORE INTO users (telegram_id) VALUES (?)', (telegramid,))
            await db.commit()

    async def is_user_exists(self, telegramid: int):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT telegram_id FROM users WHERE telegram_id = ?", (telegramid,)) as cursor:
                return len(await cursor.fetchall()) > 0
        
        return False
    
    async def create_referral(self, referrer: int, referral: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT OR IGNORE INTO referrals (user_id, friend_id) VALUES (?,?)", (referrer, referral))
            await db.commit()

    async def create_buy(self, telegramid: int, hours: int = 0, price: int = 0):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("UPDATE users SET donate = donate + ? WHERE telegram_id = ?", (price, telegramid)) as cursor:
                if cursor.rowcount < 1:
                    await db.execute('INSERT INTO users (telegram_id) VALUES (?)', (telegramid,))
                    await db.execute("UPDATE users SET donate = donate + ? WHERE telegram_id = ?", (price, telegramid))

            await db.execute("UPDATE users SET test = 1 WHERE telegram_id = ?", (telegramid,))

            if hours > 0 and price > 0:
                # Referral handle
                await db.execute("UPDATE referrals SET hours = ? WHERE friend_id = ? AND hours = 0 AND referrer_used = 0", (hours, telegramid))

                # Referrer handle
                await db.execute("UPDATE referrals SET referrer_used = 1 WHERE user_id = ? AND hours = ? AND referrer_used = 0", (telegramid, hours))

            await db.execute("DELETE FROM unique_offers WHERE telegram_id = ? AND hours = ?", (telegramid, int(hours)))
            await db.commit()

    async def create_build(self, telegramid: int, target_telegramid: int, expire_date: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT INTO builds (user_id, telegram_id, timestamp, expire_date) VALUES (?, ?, ?, ?)", (telegramid, target_telegramid, int(time.time()), expire_date))
            await db.commit()

    async def is_user_tested(self, telegramid: int):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT test FROM users WHERE telegram_id = ?", (telegramid,)) as cursor:
                async for row in cursor:
                    return row[0] > 0
            
        return False

    async def get_build_expires(self, userid: int, telegramid: int):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT expire_date FROM builds WHERE user_id = ? AND telegram_id = ? ORDER BY expire_date DESC LIMIT 1", (userid, telegramid)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return int(row[0])
        
        return 0
    
    async def get_user_hours(self, telegramid: int):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT hours FROM users WHERE telegram_id = ?", (telegramid,)) as cursor:
                async for row in cursor:
                    return int(row[0])
                
        return 0
    
    async def get_pretty_user_hours(self, telegramid: int):
        hours = await self.get_user_hours(telegramid)

        def numeral_noun_declension(
            number,
            nominative_singular,
            genetive_singular,
            nominative_plural
        ):
            return (
                (number in range(5, 20)) and nominative_plural or
                (1 in (number, (diglast := number % 10))) and nominative_singular or
                ({number, diglast} & {2, 3, 4}) and genetive_singular or nominative_plural
            )

        return f"{hours} {numeral_noun_declension(hours, 'час', 'часа', 'часов')}"
    
    async def set_user_hours(self, telegramid: int, hours: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE users SET hours = ? WHERE telegram_id = ?", (hours, telegramid))
            await db.commit()

    async def get_hours_price(self, telegramid: int, hours):
        hours = int(hours)

        price = 60000
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT price FROM unique_offers WHERE telegram_id = ? AND hours = ?", (telegramid, hours)) as cursor:
                async for row in cursor:
                    return int(row[0])
                
                if hours < 1:
                    price = 0
                elif hours <= 8:
                    price = 1500
                elif hours <= 24:
                    price = 2500
                elif hours <= 48:
                    price = 4000
                elif hours <= 96:
                    price = 6500
                elif hours <= 350:
                    price = 17500
            
            # Discount for referrers
            async with db.execute("SELECT friend_id FROM referrals WHERE user_id = ? AND hours = ? AND referrer_used = 0", (telegramid, hours)) as cursor:
                referrals_buy_it = len(await cursor.fetchall())
                discount = min(20 * referrals_buy_it, 100) # 20% discount for every referral (100% max)
                if discount > 0:
                    price *= (100 - discount) / 100

            # Discount for referrals
            async with db.execute("SELECT friend_id FROM referrals WHERE friend_id = ? AND hours = 0 AND referrer_used = 0", (telegramid,)) as cursor:
                if len(await cursor.fetchall()) > 0:
                    price *= 0.9 # 10% discount

        return int(price)
