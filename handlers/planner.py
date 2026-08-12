from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.repository import (
    add_planner_salary,
    get_planner_salaries,
)
from database.session import session_factory

from handlers.start import show_main_screen

from keyboards.planner import (
    planner_add_keyboard,
    planner_back_keyboard,
    planner_keyboard,
)

from utils.messages import delete_user_message
from utils.screens import show_screen
from utils.states import PlannerAddState


router = Router()


async def build_planner_text(
    user_id: int,
) -> str:
    now = datetime.now()

    async with session_factory() as session:
        salaries = await get_planner_salaries(
            session=session,
            user_id=user_id,
            month=now.month,
            year=now.year,
        )

    month_names = {
        1: "январь",
        2: "февраль",
        3: "март",
        4: "апрель",
        5: "май",
        6: "июнь",
        7: "июль",
        8: "август",
        9: "сентябрь",
        10: "октябрь",
        11: "ноябрь",
        12: "декабрь",
    }

    title = f"📅 <b>План на {month_names[now.month]}</b>"

    if not salaries:
        return (
            f"{title}\n\n"
            "Пока здесь пусто 🐱"
        )

    lines = [title, ""]

    total_salary = 0

    for salary in salaries:
        status = " ✅" if salary.is_completed else ""

        amount_text = (
            f"{salary.amount:,}"
            .replace(",", " ")
        )

        lines.append(
            f"💰 {salary.planned_date.strftime('%d.%m')} "
            f"— {amount_text} ₽{status}"
        )

        total_salary += salary.amount

    total_text = (
        f"{total_salary:,}"
        .replace(",", " ")
    )

    lines.append("")
    lines.append(
        f"💰 <b>Запланировано получить: "
        f"{total_text} ₽</b>"
    )

    return "\n".join(lines)


async def show_planner_screen(
    message: Message,
) -> None:
    if message.from_user is None:
        return

    text = await build_planner_text(
        user_id=message.from_user.id,
    )

    await show_screen(
        message=message,
        text=text,
        reply_markup=planner_keyboard,
        parse_mode="HTML",
    )


@router.message(F.text == "📅 План месяца")
async def show_planner(
    message: Message,
    state: FSMContext,
):
    await state.clear()
    await delete_user_message(message)

    await show_planner_screen(message)


@router.message(F.text == "➕ Добавить в план")
async def planner_add(
    message: Message,
    state: FSMContext,
):
    await delete_user_message(message)

    await show_screen(
        message=message,
        text="Что добавляем?",
        reply_markup=planner_add_keyboard,
    )


@router.message(F.text == "💰 Зарплата")
async def planner_salary_start(
    message: Message,
    state: FSMContext,
):
    await delete_user_message(message)

    await state.set_state(
        PlannerAddState.waiting_salary_date
    )

    await show_screen(
        message=message,
        text=(
            "💰 <b>Добавляем зарплату</b>\n\n"
            "На какую дату ждём деньги?\n"
            "Напиши, например: <b>25.08</b>"
        ),
        reply_markup=planner_back_keyboard,
        parse_mode="HTML",
    )


@router.message(
    PlannerAddState.waiting_salary_date
)
async def planner_salary_date(
    message: Message,
    state: FSMContext,
):
    if message.text is None:
        return

    text = message.text.strip()

    await delete_user_message(message)

    try:
        parsed_date = datetime.strptime(
            text,
            "%d.%m",
        )

        now = datetime.now()

        planned_date = parsed_date.replace(
            year=now.year,
        ).date()

    except ValueError:
        await show_screen(
            message=message,
            text=(
                "🐱 Не поняла дату.\n\n"
                "Напиши в формате: <b>25.08</b>"
            ),
            reply_markup=planner_back_keyboard,
            parse_mode="HTML",
        )
        return

    await state.update_data(
        salary_date=planned_date.isoformat(),
    )

    await state.set_state(
        PlannerAddState.waiting_salary_amount
    )

    await show_screen(
        message=message,
        text=(
            "💰 <b>Сколько примерно придёт?</b>\n\n"
            "Напиши только сумму, например: <b>60000</b>"
        ),
        reply_markup=planner_back_keyboard,
        parse_mode="HTML",
    )


@router.message(
    PlannerAddState.waiting_salary_amount
)
async def planner_salary_amount(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    if message.text is None:
        return

    text = message.text

    await delete_user_message(message)

    cleaned_amount = (
        text
        .replace(" ", "")
        .replace("₽", "")
        .strip()
    )

    try:
        amount = int(cleaned_amount)

        if amount <= 0:
            raise ValueError

    except ValueError:
        await show_screen(
            message=message,
            text=(
                "🐱 Не поняла сумму.\n\n"
                "Напиши только число, например: <b>60000</b>"
            ),
            reply_markup=planner_back_keyboard,
            parse_mode="HTML",
        )
        return

    data = await state.get_data()

    salary_date = datetime.fromisoformat(
        data["salary_date"]
    ).date()

    async with session_factory() as session:
        await add_planner_salary(
            session=session,
            user_id=message.from_user.id,
            planned_date=salary_date,
            amount=amount,
        )

    await state.clear()

    await show_planner_screen(message)


@router.message(F.text == "⬅️ Назад в план")
async def back_to_planner(
    message: Message,
    state: FSMContext,
):
    await delete_user_message(message)
    await state.clear()

    await show_planner_screen(message)


@router.message(F.text == "⬅️ Назад")
async def planner_back(
    message: Message,
    state: FSMContext,
):
    await delete_user_message(message)
    await state.clear()

    await show_main_screen(message)