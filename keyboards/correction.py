from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


correction_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="💳 Указать потраченное",
            ),
        ],
        [
            KeyboardButton(
                text="💳 Указать остаток",
            ),
        ],
        [
            KeyboardButton(
                text="⬅️ Назад в настройки",
            ),
        ],
    ],
    resize_keyboard=True,
)