import os

from aiogram import Bot
from aiogram.enums.parse_mode import ParseMode
from aiogram.types import LabeledPrice, Message, PreCheckoutQuery, CallbackQuery

from handlers.database import Database
from keyboards.payment_keyboard import PaymentKeyboard

from handlers.buildscript import LIFETIME_HOURS

async def send_invoice_handler(query: CallbackQuery, bot: Bot, hours: int):
    database = Database()
    price = await database.get_hours_price(query.message.chat.id, hours)

    if price <= 0:
        await success_payment_script(query.message, bot, hours)
        return

    title = "Доступ навсегда"
    if hours < LIFETIME_HOURS:
        title = f"Время: {hours} часов"

    message = query.message
    await message.answer_invoice(
        title=title,
        description="Оплата времени",
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

    user_hours = await database.get_user_hours(telegramid) + hours
    await database.set_user_hours(telegramid, user_hours)

    success_text = f"""
<b>🎉 Поздравляем! Оплата успешно прошла!</b>

⏳ На ваш аккаунт добавлено <b>{hours} часов</b>.
Теперь общее количество времени на вашем балансе: <b>{user_hours} часов</b>.

📦 Вы можете использовать это время для генерации билда для ваших аккаунтов.
Чтобы создать билд, выполните команду: 
<code>/build telegramid hours</code>

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
