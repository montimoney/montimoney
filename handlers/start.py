from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from database.repository import (
    ensure_monthly_mandatory_expenses,
    ensure_user,
    get_balance,
    get_credit_card_balance,
    get_main_message_id,
    get_monthly_mandatory_expenses,
    save_main_message_id,
)

from database.session import session_factory

from keyboards.main import main_keyboard

from utils.dates import (
    get_days_until_salary,
    get_next_salary_date,
)

from utils.messages import delete_user_message
from utils.screens import show_screen



router = Router()


def format_money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " ₽"


def format_days(days: int) -> str:
    if days == 0:
        return "сегодня"

    if days % 10 == 1 and days % 100 != 11:
        return f"{days} день"

    if days % 10 in (2, 3, 4) and days % 100 not in (12, 13, 14):
        return f"{days} дня"

    return f"{days} дней"


async def build_main_screen(user_id: int) -> str:

    async with session_factory() as session:

        balance = await get_balance(
            session,
            user_id,
        )

        credit_card = await get_credit_card_balance(
            session,
            user_id,
        )

        mandatory_expenses = await get_monthly_mandatory_expenses(
            session,
            user_id,
        )


    mandatory_lines = []
    mandatory_total = 0


    for expense in mandatory_expenses:

        remaining = max(
            expense.amount - expense.paid_amount,
            0,
        )

        if remaining == 0:

            paid_date = (
                expense.paid_at.strftime("%d.%m")
                if expense.paid_at
                else "оплачено"
            )

            mandatory_lines.append(
                f"✅ {expense.name} · {paid_date}"
            )

            continue


        mandatory_total += remaining


        if expense.paid_amount > 0:

            mandatory_lines.append(
                f"◐ {expense.name} — "
                f"{format_money(expense.paid_amount)} / "
                f"{format_money(expense.amount)}"
            )

        else:

            mandatory_lines.append(
                f"• {expense.name} — "
                f"{format_money(expense.amount)}"
            )


    mandatory_text = (
        "\n".join(mandatory_lines)
        if mandatory_lines
        else "Обязательных расходов пока нет"
    )


    days = get_days_until_salary()
    salary_date = get_next_salary_date()


    return (
        "🐱 <b>MonttiMoney</b>\n\n"
        "💰 <b>Баланс</b>\n"
        f"{format_money(balance)}\n\n"
        "💳 <b>Кредитка</b>\n"
        f"{format_money(credit_card)}\n\n"
        "📅 <b>До зарплаты</b>\n"
        f"{format_days(days)} · "
        f"{salary_date.strftime('%d.%m')}\n\n"
        "🔒 <b>Обязательные расходы</b>\n\n"
        f"{mandatory_text}\n\n"
        f"<b>Осталось оплатить: "
        f"{format_money(mandatory_total)}</b>"
    )


async def show_main_screen(
    message: Message,
) -> None:

    if message.from_user is None:
        return


    await show_screen(
        message,
        await build_main_screen(
            message.from_user.id,
        ),
        reply_markup=main_keyboard,
        parse_mode="HTML",
    )
    

@router.message(F.text == "🏠 Главный экран")
async def main_screen_button(
    message: Message,
):

    if message.from_user is None:
        return

    await delete_user_message(message)

    await show_main_screen(message)

@router.message(CommandStart())
async def start_handler(
    message: Message,
):

    if message.from_user is None:
        return


    async with session_factory() as session:

        await ensure_user(
            session=session,
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
        )

        await ensure_monthly_mandatory_expenses(
            session=session,
            user_id=message.from_user.id,
        )


    await delete_user_message(message)

    await show_main_screen(message)
