from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="🏠 Главный экран",
            ),
        ],
        [
            KeyboardButton(
                text="📜 История",
            ),
            KeyboardButton(
                text="📊 Статистика",
            ),
        ],
        [
            KeyboardButton(
                text="💡 Совет дня",
            ),
        ],
        [
            KeyboardButton(
                text="🎯 Копилки",
            ),
            KeyboardButton(
                text="⚙️ Настройки",
            ),
        ],
    ],
    resize_keyboard=True,
    input_field_placeholder="Например: кофе 350",
)