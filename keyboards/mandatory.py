from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


mandatory_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="➕ Добавить"),
            KeyboardButton(text="✏️ Изменить"),
        ],
        [
            KeyboardButton(text="🗑 Удалить"),
        ],
        [
            KeyboardButton(text="⬅️ Назад"),
        ],
    ],
    resize_keyboard=True,
)
