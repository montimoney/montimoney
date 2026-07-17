from aiogram import F, Router
from aiogram.types import Message

from database.repository import (
    add_to_saving_goal,
    create_saving_goal,
    find_saving_goal,
    get_saving_goals,
)

from database.session import session_factory

from handlers.start import show_main_screen

from keyboards.savings import savings_keyboard

from utils.messages import delete_user_message
from utils.screens import show_screen


router = Router()


def progress_bar(saved: int, target: int) -> str:

    if target <= 0:
        return "░░░░░░░░░░ 0%"

    percent = int(saved / target * 100)

    filled = max(1, int(percent / 10))

    if percent >= 100:
        return "██████████ 100% 🎉"

    return (
        "█" * filled
        + "░" * (10 - filled)
        + f" {percent}%"
    )


async def build_goals_text(user_id: int) -> str:

    async with session_factory() as session:

        goals = await get_saving_goals(
            session=session,
            user_id=user_id,
        )


    if not goals:

        return (
            "🎯 <b>Мои копилки</b>\n\n"
            "Копилок пока нет 🐱"
        )


    lines = []


    for goal in goals:

        lines.append(
            f"🎯 <b>{goal.name}</b>\n"
            f"{progress_bar(goal.saved_amount, goal.target_amount)}\n"
            f"{goal.saved_amount} / "
            f"{goal.target_amount} ₽"
        )


    return (
        "🎯 <b>Мои копилки</b>\n\n"
        + "\n\n".join(lines)
    )



@router.message(F.text.lower().startswith("копилка "))
async def create_goal(message: Message):

    if message.from_user is None:
        return


    parts = message.text.split()


    if len(parts) < 3:
        return


    name = parts[1]


    try:
        amount = int(parts[2])

    except ValueError:
        return


    await delete_user_message(message)


    async with session_factory() as session:

        goal = await create_saving_goal(
            session=session,
            user_id=message.from_user.id,
            name=name,
            target_amount=amount,
        )


    await show_screen(
        message,
        (
            "🎯 <b>Создала копилку</b>\n\n"
            f"{goal.name}\n"
            f"Цель: {goal.target_amount} ₽\n"
            f"{progress_bar(0, goal.target_amount)}"
        ),
        reply_markup=savings_keyboard,
    )



@router.message(F.text.lower().startswith("в "))
async def add_money(message: Message):

    if message.from_user is None:
        return


    parts = message.text.lower().split()


    if len(parts) < 3:
        return


    name = parts[1]


    try:
        amount = int(parts[2])

    except ValueError:
        return


    async with session_factory() as session:

        goal = await find_saving_goal(
            session=session,
            user_id=message.from_user.id,
            name=name,
        )


        if goal is None:
            return


        await add_to_saving_goal(
            session=session,
            goal=goal,
            amount=amount,
        )


    await delete_user_message(message)


    await show_screen(
        message,
        (
            "🎯 <b>Пополнение копилки</b>\n\n"
            f"{goal.name}\n\n"
            f"{progress_bar(goal.saved_amount, goal.target_amount)}\n\n"
            f"{goal.saved_amount} / "
            f"{goal.target_amount} ₽"
        ),
        reply_markup=savings_keyboard,
    )



@router.message(F.text == "🎯 Копилки")
async def open_savings(message: Message):

    if message.from_user is None:
        return


    await delete_user_message(message)


    await show_screen(
        message,
        await build_goals_text(
            message.from_user.id,
        ),
        reply_markup=savings_keyboard,
    )



@router.message(F.text == "⬅️ Назад")
async def savings_back(message: Message):

    if message.from_user is None:
        return


    await delete_user_message(message)

    await show_main_screen(message)
    