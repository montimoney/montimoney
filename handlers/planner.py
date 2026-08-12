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
from utils.states import PlannerAddState


router = Router()


async def delete_planner_message(
    message: Message,
    state: FSMContext,
) -> None:
    data = await state.get_data()

    planner_message_id = data.get("planner_message_id")

    if planner_message_id is None:
        return

    try:
        await message.bot.delete_message(
            chat_id=message.chat.id,
            message_id=planner_message_id,
        )
    except Exception:
        pass


async def send_planner_screen(
    message: Message,
    state: FSMContext,
    text: str,
    reply_markup,
) -> None:
    await delete_planner_message(
        message=message,
        state=state,
    )

    bot_message = await message.answer(
        text,
        reply_markup=reply_markup,
    )

    await state.update_data(
        planner_message_id=bot_message.message_id,
    )


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

    title = (
        f"📅 План на {month_names[now.month]}"
    )

    if not salaries:
        return (
            f"{title}\n\n"
            "Пока здесь пусто 🐱"
        )

    lines = [title, ""]

    total_salary = 0

    for salary in salaries:
        status = " ✅" if salary.is_completed else ""

        lines.append(
            f"💰 {salary.planned_date.strftime('%d.%m')} "
            f"— {salary.amount:,} ₽{status}".replace(",", " ")
        )

        total_salary += salary.amount

    lines.append("")
    lines.append(
        f"💰 Запланировано получить: "
        f"{total_salary:,} ₽".replace(",", " ")
    )

    return "\n".join(lines)


@router.message(F.text == "📅 План месяца")
async def show_planner(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    await state.clear()
    await delete_user_message(message)

    text = await build_planner_text(
        user_id=message.from_user.id,
    )

    await send_planner_screen(
        message=message,
        state=state,
        text=text,
        reply_markup=planner_keyboard,
    )


@router.message(F.text == "➕ Добавить в план")
async def planner_add(
    message: Message,
    state: FSMContext,
):
    await delete_user_message(message)

    await send_planner_screen(
        message=message,
        state=state,
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

    await send_planner_screen(
        message=message,
        state=state,
        text=(
            "💰 Добавляем зарплату\n\n"
            "На какую дату ждём деньги?\n"
            "Напиши, например: 25.08"
        ),
        reply_markup=planner_back_keyboard,
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

    await delete_user_message(message)

    try:
        parsed_date = datetime.strptime(
            message.text.strip(),
            "%d.%m",
        )

        now = datetime.now()

        planned_date = parsed_date.replace(
            year=now.year,
        ).date()

    except ValueError:
        await send_planner_screen(
            message=message,
            state=state,
            text=(
                "🐱 Не поняла дату.\n\n"
                "Напиши в формате: 25.08"
            ),
            reply_markup=planner_back_keyboard,
        )
        return

    await state.update_data(
        salary_date=planned_date.isoformat(),
    )

    await state.set_state(
        PlannerAddState.waiting_salary_amount
    )

    await send_planner_screen(
        message=message,
        state=state,
        text=(
            "💰 Сколько примерно придёт?\n\n"
            "Напиши только сумму, например: 60000"
        ),
        reply_markup=planner_back_keyboard,
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

    await delete_user_message(message)

    cleaned_amount = (
        message.text
        .replace(" ", "")
        .replace("₽", "")
        .strip()
    )

    try:
        amount = int(cleaned_amount)

        if amount <= 0:
            raise ValueError

    except ValueError:
        await send_planner_screen(
            message=message,
            state=state,
            text=(
                "🐱 Не поняла сумму.\n\n"
                "Напиши только число, например: 60000"
            ),
            reply_markup=planner_back_keyboard,
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

    await state.set_state(None)

    text = await build_planner_text(
        user_id=message.from_user.id,
    )

    await send_planner_screen(
        message=message,
        state=state,
        text=text,
        reply_markup=planner_keyboard,
    )


@router.message(F.text == "⬅️ Назад в план")
async def back_to_planner(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    await delete_user_message(message)

    await state.set_state(None)

    text = await build_planner_text(
        user_id=message.from_user.id,
    )

    await send_planner_screen(
        message=message,
        state=state,
        text=text,
        reply_markup=planner_keyboard,
    )


@router.message(F.text == "⬅️ Назад")
async def planner_back(
    message: Message,
    state: FSMContext,
):
    await delete_user_message(message)

    data = await state.get_data()
    planner_message_id = data.get("planner_message_id")

    if planner_message_id is not None:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=planner_message_id,
            )
        except Exception:
            pass

    await state.clear()
    await show_main_screen(message)