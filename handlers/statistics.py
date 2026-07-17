from aiogram import Router, F
from aiogram.types import Message

from database.repository import (
    get_category_statistics,
    get_financial_totals,
)

from database.session import session_factory

from handlers.start import (
    format_money,
    show_main_screen,
)

from keyboards.statistics import statistics_keyboard

from utils.messages import delete_user_message
from utils.screens import show_screen


router = Router()


CATEGORY_ICONS = {
    "Кафе": "☕",
    "Продукты": "🛒",
    "Транспорт": "🚕",
    "Красота": "💅",
    "Дом": "🏠",
    "Здоровье": "💊",
    "Питомцы": "🐱",
    "Подарки": "🎁",
    "WB": "🛍",
    "Тренировки": "🏋️",
    "Авто": "🚗",
}



@router.message(F.text == "📊 Статистика")
async def show_statistics(
    message: Message,
):

    if message.from_user is None:
        return


    await delete_user_message(message)


    async with session_factory() as session:

        income, expenses, balance = await get_financial_totals(
            session=session,
            user_id=message.from_user.id,
        )

        statistics = await get_category_statistics(
            session=session,
            user_id=message.from_user.id,
        )


    category_lines = []


    for category, amount in statistics:

        icon = CATEGORY_ICONS.get(
            category,
            "📌",
        )

        category_lines.append(
            f"{icon} {category} — "
            f"{format_money(amount)}"
        )


    categories_text = (
        "\n".join(category_lines)
        if category_lines
        else "Расходов пока нет"
    )


    text = (
        "📊 <b>Статистика</b>\n\n"
        "💰 <b>Доходы</b>\n"
        f"{format_money(income)}\n\n"
        "💸 <b>Расходы</b>\n"
        f"{format_money(expenses)}\n\n"
        "💵 <b>Баланс</b>\n"
        f"{format_money(balance)}\n\n"
        "🏷 <b>По категориям</b>\n\n"
        f"{categories_text}"
    )


    await show_screen(
        message,
        text,
        reply_markup=statistics_keyboard,
    )



@router.message(F.text == "⬅️ Назад")
async def statistics_back(
    message: Message,
):

    if message.from_user is None:
        return


    await delete_user_message(message)

    await show_main_screen(message)
    