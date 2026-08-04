from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


settings_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="💅 Обязательные расходы",
            ),
        ],
        [
            KeyboardButton(
                text="🛠 Корректировка",
            ),
        ],
        [
            KeyboardButton(
                text="↩️ Отменить запись",
            ),
        ],
        [
            KeyboardButton(
                text="🧹 Сбросить данные",
            ),
        ],
        [
            KeyboardButton(
                text="⬅️ Назад",
            ),
        ],
    ],
    resize_keyboard=True,
)