from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
import asyncio

from keyboards.settings import settings_keyboard
from keyboards.main import main_keyboard
from keyboards.mandatory import mandatory_keyboard

from database.session import session_factory
from database.repository import (
    get_monthly_mandatory_expenses,
    add_mandatory_template,
    update_mandatory_template,
    disable_mandatory_template,
    clear_user_data,
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
)

from utils.messages import delete_user_message
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

@router.message(F.text == "⬅️ Назад")
async def back_to_main(message: Message):

    if message.from_user is None:
        return


    await delete_user_message(message)

    await show_main_screen(message)
