from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.repository import (
    get_financial_totals,
    get_history,
    get_saving_goals,
)
from database.session import session_factory

from handlers.start import show_main_screen
from utils.advice import get_advice
from utils.messages import delete_user_message
from utils.screens import show_screen
from utils.states import AdviceState


router = Router()


@router.message(F.text == "💡 Совет дня")
async def show_advice(
    message: Message,
    state: FSMContext,
):

    if message.from_user is None:
        return

    await delete_user_message(message)

    async with session_factory() as session:

        income, expenses, balance = await get_financial_totals(
            session=session,
            user_id=message.from_user.id,
        )

        goals = await get_saving_goals(
            session=session,
            user_id=message.from_user.id,
        )

        history = await get_history(
            session=session,
            user_id=message.from_user.id,
            limit=50,
        )

    text = (
        "💡 <b>Совет дня</b>\n\n"
        + get_advice(
            income=income,
            expenses=expenses,
            goals_count=len(goals),
            history_count=len(history),
        )
        + "\n\n"
        "✍️ Напиши что угодно, чтобы вернуться на главный экран."
    )

    await state.set_state(AdviceState.waiting_exit)

    await show_screen(
        message,
        text,
    )


@router.message(AdviceState.waiting_exit)
async def close_advice(
    message: Message,
    state: FSMContext,
):

    await delete_user_message(message)

    await state.clear()

    await show_main_screen(message)
    