from aiogram.utils.keyboard import InlineKeyboardBuilder

def PaymentKeyboard(price: int):
    builder = InlineKeyboardBuilder()
    builder.button(text=f'Оплатить {price} ⭐', pay=True)

    return builder.as_markup()
