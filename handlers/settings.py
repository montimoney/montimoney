from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import asyncio

from keyboards.settings import settings_keyboard
from keyboards.main import main_keyboard
from keyboards.mandatory import mandatory_keyboard
from keyboards.correction import (
    correction_keyboard,
    build_category_delete_keyboard,
)

from database.session import session_factory
from database.repository import (
    get_monthly_mandatory_expenses,
    add_mandatory_template,
    update_mandatory_template,
    disable_mandatory_template,
    clear_user_data,
    get_credit_card_balance,
    set_credit_card_spent,
    get_user_categories,
    delete_user_category,
)
from database.models import MandatoryTemplate

from handlers.start import (
    build_main_screen,
    format_money,
    show_main_screen,
)

from utils.states import (
    MandatoryAddState,
    MandatoryEditState,
    MandatoryDeleteState,
    CreditCorrectionState,
    CategoryDeleteState,
)


from utils.messages import (
    delete_user_message,
    send_temp_message,
)
from utils.screens import show_screen


router = Router()


@router.message(F.text == "⚙️ Настройки")
async def open_settings(message: Message):

    await delete_user_message(message)

    await show_screen(
        message,
        (
            "⚙️ <b>Настройки</b>\n\n"
            "Выбери раздел:"
        ),
        reply_markup=settings_keyboard,
    )
@router.message(F.text == "🧹 Сбросить данные")
async def clear_data(message: Message):

    if message.from_user is None:
        return


    await delete_user_message(message)


    async with session_factory() as session:

        await clear_user_data(
            session=session,
            user_id=message.from_user.id,
        )


    await message.answer(
        "🧹 Все данные очищены.\n\n"
        "MonttiMoney готов начать с чистого листа 🐱"
    )
    

@router.message(F.text == "💅 Обязательные расходы")
async def mandatory_expenses_menu(message: Message):

    if message.from_user is None:
        return


    await delete_user_message(message)


    async with session_factory() as session:

        expenses = await get_monthly_mandatory_expenses(
            session,
            message.from_user.id,
        )


    if not expenses:

        text = "Пока обязательных расходов нет 🐱"

    else:

        lines = []

        for expense in expenses:

            remaining = expense.amount - expense.paid_amount

            if remaining == 0:

                lines.append(
                    f"✅ {expense.name}"
                )

            else:

                lines.append(
                    f"• {expense.name} — "
                    f"{format_money(remaining)}"
                )


        text = "\n".join(lines)


    await show_screen(
        message,
        (
            "💅 <b>Обязательные расходы</b>\n\n"
            f"{text}\n\n"
            "Выбери действие:"
        ),
        reply_markup=mandatory_keyboard,
    )


@router.message(F.text == "➕ Добавить")
async def add_mandatory_start(
    message: Message,
    state: FSMContext,
):

    await delete_user_message(message)

    await state.set_state(
        MandatoryAddState.waiting_name
    )

    bot_message = await message.answer(
        "💅 Напиши название нового обязательного расхода."
    )

    await state.update_data(
        bot_messages=[
            bot_message.message_id
        ]
    )


@router.message(MandatoryAddState.waiting_name)
async def add_mandatory_name(
    message: Message,
    state: FSMContext,
):

    data = await state.get_data()

    bot_messages = data.get(
        "bot_messages",
        []
    )


    bot_messages.append(
        message.message_id
    )


    bot_message = await message.answer(
        "💰 Теперь напиши сумму."
    )


    bot_messages.append(
        bot_message.message_id
    )


    await state.update_data(
        name=message.text,
        bot_messages=bot_messages,
    )


    await state.set_state(
        MandatoryAddState.waiting_amount
    )


@router.message(MandatoryAddState.waiting_amount)
async def add_mandatory_amount(
    message: Message,
    state: FSMContext,
):

    if not message.text.isdigit():

        await message.answer(
            "Напиши сумму цифрами 🐱"
        )

        return


    data = await state.get_data()


    bot_messages = data.get(
        "bot_messages",
        []
    )


    bot_messages.append(
        message.message_id
    )


    if message.from_user is None:
        return


    async with session_factory() as session:

        await add_mandatory_template(
            session,
            message.from_user.id,
            data["name"],
            int(message.text),
        )


    success_message = await message.answer(
        "✅ Обязательный расход добавлен"
    )


    bot_messages.append(
        success_message.message_id
    )


    await asyncio.sleep(2)


    for message_id in bot_messages:

        try:

            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=message_id,
            )

        except Exception:

            pass


    await state.clear()


    await show_main_screen(message)

@router.message(F.text == "✏️ Изменить")
async def edit_start(
    message: Message,
    state: FSMContext,
):

    await delete_user_message(message)

    await state.set_state(
        MandatoryEditState.waiting_name
    )

    bot_message = await message.answer(
        "✏️ Напиши расход, который изменить."
    )

    await state.update_data(
        bot_messages=[
            bot_message.message_id
        ]
    )


@router.message(MandatoryEditState.waiting_name)
async def edit_name(
    message: Message,
    state: FSMContext,
):

    if message.from_user is None:
        return


    data = await state.get_data()

    bot_messages = data.get(
        "bot_messages",
        []
    )


    bot_messages.append(
        message.message_id
    )


    async with session_factory() as session:

        expenses = await get_monthly_mandatory_expenses(
            session,
            message.from_user.id,
        )


    for expense in expenses:

        if expense.name.lower() in message.text.lower():

            bot_message = await message.answer(
                "💰 Напиши новую сумму."
            )

            bot_messages.append(
                bot_message.message_id
            )


            await state.update_data(
                template_id=expense.template_id,
                bot_messages=bot_messages,
            )


            await state.set_state(
                MandatoryEditState.waiting_amount
            )

            return


    await message.answer(
        "Не нашёл такой расход 🐱"
    )


@router.message(MandatoryEditState.waiting_amount)
async def edit_amount(
    message: Message,
    state: FSMContext,
):

    if not message.text.isdigit():
        return


    data = await state.get_data()

    bot_messages = data.get(
        "bot_messages",
        []
    )


    bot_messages.append(
        message.message_id
    )


    async with session_factory() as session:

        template = await session.get(
            MandatoryTemplate,
            data["template_id"],
        )

        await update_mandatory_template(
            session,
            template,
            int(message.text),
        )


    success = await message.answer(
        "✅ Расход изменён"
    )


    bot_messages.append(
        success.message_id
    )


    import asyncio

    await asyncio.sleep(2)


    for msg_id in bot_messages:

        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=msg_id,
            )

        except Exception:
            pass


    await state.clear()

    await show_main_screen(message)


@router.message(F.text == "🗑 Удалить")
async def delete_start(
    message: Message,
    state: FSMContext,
):

    await delete_user_message(message)

    await state.set_state(
        MandatoryDeleteState.waiting_name
    )

    bot_message = await message.answer(
        "🗑 Напиши расход, который убрать."
    )

    await state.update_data(
        bot_messages=[
            bot_message.message_id
        ]
    )

@router.message(MandatoryDeleteState.waiting_name)
async def delete_name(
    message: Message,
    state: FSMContext,
):

    if message.from_user is None:
        return


    data = await state.get_data()

    bot_messages = data.get(
        "bot_messages",
        []
    )


    bot_messages.append(
        message.message_id
    )


    async with session_factory() as session:

        expenses = await get_monthly_mandatory_expenses(
            session,
            message.from_user.id,
        )


    for expense in expenses:

        if expense.name.lower() in message.text.lower():

            async with session_factory() as session:

                template = await session.get(
                    MandatoryTemplate,
                    expense.template_id,
                )

                await disable_mandatory_template(
                    session,
                    template,
                )


            success = await message.answer(
                "✅ Расход убран из обязательных."
            )


            bot_messages.append(
                success.message_id
            )


            import asyncio

            await asyncio.sleep(2)


            for msg_id in bot_messages:

                try:

                    await message.bot.delete_message(
                        chat_id=message.chat.id,
                        message_id=msg_id,
                    )

                except Exception:
                    pass


            await state.clear()

            await show_main_screen(message)

            return


    await message.answer(
        "Не нашёл такой расход 🐱"
    )

@router.message(F.text == "🛠 Корректировка")
async def open_correction_menu(
    message: Message,
):
    if message.from_user is None:
        return

    await delete_user_message(message)

    async with session_factory() as session:
        (
            credit_limit,
            credit_spent,
            credit_available,
        ) = await get_credit_card_balance(
            session,
            message.from_user.id,
        )

    await show_screen(
        message,
        (
            "🛠 <b>Корректировка кредитки</b>\n\n"
            f"Лимит: {format_money(credit_limit)}\n"
            f"Потрачено: {format_money(credit_spent)}\n"
            f"Осталось: {format_money(credit_available)}\n\n"
            "Что хочешь указать?"
        ),
        reply_markup=correction_keyboard,
    )


@router.message(F.text == "💳 Указать потраченное")
async def correction_spent_start(
    message: Message,
    state: FSMContext,
):
    await delete_user_message(message)

    await state.set_state(
        CreditCorrectionState.waiting_spent
    )

    await message.answer(
        "💳 Напиши правильную сумму, которая сейчас "
        "потрачена с кредитки.\n\n"
        "Например: <b>32500</b>",
        parse_mode="HTML",
    )


@router.message(CreditCorrectionState.waiting_spent)
async def correction_spent_finish(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    if message.text is None:
        return

    clean_amount = (
        message.text
        .replace(" ", "")
        .replace("₽", "")
    )

    if not clean_amount.isdigit():
        await message.answer(
            "Напиши сумму только цифрами 🐱\n"
            "Например: 32500"
        )
        return

    spent_amount = int(clean_amount)

    async with session_factory() as session:
        (
            credit_limit,
            credit_spent,
            credit_available,
        ) = await set_credit_card_spent(
            session=session,
            user_id=message.from_user.id,
            spent_amount=spent_amount,
        )

    await state.clear()

    await message.answer(
        (
            "✅ Кредитка скорректирована\n\n"
            f"Лимит: {format_money(credit_limit)}\n"
            f"Потрачено: {format_money(credit_spent)}\n"
            f"Осталось: {format_money(credit_available)}"
        ),
        reply_markup=main_keyboard,
    )

    await show_main_screen(message)


@router.message(F.text == "💳 Указать остаток")
async def correction_available_start(
    message: Message,
    state: FSMContext,
):
    await delete_user_message(message)

    await state.set_state(
        CreditCorrectionState.waiting_available
    )

    await message.answer(
        "💳 Напиши правильный доступный остаток "
        "на кредитке.\n\n"
        "Например: <b>187500</b>",
        parse_mode="HTML",
    )


@router.message(CreditCorrectionState.waiting_available)
async def correction_available_finish(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    if message.text is None:
        return

    clean_amount = (
        message.text
        .replace(" ", "")
        .replace("₽", "")
    )

    if not clean_amount.isdigit():
        await message.answer(
            "Напиши сумму только цифрами 🐱\n"
            "Например: 187500"
        )
        return

    available_amount = int(clean_amount)

    async with session_factory() as session:
        (
            credit_limit,
            current_spent,
            current_available,
        ) = await get_credit_card_balance(
            session,
            message.from_user.id,
        )

        if available_amount > credit_limit:
            await message.answer(
                (
                    "Остаток не может быть больше лимита.\n\n"
                    f"Текущий лимит: "
                    f"{format_money(credit_limit)}"
                )
            )
            return

        spent_amount = (
            credit_limit - available_amount
        )

        (
            credit_limit,
            credit_spent,
            credit_available,
        ) = await set_credit_card_spent(
            session=session,
            user_id=message.from_user.id,
            spent_amount=spent_amount,
        )

    await state.clear()

    await message.answer(
        (
            "✅ Кредитка скорректирована\n\n"
            f"Лимит: {format_money(credit_limit)}\n"
            f"Потрачено: {format_money(credit_spent)}\n"
            f"Осталось: {format_money(credit_available)}"
        ),
        reply_markup=main_keyboard,
    )

    await show_main_screen(message)

@router.message(F.text == "🗑 Удалить категорию")
async def delete_category_start(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    await delete_user_message(message)

    async with session_factory() as session:
        categories = await get_user_categories(
            session=session,
            user_id=message.from_user.id,
        )

    if not categories:
        await send_temp_message(
            message,
            "Пользовательских категорий пока нет 🐱",
        )
        return

    bot_message = await message.answer(
        "🗑 Выбери категорию, которую нужно удалить.\n\n"
        "Старые расходы в истории останутся.",
        reply_markup=build_category_delete_keyboard(
            categories
        ),
    )

    await state.update_data(
        bot_messages=[bot_message.message_id]
    )

    await state.set_state(
        CategoryDeleteState.waiting_category
    )
@router.message(CategoryDeleteState.waiting_category)
async def delete_category_finish(
    message: Message,
    state: FSMContext,
):
    if message.from_user is None:
        return

    if message.text is None:
        return

    data = await state.get_data()
    bot_messages = data.get("bot_messages", [])

    bot_messages.append(message.message_id)

    if message.text == "⬅️ Назад в корректировку":
        for message_id in bot_messages:
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=message_id,
                )
            except Exception:
                pass

        await state.clear()

        await show_screen(
            message,
            "🛠 <b>Корректировка кредитки</b>\n\n"
            "Выбери действие:",
            reply_markup=correction_keyboard,
        )
        return

    category = message.text.removeprefix("🗑 ").strip()

    async with session_factory() as session:
        deleted_count = await delete_user_category(
            session=session,
            user_id=message.from_user.id,
            category=category,
        )

    if deleted_count == 0:
        text = "Не удалось найти такую категорию 🐱"
    else:
        text = (
            f"✅ Категория «{category}» удалена.\n\n"
            "Старые операции остались в истории."
        )

    result_message = await message.answer(
        text,
        reply_markup=correction_keyboard,
    )

    bot_messages.append(result_message.message_id)

    await asyncio.sleep(2)

    for message_id in bot_messages:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=message_id,
            )
        except Exception:
            pass

    await state.clear()

@router.message(F.text == "⬅️ Назад в настройки")
async def back_to_settings(
    message: Message,
    state: FSMContext,
):
    await state.clear()
    await delete_user_message(message)

    await show_screen(
        message,
        (
            "⚙️ <b>Настройки</b>\n\n"
            "Выбери раздел:"
        ),
        reply_markup=settings_keyboard,
    )

@router.message(F.text == "⬅️ Назад")
async def back_to_main(message: Message):

    if message.from_user is None:
        return


    await delete_user_message(message)

    await show_main_screen(message)
