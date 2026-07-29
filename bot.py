import asyncio
import logging

from aiogram import Bot, Dispatcher

from config import config
from database.db import create_database

from handlers.advice import router as advice_router
from handlers.cancel import router as cancel_router
from handlers.clear import router as clear_router
from handlers.history import router as history_router
from handlers.savings import router as savings_router
from handlers.settings import router as settings_router
from handlers.start import router as start_router
from handlers.statistics import router as statistics_router
from handlers.transactions import router as transactions_router
from handlers.undo import router as undo_router


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    await create_database()

    bot = Bot(token=config.bot_token)
    dispatcher = Dispatcher()

    dispatcher.include_router(cancel_router)
    dispatcher.include_router(clear_router)
    dispatcher.include_router(start_router)
    dispatcher.include_router(settings_router)
    dispatcher.include_router(statistics_router)
    dispatcher.include_router(savings_router)
    dispatcher.include_router(history_router)
    dispatcher.include_router(undo_router)
    dispatcher.include_router(advice_router)
    dispatcher.include_router(transactions_router)

    await bot.delete_webhook(drop_pending_updates=True)

    bot_info = await bot.get_me()

    logging.info(
        "MonttiMoney запущен: @%s, bot_id=%s",
        bot_info.username,
        bot_info.id,
    )

    try:
        await dispatcher.start_polling(
            bot,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
    