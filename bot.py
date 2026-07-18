import asyncio
import logging

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.types import TelegramObject

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


class UpdateLoggerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler,
        event: TelegramObject,
        data: dict,
    ):
        print("\n📩 ПОЛУЧЕНО ОБНОВЛЕНИЕ:")
        print(event)

        try:
            return await handler(event, data)
        except Exception:
            logging.exception("❌ Ошибка при обработке обновления")
            raise


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    await create_database()

    bot = Bot(token=config.bot_token)
    dispatcher = Dispatcher()

    bot_info = await bot.get_me()

    print(f"🤖 Запущен бот: @{bot_info.username}")
    print(f"🆔 ID бота: {bot_info.id}")

    webhook_info = await bot.get_webhook_info()

    print(f"🌐 Webhook: {webhook_info.url or 'не установлен'}")
    print(f"📨 Ожидающих обновлений: {webhook_info.pending_update_count}")

    await bot.delete_webhook(drop_pending_updates=True)

    dispatcher.update.outer_middleware(UpdateLoggerMiddleware())

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

    print("✅ MonttiMoney запущен!")
    print("📡 Ожидаю сообщения из Telegram...")

    try:
        await dispatcher.start_polling(
            bot,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
    