import zipfile
import os
from io import BytesIO
from datetime import datetime

from aiogram import Bot
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery, CallbackQuery, BufferedInputFile

from handlers.database import Database
from keyboards.payment_keyboard import PaymentKeyboard

from handlers.buildscript import generate_script, calc_expiredate, LIFETIME_HOURS

async def send_invoice_handler(query: CallbackQuery, hours: int):
    database = Database()
    price = await database.get_hours_price(query.message.chat.id, hours)

    title = "Доступ навсегда"
    if hours < LIFETIME_HOURS:
        title = f"Доступ на {hours} часов"

    message = query.message
    await message.answer_invoice(
        title=title,
        description="Позволяет пользоваться скриптом указанное количество времени",
        prices=[LabeledPrice(label='XTR', amount = price)],
        provider_token="",
        payload=f'buy_access_{hours}h',
        currency='XTR',
        reply_markup=PaymentKeyboard(price)
    )


async def pre_checkout_handler(query: PreCheckoutQuery):
    await query.answer(ok=True)

async def success_payment_script(message: Message, bot: Bot, hours: int):
    database = Database()
    telegramid = message.chat.id

    price = await database.get_hours_price(telegramid, hours)
    hours += 1/6 # 10 minutes for setup

    # Generate script and send it
    script = generate_script(telegramid, hours).encode()
    if script is None:
        await bot.send_message(message.chat.id, '❌ Произошла ошибка при попытке отправить файл.\n\nСвяжитесь с поддержкой (контакты указаны в приветственном сообщении)')
        return
    
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr('rainbow-hash/memhash-frontend.fly.dev/index.html', script)
    
    zip_buffer.seek(0)
    zip_file_content = zip_buffer.read()
    
    expire_date = calc_expiredate(hours)
    success_text = f'''
    🎉 Оплата прошла успешно

Ваша подписка действительна до: {datetime.fromtimestamp(expire_date).strftime("%d.%m.%Y - %H:%M:%S")}
💙 Удачного использования, вам обязательно понравится!
    '''
    await bot.send_document(message.chat.id, BufferedInputFile(zip_file_content, filename="rainbow_hash.zip"), caption=success_text.strip())
    await database.create_buy(telegramid, expire_date, hours, price)

async def success_payment_handler(message: Message, bot: Bot):
    if 'RAINBOWHASH_ALL_REFUND' in os.environ: # For tests
        await bot.refund_star_payment(
            message.chat.id,
            message.successful_payment.telegram_payment_charge_id
        )

    await message.answer("Заказ обрабатывается...")

    payload = message.successful_payment.invoice_payload
    if payload.startswith('buy_access'):
        hours = int(''.join(c if c.isdigit() else '' for c in payload))
        await success_payment_script(message, bot, hours)
    else:
        await message.answer('❌ Произошла ошибка при попытке оплаты.\n\nСвяжитесь с поддержкой (контакты указаны в приветственном сообщении)')

async def pay_support_handler(message: Message):
    await message.answer(
        text='''⚠️ Обратите внимание, что мы не несём ответственности за сохранность ваших аккаунтов.
Возврат средств по причине блокировки или каких-либо других санкций со стороны разработчиков - не предусмотрен.
        '''
    )
