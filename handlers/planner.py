from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from database.repository import (
    add_planner_expense,
    add_planner_salary,
    delete_planner_expense,
    get_planner_expense_by_id,
    get_planner_expenses,
    get_planner_salaries_from_current_month,
    move_planner_expense,
    toggle_planner_expense_completed,
    update_planner_expense_amount,
    get_planner_salaries_from_current_month,
)

from database.session import session_factory

from handlers.start import show_main_screen

from keyboards.planner import (
    planner_add_keyboard,
    planner_back_keyboard,
    planner_edit_keyboard,
    planner_expense_actions_keyboard,
    planner_expense_choice_keyboard,
    planner_keyboard,
    planner_salary_choice_keyboard,
)

from utils.messages import delete_user_message
from utils.screens import show_screen
from utils.states import (
    PlannerAddState,
    PlannerEditState,
)


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
        salaries = await get_planner_salaries_from_current_month(
            session=session,
            user_id=user_id,
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

    if not salaries:
        return (
            "📅 <b>План</b>\n\n"
            "Пока здесь пусто 🐱"
        )

    lines = [
        "📅 <b>План</b>",
        "",
    ]

    total_salary = 0
    total_expenses = 0

    current_group = None

    for salary in salaries:
        group_key = (
            salary.planned_date.year,
            salary.planned_date.month,
        )

        if group_key != current_group:
            current_group = group_key

            month_name = month_names[
                salary.planned_date.month
            ].upper()

            if salary.planned_date.year != now.year:
                month_title = (
                    f"{month_name} "
                    f"{salary.planned_date.year}"
                )
            else:
                month_title = month_name

            lines.append(
                f"━━━ <b>{month_title}</b> ━━━"
            )
            lines.append("")

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
        total_salary
        - total_expenses
    )

    lines.append(
        "━━━ <b>ИТОГО</b> ━━━"
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
        salaries = await get_planner_salaries_from_current_month(
            session=session,
            user_id=message.from_user.id,

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
        salaries = await get_planner_salaries_from_current_month(
            session=session,
            user_id=message.from_user.id,
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

# --------------------
# ИЗМЕНИТЬ ПЛАН
# --------------------

@router.message(F.text == "✏️ Изменить план")
async def planner_edit_start(
    message: Message,
    state: FSMContext,
):
    await delete_user_message(message)
    await state.clear()

    await show_screen(
        message=message,
        text="✏️ <b>Что изменяем?</b>",
        reply_markup=planner_edit_keyboard,
        parse_mode="HTML",
    )


@router.message(F.text == "💸 Изменить трату")
async def planner_edit_expense_start(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    await delete_user_message(message)

    now = datetime.now()

    async with session_factory() as session:
        salaries = await get_planner_salaries_from_current_month(
            session=session,
            user_id=message.from_user.id,
        )

    if not salaries:
        await show_screen(
            message=message,
            text="🐱 В этом месяце пока нет зарплат.",
            reply_markup=planner_back_keyboard,
        )
        return

    await state.set_state(
        PlannerEditState.waiting_expense_salary
    )

    await show_screen(
        message=message,
        text=(
            "💸 <b>У какой зарплаты "
            "находится трата?</b>"
        ),
        reply_markup=planner_salary_choice_keyboard(
            salaries
        ),
        parse_mode="HTML",
    )


@router.message(
    PlannerEditState.waiting_expense_salary
)
async def planner_edit_expense_salary(
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
        salaries = await get_planner_salaries_from_current_month(
            session=session,
            user_id=message.from_user.id,
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
                    "🐱 Не нашла эту зарплату.\n\n"
                    "Выбери её кнопкой ниже."
                ),
                reply_markup=planner_salary_choice_keyboard(
                    salaries
                ),
            )
            return

        expenses = await get_planner_expenses(
            session=session,
            user_id=message.from_user.id,
            salary_id=selected_salary.id,
        )

    if not expenses:
        await state.clear()

        await show_screen(
            message=message,
            text=(
                "🐱 У этой зарплаты пока нет трат."
            ),
            reply_markup=planner_back_keyboard,
        )
        return

    await state.update_data(
        edit_salary_id=selected_salary.id,
    )

    await state.set_state(
        PlannerEditState.waiting_expense
    )

    await show_screen(
        message=message,
        text="💸 <b>Какую трату изменяем?</b>",
        reply_markup=planner_expense_choice_keyboard(
            expenses
        ),
        parse_mode="HTML",
    )


@router.message(
    PlannerEditState.waiting_expense
)
async def planner_edit_expense_choice(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    if message.text is None:
        return

    selected_text = message.text.strip()

    await delete_user_message(message)

    data = await state.get_data()
    salary_id = data.get("edit_salary_id")

    if salary_id is None:
        await state.clear()
        await show_planner_screen(message)
        return

    async with session_factory() as session:
        expenses = await get_planner_expenses(
            session=session,
            user_id=message.from_user.id,
            salary_id=salary_id,
        )

    selected_expense = None

    for expense in expenses:
        amount_text = (
            f"{expense.amount:,}"
            .replace(",", " ")
        )

        status = (
            "✅ "
            if expense.is_completed
            else ""
        )

        button_text = (
            f"{status}{expense.name} "
            f"— {amount_text} ₽"
        )

        if button_text == selected_text:
            selected_expense = expense
            break

    if selected_expense is None:
        await show_screen(
            message=message,
            text=(
                "🐱 Не нашла эту трату.\n\n"
                "Выбери её кнопкой ниже."
            ),
            reply_markup=planner_expense_choice_keyboard(
                expenses
            ),
        )
        return

    await state.update_data(
        edit_expense_id=selected_expense.id,
    )

    await state.set_state(None)

    await show_screen(
        message=message,
        text=(
            f"💸 <b>{selected_expense.name}</b>\n"
            f"{format_money(selected_expense.amount)}\n\n"
            "Что делаем?"
        ),
        reply_markup=planner_expense_actions_keyboard,
        parse_mode="HTML",
    )

# --------------------
# ДЕЙСТВИЯ С ТРАТОЙ
# --------------------

@router.message(F.text == "✏️ Изменить сумму")
async def planner_expense_change_amount_start(
    message: Message,
    state: FSMContext,
):
    await delete_user_message(message)

    data = await state.get_data()

    if data.get("edit_expense_id") is None:
        await state.clear()
        await show_planner_screen(message)
        return

    await state.set_state(
        PlannerEditState.waiting_new_amount
    )

    await show_screen(
        message=message,
        text=(
            "✏️ <b>Новая сумма</b>\n\n"
            "Напиши новую сумму траты.\n"
            "Например: <b>5500</b>"
        ),
        reply_markup=planner_back_keyboard,
        parse_mode="HTML",
    )


@router.message(
    PlannerEditState.waiting_new_amount
)
async def planner_expense_change_amount_finish(
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
                "<b>5500</b>"
            ),
            reply_markup=planner_back_keyboard,
            parse_mode="HTML",
        )
        return

    data = await state.get_data()
    expense_id = data.get("edit_expense_id")

    async with session_factory() as session:
        expense = await get_planner_expense_by_id(
            session=session,
            user_id=message.from_user.id,
            expense_id=expense_id,
        )

        if expense is not None:
            await update_planner_expense_amount(
                session=session,
                expense=expense,
                new_amount=amount,
            )

    await state.clear()
    await show_planner_screen(message)


@router.message(F.text == "↔️ Перенести")
async def planner_expense_move_start(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    await delete_user_message(message)

    data = await state.get_data()

    if data.get("edit_expense_id") is None:
        await state.clear()
        await show_planner_screen(message)
        return

    now = datetime.now()

    async with session_factory() as session:
        salaries = await get_planner_salaries_from_current_month(
               session=session,
               user_id=message.from_user.id,
        )

    await state.set_state(
        PlannerEditState.waiting_move_salary
    )

    await show_screen(
        message=message,
        text=(
            "↔️ <b>К какой зарплате перенести трату?</b>"
        ),
        reply_markup=planner_salary_choice_keyboard(
            salaries
        ),
        parse_mode="HTML",
    )


@router.message(
    PlannerEditState.waiting_move_salary
)
async def planner_expense_move_finish(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    if message.text is None:
        return

    selected_text = message.text.strip()

    await delete_user_message(message)

    data = await state.get_data()
    expense_id = data.get("edit_expense_id")

    now = datetime.now()

    async with session_factory() as session:
        salaries = await get_planner_salaries_from_current_month(
              session=session,
              user_id=message.from_user.id,
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
                    "🐱 Не нашла эту зарплату.\n\n"
                    "Выбери её кнопкой."
                ),
                reply_markup=planner_salary_choice_keyboard(
                    salaries
                ),
            )
            return

        expense = await get_planner_expense_by_id(
            session=session,
            user_id=message.from_user.id,
            expense_id=expense_id,
        )

        if expense is not None:
            await move_planner_expense(
                session=session,
                expense=expense,
                new_salary_id=selected_salary.id,
            )

    await state.clear()
    await show_planner_screen(message)


@router.message(F.text == "✅ Выполнено")
async def planner_expense_completed(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    await delete_user_message(message)

    data = await state.get_data()
    expense_id = data.get("edit_expense_id")

    if expense_id is not None:
        async with session_factory() as session:
            expense = await get_planner_expense_by_id(
                session=session,
                user_id=message.from_user.id,
                expense_id=expense_id,
            )

            if expense is not None:
                await toggle_planner_expense_completed(
                    session=session,
                    expense=expense,
                )

    await state.clear()
    await show_planner_screen(message)


@router.message(F.text == "🗑 Удалить")
async def planner_expense_delete(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    await delete_user_message(message)

    data = await state.get_data()
    expense_id = data.get("edit_expense_id")

    if expense_id is not None:
        async with session_factory() as session:
            expense = await get_planner_expense_by_id(
                session=session,
                user_id=message.from_user.id,
                expense_id=expense_id,
            )

            if expense is not None:
                await delete_planner_expense(
                    session=session,
                    expense=expense,
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