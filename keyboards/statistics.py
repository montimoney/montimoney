from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


statistics_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="⬅️ Назад",
            ),
        ],
    ],
    resize_keyboard=True,
)
