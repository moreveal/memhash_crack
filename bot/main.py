import os
import time
import asyncio
from datetime import datetime

from aiogram import F
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.types import BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from handlers.paths import get_main_path
from handlers.database import Database
from handlers.helpers import get_pretty_hours
from handlers.buildscript import generate_build, generate_key, calc_expiredate
from handlers.mailing import MailingState
import handlers.payment as Payment

from filters.is_admin import AdminFilter

# from handlers.buildscript import generate_build
# with open(os.path.join(get_main_path(), 'output/build.zip'), 'wb') as f:
#     f.write(generate_build(6384965964))
# exit(1)

# SQLite
database = Database()

# Aiogram
# bot = Bot('6818488855:AAHOEMVKUCZb2EpFoMsXY5NQwj1bzecZV4U') # Bot for tests only
bot = Bot(token=os.environ['RAINBOWHASH_API_TOKEN'])
dp = Dispatcher(storage=MemoryStorage())

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    with open(os.path.join(get_main_path(), 'start.html'), encoding='utf-8') as f:
        content = f.read()

    user_id = message.from_user.id

    referrer = None
    if " " in message.text:
        referrer_candidate = message.text.split()[1]

        try:
            referrer_candidate = int(referrer_candidate)

            if not await database.is_user_exists(user_id) and await database.is_user_exists(referrer_candidate):
                referrer = referrer_candidate
        except ValueError:
            pass

    if referrer:
        await database.create_referral(referrer, user_id)
    
    await database.create_new_user(message.from_user.id)
    await message.answer(content, parse_mode=ParseMode.HTML)

@dp.message(Command("paysupport"))
async def cmd_paysupport(message: types.Message):
    await Payment.pay_support_handler(message)

@dp.message(Command("changelog"))
async def cmd_changelog(message: types.Message):
    with open(os.path.join(get_main_path(), 'changelog.html'), encoding='utf-8') as f:
        content = f.read()

    await message.answer(content, parse_mode=ParseMode.HTML)

@dp.message(Command("referral"))
async def cmd_referral(message: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Получить реферальную ссылку", callback_data='get_referral_link')]
        ]
    )
    
    text = '''<b>Хотите сэкономить на подписке? Пригласите друга!</b> 💵

<i>📜 Условия </i>
- Каждый приглашенный друг получит 10% скидки на любой вариант подписки
- Вы получите 20% скидки к варианту подписки, оплаченным вашим другом

<i>📝 Примечания:</i>
- Скидка у пригласившего появится только после оплаты подписки другом
- Скидка на любой из вариант подписок для друга единоразовая
- Скидки от нескольких приглашённых друзей суммируются
(5 приглашённых = бесплатная подписка)
'''

    await message.answer(text, parse_mode=ParseMode.HTML, reply_markup=keyboard)

@dp.message(Command("buy"))
async def cmd_buy(message: types.Message):
    telegramid = message.from_user.id

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="30 минут (0 ⭐)", callback_data="buy_test"),
                InlineKeyboardButton(text=f"8 часов ({await database.get_hours_price(telegramid, 8)} ⭐)", callback_data="buy_8h", pay=True)
            ],
            [
                InlineKeyboardButton(text=f"24 часа ({await database.get_hours_price(telegramid, 24)} ⭐)", callback_data="buy_24h", pay=True),
                InlineKeyboardButton(text=f"48 часов ({await database.get_hours_price(telegramid, 48)} ⭐)", callback_data="buy_48h", pay=True)
            ],
            [
                InlineKeyboardButton(text=f"96 часов ({await database.get_hours_price(telegramid, 96)} ⭐)", callback_data="buy_96h", pay=True),
                InlineKeyboardButton(text=f"350 часов ({await database.get_hours_price(telegramid, 350)} ⭐)", callback_data="buy_350h", pay=True)
            ],
            [
                InlineKeyboardButton(text="Отмена", callback_data="cancel")
            ]
        ]
    )

    hours = await database.get_user_hours(telegramid)
    await message.answer(f"⏳ Ваш текущий баланс: <b>{get_pretty_hours(hours)}</b>\n\nВыберите количество часов для покупки:", reply_markup=keyboard, parse_mode=ParseMode.HTML)

@dp.message(Command("build"))
async def process_get_build(message: types.Message):
    try:
        await message.answer("⏳ Генерируется актуальный билд. Подождите, это займет немного времени...")
        zip_file_content = generate_build()
        
        if zip_file_content is None:
            raise Exception("Build error")

        success_text = f"""
<b>✅ Билд готов к загрузке!</b>

💡 <i>Совет:</i> Используйте <code>/key telegramid hours</code> для генерации ключей доступа.

🔑 Файл .key должен располагаться рядом с исполняемым файлом "memhash_worker" перед его запуском.
        """

        # Send the archive
        await bot.send_document(
            message.chat.id,
            BufferedInputFile(zip_file_content, filename=f"build.zip"),
            caption=success_text.strip(),
            parse_mode=ParseMode.HTML
        )

    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка при генерации билда. Попробуйте позже или обратитесь в поддержку.",
            parse_mode=ParseMode.HTML
        )
        print(f"Build error: {e}")

@dp.message(Command("key"))
async def process_generate_key(message: types.Message):
    telegramid = message.from_user.id

    # Extract the arguments
    try:
        command_parts = message.text.split()
        if len(command_parts) != 3:
            if len(command_parts) == 2:
                target_telegramid = int(telegramid)
                hours = int(command_parts[1])
            else:
                raise ValueError("Incorrect amount of arguments")
        else:
            target_telegramid = int(command_parts[1])
            hours = int(command_parts[2])

        if hours <= 0:
            raise ValueError("Incorrect amount of hours")
    except ValueError:
        await message.answer(
            "❌ Неверный формат команды.\n\n"
            "Используйте: <code>/key telegramid hours</code>\n"
            "Пример: <code>/key 2718291002 5</code>\n\n"
            "Вы также можете сгенерировать ключ для текущего аккаунта:\n"
            "Пример: <code>/key 5</code>\n\n"
            "<b><a href=\"https://pikabu.ru/story/kak_uznat_identifikator_telegram_kanalachatagruppyi_kak_uznat_chat_id_telegram_bez_botov_i_koda_11099278\">* Как узнать Telegram ID?</a></b>",
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True
        )
        return
    
    user_hours = await database.get_user_hours(telegramid)
    if user_hours < hours:
        await message.answer(
            f"❌ Недостаточно часов на вашем балансе.\n\n"
            f"Ваш баланс: <b>{get_pretty_hours(user_hours)}</b>\n"
            f"Для команды вы запрашиваете: <b>{get_pretty_hours(hours)}</b>\n\n"
            f"Пополните баланс, используя /buy",
            parse_mode=ParseMode.HTML
        )
        return

    expire_date = await database.get_build_expires(telegramid, target_telegramid)
    if time.time() < expire_date:
        await message.answer(f"🫡 На этом аккаунте уже есть активная подписка, дождитесь её завершения: {datetime.fromtimestamp(expire_date).strftime('%d.%m.%Y - %H:%M:%S')}")
        return

    remaining_hours = user_hours - hours
    await database.set_user_hours(telegramid, remaining_hours)
    
    await message.answer(f"🔑 Генерация ключа [{target_telegramid} / Hours: {hours}]")

    # Generate the key
    expire_date = calc_expiredate(hours)
    try:
        key_content = generate_key(message.from_user.full_name or str(message.from_user.id), target_telegramid, expire_date + 60)
        if key_content is None:
            raise Exception("Build error")
    except Exception as e:
        await message.answer(
            "❌ Произошла ошибка при попытке сгенерировать ключ.\n\n"
            "Свяжитесь с поддержкой (контакты указаны в приветственном сообщении)",
            parse_mode=ParseMode.HTML
        )
        print("Generate key error:", e)
        return

    success_text = f"""
<b>✅ Ключ успешно создан!</b>

📦 Для аккаунта: <b>{target_telegramid}</b>  
⏳ Использовано: <b>{get_pretty_hours(hours)}</b>  
📉 Оставшийся баланс: <b>{get_pretty_hours(remaining_hours)}</b>

📅 Ключ активен до: <b>{datetime.fromtimestamp(expire_date).strftime('%d.%m.%Y - %H:%M:%S')}</b>

⚡ Используйте данный ключ, поместив его рядом с исполняемым файлом воркера! 

💡 <i>Совет:</i> Билд можно скачать с помощью команды:  
<code>/build</code>

💙 Спасибо, что выбрали наш сервис! Мы рады помочь вам!
    """
    
    # Send the archive
    await bot.send_document(
        message.chat.id,
        BufferedInputFile(key_content, filename=f"{target_telegramid}.key"),
        caption=success_text.strip(),
        parse_mode=ParseMode.HTML
    )
    await database.create_build(telegramid, target_telegramid, expire_date)

@dp.callback_query(lambda callback: callback.data == "get_referral_link")
async def process_get_referral_link(callback_query: types.CallbackQuery):
    telegramid = callback_query.from_user.id

    me = await bot.get_me()
    referral_link = f"https://t.me/{me.username}?start={telegramid}"
    await callback_query.message.answer(f"Ваша реферальная ссылка:\n<code>{referral_link}</code>", parse_mode=ParseMode.HTML)

@dp.callback_query(lambda callback: callback.data.startswith("buy_"))
async def process_buy(callback_query: types.CallbackQuery):
    telegramid = callback_query.from_user.id

    if callback_query.data == "buy_test":
        hours = 0.5 # Test period

        already_tested = await database.is_user_tested(telegramid)
        if already_tested:
            await callback_query.message.answer("😔 Вы уже пользовались тестовым периодом или оплачивали подписку")
            return
        
        await Payment.success_payment_script(callback_query.message, bot, hours)
    else:
        hours = int(''.join(c if c.isdigit() else '' for c in callback_query.data))
        await Payment.send_invoice_handler(callback_query, bot, hours)

@dp.callback_query(lambda callback: callback.data == "cancel")
async def process_cancel(callback_query: types.CallbackQuery):
    await callback_query.answer("Покупка отменена.", show_alert=True)
    await callback_query.message.edit_text("Покупка отменена.")

# Admin commands
@dp.message(AdminFilter(), Command("mailing"))
async def command_mailing(message: types.Message, state: FSMContext):
    await state.set_state(MailingState.message)

    cancel_button = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text='Отмена', callback_data='cancel_mailing')]]
    )

    await message.answer(
        "Введите сообщение для рассылки ниже:",
        reply_markup=cancel_button
    )

@dp.callback_query(lambda callback: callback.data == "cancel_mailing")
async def cancel_mailing(callback_query: types.CallbackQuery, state: FSMContext):
    await state.clear()

    await callback_query.message.edit_text('Вы успешно отменили рассылку!')

@dp.message(MailingState.message)
async def process_mailing(message: types.Message, state: FSMContext):
    await state.update_data(message=message)
    await state.clear()

    await message.answer('Сообщение успешно отправлено всем участникам!')

    users = await database.get_all_users()
    for user in users:
        await bot.copy_message(chat_id=user, from_chat_id=message.chat.id, message_id=message.message_id)
# --------------

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
