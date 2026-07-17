from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


history_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="⬅️ Назад",
            ),
        ],
    ],
    resize_keyboard=True,
)
