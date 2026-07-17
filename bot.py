import asyncio

from aiogram import Bot, Dispatcher

from config import config
from database.db import create_database

from handlers.advice import router as advice_router
from handlers.clear import router as clear_router
from handlers.history import router as history_router
from handlers.savings import router as savings_router
from handlers.settings import router as settings_router
from handlers.start import router as start_router
from handlers.statistics import router as statistics_router
from handlers.transactions import router as transactions_router
from handlers.undo import router as undo_router


async def main() -> None:
    await create_database()

    bot = Bot(token=config.bot_token)
    dispatcher = Dispatcher()

    # Порядок важен:
    # общий обработчик transactions_router должен быть последним.
    dispatcher.include_router(clear_router)
    dispatcher.include_router(start_router)
    dispatcher.include_router(settings_router)
    dispatcher.include_router(statistics_router)
    dispatcher.include_router(savings_router)
    dispatcher.include_router(history_router)
    dispatcher.include_router(undo_router)
    dispatcher.include_router(advice_router)
    dispatcher.include_router(transactions_router)

    print("✅ MonttiMoney запущен!")
    print("✅ База данных подключена!")
    print("✅ Настройки подключены!")
    print("✅ Статистика подключена!")
    print("✅ История подключена!")
    print("✅ Совет дня подключён!")

    try:
        await dispatcher.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
    