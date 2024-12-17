import os

from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery, CallbackQuery, BufferedInputFile

from handlers.database import Database
from handlers.helpers import get_pretty_hours
from handlers.buildscript import generate_build, generate_key, calc_expiredate
from keyboards.payment_keyboard import PaymentKeyboard

async def send_invoice_handler(query: CallbackQuery, bot: Bot, hours: int):
    database = Database()
    price = await database.get_hours_price(query.message.chat.id, hours)

    if price <= 0:
        await success_payment_script(query.message, bot, hours)
        return

    title = f"Время: {get_pretty_hours(hours)}"

    message = query.message
    await message.answer_invoice(
        title=title,
        description="Покупка времени",
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

    is_test_period = hours < 1

    if not is_test_period:    
        user_hours = await database.get_user_hours(telegramid) + hours
        await database.set_user_hours(telegramid, user_hours)

    if is_test_period:
        hours += 1/6 # test for 10 minutes

        expire_date = calc_expiredate(hours)
        # Generate the build
        try:
            key_content = generate_key(message.from_user.full_name or str(message.from_user.id), telegramid, expire_date)
            if key_content is None:
                raise Exception("Build error")
        except Exception as e:
            await message.answer(
                "❌ Произошла ошибка при попытке сгенерировать тестовый ключ.\n\n"
                "Свяжитесь с поддержкой (контакты указаны в приветственном сообщении)",
                parse_mode=ParseMode.HTML
            )
            print("Test generate key error:", e)
        
        # Send the archive
        await bot.send_document(
            message.chat.id,
            BufferedInputFile(key_content, filename=f"{telegramid}.key"),
            caption=f"""
<b>🎉 Поздравляем! Ваш тестовый ключ сгенерирован!</b>

💡 <i>Подсказка:</i> Получите актуальный билд с помощью команды <code>/build</code> и поместите ключ рядом с файлом memhash_worker
У вас есть 10 дополнительных минут на установку, в случае возникновения проблем - обратитесь в поддержку.

💙 <b>Приятного использования! Мы уверены, что вам понравится!</b>
            """,
            parse_mode=ParseMode.HTML
        )
        await database.create_build(telegramid, telegramid, expire_date)
        await database.create_buy(telegramid, hours, 0)

        return
    
    success_text = f"""
<b>🎉 Поздравляем! Оплата успешно прошла!</b>

⏳ На ваш аккаунт добавлено <b>{get_pretty_hours(hours)}</b>.
Теперь общее количество времени на вашем балансе: <b>{get_pretty_hours(await database.get_user_hours(telegramid))}</b>.

📦 Вы можете использовать это время для генерации ключей для ваших аккаунтов.
Чтобы создать ключ, выполните команду: 
<code>/key telegramid hours</code>

💡 <i>Совет:</i> Оптимизируйте своё время, распределяя часы между несколькими аккаунтами! 

💙 <b>Приятного использования! Мы уверены, что вам понравится!</b>
"""

    price = await database.get_hours_price(telegramid, hours)
    await database.create_buy(telegramid, hours, price)
    await message.answer(success_text, parse_mode=ParseMode.HTML)

async def success_payment_handler(message: Message, bot: Bot):
    if 'RAINBOWHASH_ALL_REFUND' in os.environ: # For tests
        await bot.refund_star_payment(
            message.chat.id,
            message.successful_payment.telegram_payment_charge_id
        )

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
