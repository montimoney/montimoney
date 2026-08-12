from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.repository import (
    add_planner_expense,
    add_planner_salary,
    get_planner_expenses,
    get_planner_salaries,
)
from database.session import session_factory

from handlers.start import show_main_screen

from keyboards.planner import (
    planner_add_keyboard,
    planner_back_keyboard,
    planner_keyboard,
    planner_salary_choice_keyboard,
)

from utils.messages import delete_user_message
from utils.screens import show_screen
from utils.states import PlannerAddState


router = Router()


def format_money(amount: int) -> str:
    return f"{amount:,}".replace(",", " ") + " ₽"


def salary_button_text(salary) -> str:
    return (
        f"💰 {salary.planned_date.strftime('%d.%m')} "
        f"— {format_money(salary.amount)}"
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

        salary_expenses = {}

        for salary in salaries:
            salary_expenses[salary.id] = await get_planner_expenses(
                session=session,
                user_id=user_id,
                salary_id=salary.id,
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
    total_expenses = 0

    for salary in salaries:
        salary_status = (
            " ✅"
            if salary.is_completed
            else ""
        )

        lines.append(
            f"💰 <b>{salary.planned_date.strftime('%d.%m')} "
            f"— {format_money(salary.amount)}</b>"
            f"{salary_status}"
        )

        expenses = salary_expenses.get(
            salary.id,
            [],
        )

        salary_expense_total = 0

        if expenses:
            for expense in expenses:
                expense_status = (
                    "✅"
                    if expense.is_completed
                    else "•"
                )

                lines.append(
                    f"{expense_status} "
                    f"{expense.name} — "
                    f"{format_money(expense.amount)}"
                )

                salary_expense_total += expense.amount

        else:
            lines.append(
                "• Траты пока не добавлены"
            )

        remaining = (
            salary.amount
            - salary_expense_total
        )

        if remaining >= 0:
            lines.append(
                f"Останется: "
                f"<b>{format_money(remaining)}</b>"
            )
        else:
            lines.append(
                f"⚠️ Не хватает: "
                f"<b>{format_money(abs(remaining))}</b>"
            )

        lines.append("")

        total_salary += salary.amount
        total_expenses += salary_expense_total

    total_remaining = (
        total_salary - total_expenses
    )

    lines.append(
        f"💰 Запланировано получить: "
        f"<b>{format_money(total_salary)}</b>"
    )

    lines.append(
        f"💸 Запланировано потратить: "
        f"<b>{format_money(total_expenses)}</b>"
    )

    if total_remaining >= 0:
        lines.append(
            f"✨ Останется: "
            f"<b>{format_money(total_remaining)}</b>"
        )
    else:
        lines.append(
            f"⚠️ Не хватает: "
            f"<b>{format_money(abs(total_remaining))}</b>"
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


# ВАЖНО:
# этот обработчик стоит ДО обработчиков состояний,
# чтобы кнопка "Назад" работала на любом этапе ввода.

@router.message(F.text == "⬅️ Назад в план")
async def back_to_planner(
    message: Message,
    state: FSMContext,
):
    await delete_user_message(message)
    await state.clear()

    await show_planner_screen(message)


# --------------------
# ЗАРПЛАТА
# --------------------

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
                "Напиши в формате: "
                "<b>25.08</b>"
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
            "Напиши только сумму, например: "
            "<b>60000</b>"
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
                "Напиши только число, например: "
                "<b>60000</b>"
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


# --------------------
# ТРАТЫ
# --------------------

@router.message(F.text == "💸 Траты")
async def planner_expense_start(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    await delete_user_message(message)

    now = datetime.now()

    async with session_factory() as session:
        salaries = await get_planner_salaries(
            session=session,
            user_id=message.from_user.id,
            month=now.month,
            year=now.year,
        )

    if not salaries:
        await show_screen(
            message=message,
            text=(
                "🐱 Сначала добавь зарплату.\n\n"
                "Трату нужно привязать к деньгам, "
                "из которых ты планируешь её оплатить."
            ),
            reply_markup=planner_back_keyboard,
        )
        return

    await state.set_state(
        PlannerAddState.waiting_expense_salary
    )

    await show_screen(
        message=message,
        text=(
            "💸 <b>Из какой зарплаты "
            "планируем потратить?</b>"
        ),
        reply_markup=planner_salary_choice_keyboard(
            salaries
        ),
        parse_mode="HTML",
    )


@router.message(
    PlannerAddState.waiting_expense_salary
)
async def planner_expense_salary(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    if message.text is None:
        return

    selected_text = message.text.strip()

    await delete_user_message(message)

    now = datetime.now()

    async with session_factory() as session:
        salaries = await get_planner_salaries(
            session=session,
            user_id=message.from_user.id,
            month=now.month,
            year=now.year,
        )

    selected_salary = None

    for salary in salaries:
        if salary_button_text(salary) == selected_text:
            selected_salary = salary
            break

    if selected_salary is None:
        await show_screen(
            message=message,
            text=(
                "🐱 Не смогла найти эту зарплату.\n\n"
                "Выбери её кнопкой ниже."
            ),
            reply_markup=planner_salary_choice_keyboard(
                salaries
            ),
        )
        return

    await state.update_data(
        expense_salary_id=selected_salary.id,
    )

    await state.set_state(
        PlannerAddState.waiting_expense_name
    )

    await show_screen(
        message=message,
        text=(
            "💸 <b>На что планируем потратить?</b>\n\n"
            "Напиши название.\n"
            "Например: <b>Рассрочка</b>"
        ),
        reply_markup=planner_back_keyboard,
        parse_mode="HTML",
    )


@router.message(
    PlannerAddState.waiting_expense_name
)
async def planner_expense_name(
    message: Message,
    state: FSMContext,
):
    if message.text is None:
        return

    name = message.text.strip()

    await delete_user_message(message)

    if not name:
        await show_screen(
            message=message,
            text=(
                "🐱 Напиши название траты.\n\n"
                "Например: <b>Красота</b>"
            ),
            reply_markup=planner_back_keyboard,
            parse_mode="HTML",
        )
        return

    await state.update_data(
        expense_name=name,
    )

    await state.set_state(
        PlannerAddState.waiting_expense_amount
    )

    await show_screen(
        message=message,
        text=(
            f"💸 <b>{name}</b>\n\n"
            "Сколько планируем потратить?\n"
            "Напиши, например: <b>7000</b>"
        ),
        reply_markup=planner_back_keyboard,
        parse_mode="HTML",
    )


@router.message(
    PlannerAddState.waiting_expense_amount
)
async def planner_expense_amount(
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
                "Напиши только число, например: "
                "<b>7000</b>"
            ),
            reply_markup=planner_back_keyboard,
            parse_mode="HTML",
        )
        return

    data = await state.get_data()

    salary_id = data.get(
        "expense_salary_id"
    )

    expense_name = data.get(
        "expense_name"
    )

    if salary_id is None or expense_name is None:
        await state.clear()

        await show_planner_screen(message)
        return

    async with session_factory() as session:
        await add_planner_expense(
            session=session,
            user_id=message.from_user.id,
            salary_id=salary_id,
            name=expense_name,
            amount=amount,
        )

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