from aiogram import Router, F
from aiogram.types import Message

from database.repository import get_history
from database.session import session_factory

from handlers.start import show_main_screen

from keyboards.history import history_keyboard

from utils.messages import delete_user_message
from utils.screens import show_screen


router = Router()


def format_money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " ₽"



@router.message(F.text == "📜 История")
async def show_history(
    message: Message,
):

    if message.from_user is None:
        return


    await delete_user_message(message)


    async with session_factory() as session:

        transactions = await get_history(
            session=session,
            user_id=message.from_user.id,
        )


    if not transactions:

        text = (
            "📜 <b>История</b>\n\n"
            "Записей пока нет 🐱"
        )

    else:

        lines = []
        last_date = None


        for transaction in transactions:

            current_date = (
                transaction.created_at.strftime("%d.%m")
            )


            if current_date != last_date:

                lines.append(
                    f"\n<b>{current_date}</b>"
                )

                last_date = current_date


            icon = (
                "💰"
                if transaction.operation_type == "income"
                else "💸"
            )


            sign = (
                "+"
                if transaction.operation_type == "income"
                else "-"
            )


            lines.append(
                f"{icon} "
                f"{transaction.description} — "
                f"{sign}{format_money(transaction.amount)}"
            )


        text = (
            "📜 <b>История</b>\n\n"
            + "\n".join(lines)
        )


    await show_screen(
        message,
        text,
        reply_markup=history_keyboard,
    )



@router.message(F.text == "⬅️ Назад")
async def history_back(
    message: Message,
):

    if message.from_user is None:
        return


    await delete_user_message(message)

    await show_main_screen(message)
    