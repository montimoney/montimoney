from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


undo_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="✅ Да, удалить",
            ),
            KeyboardButton(
                text="❌ Оставить",
            ),
        ],
    ],
    resize_keyboard=True,
)
