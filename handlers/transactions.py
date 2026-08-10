from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.repository import (
    add_credit_card_debt,
    add_transaction,
    find_mandatory_expense,
    get_user_categories,
    pay_credit_card_debt,
    pay_mandatory_expense,
    save_category_keyword,
)

from database.session import session_factory

from handlers.start import show_main_screen

from keyboards.categories import build_category_keyboard

from utils.categories import (
    detect_category,
    detect_operation_type,
)

from utils.categories_dict import (
    CATEGORY_ICONS,
    CUSTOM_CATEGORY_ICONS,
)

from utils.states import CategoryState

from utils.messages import (
    delete_user_message,
    send_temp_message,
)

from utils.parser import (
    is_credit_card_expense,
    is_credit_card_payment,
    parse_amount,
    parse_description,
)


router = Router()


IGNORED_BUTTONS = {
    "🏠 Главный экран",
    "📊 Статистика",
    "⚙️ Настройки",
    "🎯 Копилки",
    "📜 История",
    "💡 Совет дня",
    "💅 Обязательные расходы",
    "↩️ Отменить запись",
    "🧹 Сбросить данные",
    "⬅️ Назад",
    "✅ Да, удалить",
    "❌ Оставить",
}


CATEGORY_MAP = {
    "☕ Кафе": "Кафе",
    "🛒 Продукты": "Продукты",
    "🚕 Транспорт": "Транспорт",
    "💅 Красота": "Красота",
    "🏠 Дом": "Дом",
    "💊 Здоровье": "Здоровье",
    "🐱 Питомцы": "Питомцы",
    "🎁 Подарки": "Подарки",
    "🛍 WB": "WB",
    "🏋️ Тренировки": "Тренировки",
    "🚗 Авто": "Авто",
}


def format_category(category: str) -> str:
    icon = (
        CATEGORY_ICONS.get(category)
        or CUSTOM_CATEGORY_ICONS.get(category)
        or "📌"
    )

    return f"{icon} {category}"


@router.message(CategoryState.waiting_category)
async def choose_category(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    if message.text is None:
        return

    data = await state.get_data()

    category = CATEGORY_MAP.get(message.text)

    if category is None:
        category = message.text.strip().capitalize()

    async with session_factory() as session:
        await add_transaction(
            session=session,
            user_id=message.from_user.id,
            operation_type=data["operation_type"],
            amount=data["amount"],
            description=data["description"],
            category=category,
            is_credit_card=data.get("is_credit_card", False),
        )

        await save_category_keyword(
            session=session,
            user_id=message.from_user.id,
            keyword=data["keyword"],
            category=category,
        )

        if data.get("is_credit_card"):
            await add_credit_card_debt(
                session=session,
                user_id=message.from_user.id,
                amount=data["amount"],
            )

    old_message_id = data.get("category_message_id")

    if old_message_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=old_message_id,
            )
        except Exception:
            pass

    await state.clear()

    await delete_user_message(message)

    text = (
        "💰 Доход добавлен"
        if data["operation_type"] == "income"
        else "💸 Расход добавлен"
    )

    credit_card_text = (
        "\n💳 Сумма добавлена к долгу по кредитке"
        if data.get("is_credit_card")
        else ""
    )

    await send_temp_message(
        message,
        (
            f"{text}\n\n"
            f"{data['description']} — {data['amount']} ₽"
            f"{credit_card_text}"
        ),
    )

    await show_main_screen(message)


@router.message()
async def handle_text(
    message: Message,
    state: FSMContext,
):
    if message.text is None:
        return

    if message.from_user is None:
        return

    if message.text in IGNORED_BUTTONS:
        return

    amount = parse_amount(message.text)

    if amount is None:
        await delete_user_message(message)

        await send_temp_message(
            message,
            "🐱 Не нашла сумму",
        )

        return

    description = parse_description(message.text)

    async with session_factory() as session:
        # 1. Погашение долга по кредитной карте

        if is_credit_card_payment(message.text):
            balance = await pay_credit_card_debt(
                session=session,
                user_id=message.from_user.id,
                amount=amount,
            )

            await add_transaction(
                session=session,
                user_id=message.from_user.id,
                operation_type="expense",
                amount=amount,
                description="Погашение кредитки",
                category="Кредитка",
                is_credit_card=False,
            )

            await send_temp_message(
                message,
                (
                    "💳 Кредитка погашена\n\n"
                    f"Внесено: {amount} ₽\n"
                    f"Остаток долга: {balance} ₽\n\n"
                    "💸 Сумма вычтена из общего баланса"
                ),
            )

            await delete_user_message(message)
            await show_main_screen(message)

            return

        # 2. Определяем тип операции и кредитку

        operation_type = detect_operation_type(message.text)

        credit_card = (
            operation_type == "expense"
            and is_credit_card_expense(message.text)
        )

        # 3. Ищем обязательный расход

        mandatory_expense = None

        if operation_type == "expense":
            mandatory_expense = await find_mandatory_expense(
                    session=session,
                    user_id=message.from_user.id,
                    text=message.text,
                )

        # 4. Если нашли обязательный расход

            if mandatory_expense is not None:
                applied_amount = await pay_mandatory_expense(
                    session=session,
                    expense=mandatory_expense,
                    payment_amount=amount,
                )

                category = await detect_category(
                    session=session,
                    user_id=message.from_user.id,
                    text=description,
                )

                if category is None:
                    category = "Обязательные расходы"

                await add_transaction(
                    session=session,
                    user_id=message.from_user.id,
                    operation_type=operation_type,
                    amount=amount,
                    description=description,
                    category=category,
                    is_credit_card=credit_card,
                )

                if credit_card:
                    await add_credit_card_debt(
                        session=session,
                        user_id=message.from_user.id,
                        amount=amount,
                    )

                remaining = max(
                    mandatory_expense.amount
                    - mandatory_expense.paid_amount,
                    0,
                )

                if applied_amount == 0:
                    mandatory_text = (
                        "✅ Этот обязательный расход "
                        "уже был полностью оплачен"
                    )
                elif remaining == 0:
                    mandatory_text = (
                        "✅ Обязательный расход оплачен полностью"
                    )
                else:
                    mandatory_text = (
                        "💅 Учтено в обязательных расходах\n"
                        f"Осталось оплатить: {remaining} ₽"
                    )

                credit_card_text = (
                    "\n💳 Сумма добавлена к долгу по кредитке"
                    if credit_card
                    else ""
                )

                await send_temp_message(
                    message,
                    (
                        "💸 Расход добавлен\n\n"
                        f"{description} — {amount} ₽\n\n"
                        f"{mandatory_text}"
                        f"{credit_card_text}"
                    ),
                )

                await delete_user_message(message)
                await show_main_screen(message)

                return

            # 5. Ищем обычную категорию

            category = await detect_category(
                session=session,
                user_id=message.from_user.id,
                text=message.text,
            )

            # 6. Если категория неизвестна — спрашиваем пользователя

            if (
                category is None
                and operation_type == "expense"
            ):
                user_categories = await get_user_categories(
                    session=session,
                    user_id=message.from_user.id,
                )

                category_message = await message.answer(
                    (
                        "🐱 Не знаю, куда отнести:\n\n"
                        f"<b>{description}</b>\n\n"
                        "Выбери категорию "
                        "или напиши свою:"
                    ),
                    reply_markup=build_category_keyboard(
                        extra_categories=user_categories
                    ),
                    parse_mode="HTML",
                )

                keyword_parts = description.split()

                keyword = (
                    keyword_parts[0].lower()
                    if keyword_parts
                    else description.lower()
                )

                await state.update_data(
                    operation_type=operation_type,
                    amount=amount,
                    description=description,
                    keyword=keyword,
                    is_credit_card=credit_card,
                    category_message_id=category_message.message_id,
                )

                await state.set_state(
                    CategoryState.waiting_category
                )

                await delete_user_message(message)

                return

            # 7. Сохраняем обычную операцию

            await add_transaction(
                session=session,
                user_id=message.from_user.id,
                operation_type=operation_type,
                amount=amount,
                description=description,
                category=category,
                is_credit_card=credit_card,
                )

            if credit_card:
                await add_credit_card_debt(
                    session=session,
                    user_id=message.from_user.id,
                    amount=amount,
                )

            text = (
                "💰 Доход добавлен"
                if operation_type == "income"
                else "💸 Расход добавлен"
            )

            credit_card_text = (
                "\n💳 Сумма добавлена к долгу по кредитке"
                if credit_card
                else ""
            )

            await send_temp_message(
                message,
                (
                    f"{text}\n\n"
                    f"{description} — {amount} ₽"
                    f"{credit_card_text}"
                ),
            )

        await delete_user_message(message)

        await show_main_screen(message)