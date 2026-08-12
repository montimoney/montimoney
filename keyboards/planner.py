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

def planner_salary_choice_keyboard(
    salaries,
) -> ReplyKeyboardMarkup:
    buttons = []

    for salary in salaries:
        amount_text = (
            f"{salary.amount:,}"
            .replace(",", " ")
        )

        buttons.append(
            [
                KeyboardButton(
                    text=(
                        f"💰 {salary.planned_date.strftime('%d.%m')} "
                        f"— {amount_text} ₽"
                    ),
                )
            ]
        )

    buttons.append(
        [
            KeyboardButton(
                text="⬅️ Назад в план",
            )
        ]
    )

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
    )