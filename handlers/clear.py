from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

from database.session import session_factory
from database.repository import clear_test_data

from handlers.start import build_main_screen
from keyboards.main import main_keyboard

from utils.messages import (
    send_temp_message,
    delete_user_message,
)


router = Router()


@router.message(Command("clear"))
@router.message(F.text == "🧹 Очистить тестовые данные")
async def clear_handler(message: Message):

    if message.from_user is None:
        return

    await delete_user_message(message)

    async with session_factory() as session:
        await clear_test_data(
            session=session,
            user_id=message.from_user.id,
        )

    await send_temp_message(
        message,
        "🧹 Тестовые данные очищены 🐱",
    )

    await message.answer(
        await build_main_screen(
            message.from_user.id
        ),
        reply_markup=main_keyboard,
        parse_mode="HTML",
    )
    