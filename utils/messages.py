from aiogram.types import Message


async def delete_user_message(
    message: Message,
) -> None:
    """
    Удаляет сообщение пользователя.
    """

    try:
        await message.delete()

    except Exception:
        pass



async def send_temp_message(
    message: Message,
    text: str,
    seconds: int = 3,
) -> None:
    """
    Временное сообщение.
    """

    temp_message = await message.answer(
        text
    )

    import asyncio

    await asyncio.sleep(seconds)

    try:
        await temp_message.delete()

    except Exception:
        pass
    