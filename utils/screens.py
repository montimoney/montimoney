from aiogram.types import Message

from database.repository import (
    get_main_message_id,
    save_main_message_id,
)

from database.session import session_factory


async def show_screen(
    message: Message,
    text: str,
    reply_markup=None,
    parse_mode="HTML",
):

    if message.from_user is None:
        return


    user_id = message.from_user.id


    async with session_factory() as session:

        old_message_id = await get_main_message_id(
            session=session,
            user_id=user_id,
        )


    if old_message_id:

        try:
            await message.bot.delete_message(
                chat_id=user_id,
                message_id=old_message_id,
            )

        except Exception:
            pass


    new_message = await message.answer(
        text,
        reply_markup=reply_markup,
        parse_mode=parse_mode,
    )


    async with session_factory() as session:

        await save_main_message_id(
            session=session,
            user_id=user_id,
            message_id=new_message.message_id,
        )
        