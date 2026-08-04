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
                text="🗑 Удалить категорию",
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


def build_category_delete_keyboard(
    categories: list[str],
) -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(
                text=f"🗑 {category}",
            )
        ]
        for category in categories
    ]

    keyboard.append(
        [
            KeyboardButton(
                text="⬅️ Назад в корректировку",
            )
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
    )