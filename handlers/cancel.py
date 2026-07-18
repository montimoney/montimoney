from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from handlers.start import show_main_screen
from utils.messages import delete_user_message

router = Router()

CANCEL_WORDS = {
    "отмена",
    "отмена ❌",
    "стоп",
    "назад",
}


@router.message(F.text.func(lambda text: text and text.lower() in CANCEL_WORDS))
async def cancel_handler(
    message: Message,
    state: FSMContext,
):
    data = await state.get_data()

    old_message = data.get("category_message_id")

    if old_message:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=old_message,
            )
        except Exception:
            pass

    await state.clear()

    await delete_user_message(message)

    await show_main_screen(message)