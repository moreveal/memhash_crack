import os
import time
import asyncio
from datetime import datetime

from aiogram import F
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from handlers.paths import get_main_path
from handlers.database import Database
from handlers.buildscript import LIFETIME_HOURS
import handlers.payment as Payment

# from handlers.buildscript import generate_script
# with open(os.path.join(get_main_path(), 'output/build.zip'), 'wb') as f:
#     f.write(generate_script(1425589338))
# exit(1)

# SQLite
database = Database()

# Aiogram
bot = Bot(token=os.environ['RAINBOWHASH_API_TOKEN'])
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    with open(os.path.join(get_main_path(), 'start.md'), 'r', encoding='utf-8') as f:
        content = f.read()
    
    await database.create_new_user(message.from_user.id)
    await message.answer(content, parse_mode=ParseMode.MARKDOWN_V2, disable_web_page_preview=False)

@dp.message(Command("paysupport"))
async def cmd_paysupport(message: types.Message):
    await Payment.pay_support_handler(message)

@dp.message(Command("buy"))
async def cmd_buy(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="30 минут (0 ⭐)", callback_data="buy_test"),
                InlineKeyboardButton(text=f"8 часов ({await database.get_hours_price(message.from_user.id, 8)} ⭐)", callback_data="buy_8h", pay=True)
            ],
            [
                InlineKeyboardButton(text=f"24 часа ({await database.get_hours_price(message.from_user.id, 24)} ⭐)", callback_data="buy_24h", pay=True),
                InlineKeyboardButton(text=f"48 часов ({await database.get_hours_price(message.from_user.id, 48)} ⭐)", callback_data="buy_48h", pay=True)
            ],
            [
                InlineKeyboardButton(text=f"96 часов ({await database.get_hours_price(message.from_user.id, 96)} ⭐)", callback_data="buy_96h", pay=True),
                InlineKeyboardButton(text=f"Бессрочно ({await database.get_hours_price(message.from_user.id, LIFETIME_HOURS)} ⭐)", callback_data="buy_lifetime", pay=True)
            ],
            [
                InlineKeyboardButton(text="Отмена", callback_data="cancel")
            ]
        ]
    )

    await message.answer("Выберите вариант подписки:", reply_markup=keyboard)

@dp.callback_query(lambda callback: callback.data.startswith("buy_"))
async def process_buy(callback_query: types.CallbackQuery):
    telegramid = callback_query.from_user.id

    expire_date = await database.get_user_expires(telegramid)
    if time.time() < expire_date:
        await callback_query.message.answer(f"🫡 У вас уже есть активная подписка, дождитесь её завершения: {datetime.fromtimestamp(expire_date).strftime('%d.%m.%Y - %H:%M:%S')}")
        return

    if callback_query.data == "buy_test":
        hours = 0.5 # Test period

        already_tested = await database.is_user_tested(telegramid)
        if already_tested:
            await callback_query.message.answer("😔 Вы уже пользовались тестовым периодом или оплачивали подписку")
            return
        
        await Payment.success_payment_script(callback_query.message, bot, hours)
    else:
        hours = 8
        if callback_query.data == "buy_lifetime":
            hours = LIFETIME_HOURS
        else:
            hours = int(''.join(c if c.isdigit() else '' for c in callback_query.data))
        
        await Payment.send_invoice_handler(callback_query, bot, hours)

@dp.callback_query(lambda callback: callback.data == "cancel")
async def process_cancel(callback_query: types.CallbackQuery):
    await callback_query.answer("Покупка отменена.", show_alert=True)
    await callback_query.message.edit_text("Покупка отменена.")

# Entry point
async def main():
    try:
        # Database setup
        await database.init()

        dp.pre_checkout_query.register(Payment.pre_checkout_handler)
        dp.message.register(Payment.success_payment_handler, F.successful_payment)
        
        # Telegram bot
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
