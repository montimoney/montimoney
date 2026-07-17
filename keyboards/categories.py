from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


BASE_CATEGORIES = [
    "☕ Кафе",
    "🛒 Продукты",
    "🚕 Транспорт",
    "💅 Красота",
    "🏠 Дом",
    "💊 Здоровье",
    "🐱 Питомцы",
    "🎁 Подарки",
    "🛍 WB",
    "🏋️ Тренировки",
    "🚗 Авто",
]


def build_category_keyboard(
    extra_categories: list[str] | None = None,
) -> ReplyKeyboardMarkup:

    categories = BASE_CATEGORIES.copy()


    if extra_categories:

        for category in extra_categories:

            if category not in categories:
                categories.append(category)


    buttons = []


    for i in range(0, len(categories), 2):

        buttons.append(
            [
                KeyboardButton(
                    text=categories[i]
                ),
                KeyboardButton(
                    text=categories[i + 1]
                )
                if i + 1 < len(categories)
                else KeyboardButton(text=""),
            ]
        )


    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
    )
