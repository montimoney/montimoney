from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


planner_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="➕ Добавить в план",
            ),
        ],
        [
            KeyboardButton(
                text="✏️ Изменить план",
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


planner_add_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="💰 Зарплата",
            ),
            KeyboardButton(
                text="💸 Траты",
            ),
        ],
        [
            KeyboardButton(
                text="⬅️ Назад в план",
            ),
        ],
    ],
    resize_keyboard=True,
)

planner_back_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(
                text="⬅️ Назад в план",
            ),
        ],
    ],
    resize_keyboard=True,
)