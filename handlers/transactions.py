from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.repository import (
    add_credit_card_debt,
    add_transaction,
    pay_credit_card_debt,
    save_category_keyword,
    get_user_categories,
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


    data = await state.get_data()


    category = CATEGORY_MAP.get(
        message.text
    )


    if category is None:

        category = message.text.strip()

        category = category.capitalize()


    async with session_factory() as session:

        await add_transaction(
            session=session,
            user_id=message.from_user.id,
            operation_type=data["operation_type"],
            amount=data["amount"],
            description=data["description"],
            category=category,
        )


        await save_category_keyword(
            session=session,
            user_id=message.from_user.id,
            keyword=data["keyword"],
            category=category,
        )


    old_message_id = data.get(
        "category_message_id"
    )


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



    amount = parse_amount(
        message.text
    )


    if amount is None:

        await delete_user_message(message)

        await send_temp_message(
            message,
            "🐱 Не нашла сумму",
        )

        return



    description = parse_description(
        message.text
    )


    async with session_factory() as session:


        if is_credit_card_payment(
            message.text
        ):

            balance = await pay_credit_card_debt(
                session=session,
                user_id=message.from_user.id,
                amount=amount,
            )


            await send_temp_message(
                message,
                (
                    "💳 Кредитка погашена\n\n"
                    f"Остаток долга: {balance} ₽"
                ),
            )


        else:


            operation_type = detect_operation_type(
                message.text
            )


            category = await detect_category(
                session=session,
                user_id=message.from_user.id,
                text=message.text,
            )


            if (
                category is None
                and operation_type == "expense"
            ):


                async with session_factory() as category_session:

                    user_categories = await get_user_categories(
                        session=category_session,
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


                await state.update_data(
                    operation_type=operation_type,
                    amount=amount,
                    description=description,
                    keyword=description.split()[0].lower(),
                    category_message_id=category_message.message_id,
                )


                await state.set_state(
                    CategoryState.waiting_category
                )


                await delete_user_message(message)

                return



            await add_transaction(
                session=session,
                user_id=message.from_user.id,
                operation_type=operation_type,
                amount=amount,
                description=description,
                category=category,
            )


            if (
                operation_type == "expense"
                and is_credit_card_expense(message.text)
            ):

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


            await send_temp_message(
                message,
                (
                    f"{text}\n\n"
                    f"{description} — {amount} ₽"
                ),
            )


    await delete_user_message(message)

    await show_main_screen(message)
