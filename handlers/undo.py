from aiogram import Router, F
from aiogram.types import Message

from database.session import session_factory
from database.repository import (
    get_last_transaction,
    delete_transaction,
)

from keyboards.undo import undo_keyboard

from handlers.start import show_main_screen

from utils.messages import delete_user_message
from utils.screens import show_screen


router = Router()



@router.message(F.text == "↩️ Отменить запись")
async def undo_start(
    message: Message,
):

    if message.from_user is None:
        return


    await delete_user_message(message)


    async with session_factory() as session:

        transaction = await get_last_transaction(
            session=session,
            user_id=message.from_user.id,
        )


    if transaction is None:

        await show_screen(
            message,
            "🐱 Пока нечего отменять.",
        )

        return


    icon = (
        "💰"
        if transaction.operation_type == "income"
        else "💸"
    )


    text = (
        "↩️ <b>Последняя запись</b>\n\n"
        f"{icon} {transaction.description}\n"
        f"{transaction.amount} ₽\n\n"
        "Удалить её?"
    )


    await show_screen(
        message,
        text,
        reply_markup=undo_keyboard,
    )



@router.message(F.text == "✅ Да, удалить")
async def undo_confirm(
    message: Message,
):

    if message.from_user is None:
        return


    async with session_factory() as session:

        transaction = await get_last_transaction(
            session=session,
            user_id=message.from_user.id,
        )


        if transaction:

            await delete_transaction(
                session=session,
                transaction=transaction,
            )


    await delete_user_message(message)


    await show_main_screen(message)



@router.message(F.text == "❌ Оставить")
async def undo_cancel(
    message: Message,
):

    await delete_user_message(message)

    await show_main_screen(message)